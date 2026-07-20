/** Prove the browser port and the Python pipeline agree.
 *
 *  src/lib/score.ts re-implements engine.py so the workbench can score an
 *  application with no server. That is only defensible if the two produce the
 *  same numbers, so this replays all 200 portfolio cases through the TypeScript
 *  engine and compares against what the pipeline recorded.
 *
 *  Run: node web/scripts/verify-port.mjs   (also runs in CI)
 */
import { build } from 'esbuild'
import { pathToFileURL } from 'node:url'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { mkdtempSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

const here = dirname(fileURLToPath(import.meta.url))
const webRoot = resolve(here, '..')
const outDir = mkdtempSync(join(tmpdir(), 'uwc-verify-'))
const outfile = join(outDir, 'bundle.mjs')

await build({
  stdin: {
    contents: `
      export * from './src/lib/score.ts'
      export { cases } from './src/data/index.ts'
    `,
    resolveDir: webRoot,
    loader: 'ts',
  },
  bundle: true,
  format: 'esm',
  platform: 'node',
  outfile,
  logLevel: 'warning',
})

const m = await import(pathToFileURL(outfile).href)
rmSync(outDir, { recursive: true, force: true })

const fails = []
let maxLr = 0
let maxExt = 0
let maxPub = 0
let maxPrem = 0

for (const c of m.cases) {
  const app = m.caseToApplication(c)

  const rule = m.ruleScore(app).score
  if (rule !== c.rule_score) {
    fails.push(`${c.id} rule engine: got ${rule}, pipeline ${c.rule_score}`)
  }

  const f = m.featurize(app)
  maxExt = Math.max(maxExt, Math.abs(f.external_prior - c.ext_prior))
  maxPub = Math.max(maxPub, Math.abs(f.published_cvd_prior - c.pub_prior))

  // engine.py exports the logistic coefficients and scaler statistics rounded
  // to 6 decimal places. Across 20 standardised features that quantisation
  // moves the logit by ~1e-5, which is enough to land a handful of cases on the
  // far side of a 0.05 rounding boundary once the score is stored to one
  // decimal place. One full step is therefore the exact-agreement floor.
  const lr = m.mlScore(f)
  maxLr = Math.max(maxLr, Math.abs(lr - c.ml_score_lr))

  const premium = m.estimatePremium(app.age, app.smoker, app.coverage, app.policy)
  maxPrem = Math.max(maxPrem, Math.abs(premium - c.premium))

  const afford = m.affordabilityAssess(
    app.income, app.monthlyExpenses, app.debt,
    app.coverage, app.existingCoverage, app.age, premium,
  )
  if (afford.verdict !== c.afford.verdict) {
    fails.push(`${c.id} affordability: got ${afford.verdict}, pipeline ${c.afford.verdict}`)
  }
  afford.indicators.forEach((ind, i) => {
    const want = c.afford.indicators[i]
    if (ind.status !== want.status) {
      fails.push(`${c.id} "${ind.label}": got ${ind.status}, pipeline ${want.status}`)
    }
  })
}

const TOL = { lr: 0.101, prior: 0.001, premium: 0.011 }
if (maxLr > TOL.lr) fails.push(`logistic score drifts up to ${maxLr.toFixed(3)} points`)
if (maxExt > TOL.prior) fails.push(`external prior drifts up to ${maxExt.toFixed(5)}`)
if (maxPub > TOL.prior) fails.push(`published CVD prior drifts up to ${maxPub.toFixed(5)}`)
if (maxPrem > TOL.premium) fails.push(`premium drifts up to ${maxPrem.toFixed(3)}`)

console.log(`checked ${m.cases.length} cases`)
console.log(`  rule engine + affordability verdicts  exact`)
console.log(`  logistic score        max drift ${maxLr.toFixed(3)} pts (stored to 0.1)`)
console.log(`  external prior        max drift ${maxExt.toFixed(5)}`)
console.log(`  published CVD prior   max drift ${maxPub.toFixed(5)}`)
console.log(`  indicative premium    max drift ${maxPrem.toFixed(3)}`)

if (fails.length) {
  console.error(`\n${fails.length} mismatch(es) between the browser port and the pipeline:`)
  for (const f of fails.slice(0, 20)) console.error(`  ${f}`)
  process.exit(1)
}
console.log('\nbrowser port agrees with the pipeline')
