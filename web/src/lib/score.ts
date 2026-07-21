/** A faithful browser port of the Python scoring pipeline.
 *
 *  Every constant here is either copied from src/engine.py and
 *  src/published_models.py or read from the model coefficients the pipeline
 *  exports into report.risk_models. Nothing is re-estimated in the browser, so
 *  a case scored here and the same case scored by `python src/run_pipeline.py`
 *  return the same numbers — which is what lets the workbench score a new
 *  application with no server behind it.
 *
 *  Ports: rule_score · framingham_cvd10 · external prior · logistic regression
 *  · estimate_premium · affordability_assess · decide. */

import { activeReport } from '../data/store'
import type { Affordability, AffordIndicator, Case, Conflict, Tier, Verdict } from '../data/types'

/* ------------------------------------------------------------------ input -- */

export interface Application {
  name: string
  sex: 'M' | 'F'
  age: number
  income: number
  monthlyExpenses: number
  debt: number
  credit: number
  coverage: number
  existingCoverage: number
  policy: string
  bmi: number
  systolic: number
  /** total cholesterol — feeds the public-dataset prior, not the rule engine */
  cholesterol: number
  smoker: 'Non-smoker' | 'Former smoker' | 'Smoker'
  conditions: string
  familyHistory: boolean
  hazard: string
  violations: number
  alcohol: 'None' | 'Moderate' | 'Heavy'
  priorDecline: boolean
  dangerousDriving: boolean
  drugUse: boolean
  criminalRecord: boolean
  bankruptcy: boolean
  foreignTravel: boolean
  weightChange: boolean
  unique: string
}

/* ------------------------------------------------------------- rule engine -- */

export type RuleFactorOut = { label: string; value: string; points: number }

/** Port of engine.rule_score — the explainable, weighted layer. */
export function ruleScore(a: Application): { score: number; factors: RuleFactorOut[] } {
  const factors: RuleFactorOut[] = []
  const add = (label: string, value: string, points: number) =>
    factors.push({ label, value, points })

  const conds =
    a.conditions.trim() === '' || a.conditions === 'None'
      ? []
      : a.conditions.split(',').map((c) => c.trim())
  const dti = a.income > 0 ? a.debt / a.income : 0

  add('Applicant age', `${a.age} years`, a.age < 30 ? 0 : a.age <= 45 ? 5 : a.age <= 55 ? 10 : 18)
  add('Tobacco use', a.smoker, a.smoker === 'Smoker' ? 25 : a.smoker === 'Former smoker' ? 8 : 0)
  add(
    'Body mass index',
    `${a.bmi.toFixed(1)} BMI`,
    a.bmi < 18.5 || a.bmi >= 35 ? 15 : a.bmi >= 30 ? 8 : a.bmi >= 25 ? 3 : 0,
  )
  add(
    'Medical conditions',
    conds.join(', ') || 'None',
    conds.reduce((s, c) => s + (c.toLowerCase().includes('diabetes') ? 15 : 8), 0),
  )
  add('Family medical history', a.familyHistory ? 'Notable' : 'None disclosed', a.familyHistory ? 6 : 0)
  add(
    'Debt-to-income ratio',
    `${(dti * 100).toFixed(1)}%`,
    dti < 0.2 ? 0 : dti < 0.35 ? 5 : dti < 0.5 ? 12 : 20,
  )
  add(
    'Credit score',
    String(a.credit),
    a.credit > 750 ? 0 : a.credit >= 700 ? 3 : a.credit >= 650 ? 8 : 15,
  )
  const hazardous = a.hazard !== 'None' && a.hazard.trim() !== ''
  add('Hazardous activities', hazardous ? a.hazard : 'None disclosed', hazardous ? 10 : 0)
  add(
    'Driving record',
    `${a.violations} violation(s) in 3 years`,
    a.violations === 0 ? 0 : a.violations <= 2 ? 4 : 10,
  )
  add('Alcohol use', a.alcohol, a.alcohol === 'Heavy' ? 12 : a.alcohol === 'Moderate' ? 2 : 0)

  // Section 6 personal declarations, per the Manulife OTIP application form
  const declarations: [boolean, string, number][] = [
    [a.priorDecline, 'Prior insurance declined/modified/rated (Q6-1)', 8],
    [a.dangerousDriving, 'Careless/dangerous driving or licence suspension (Q6-2a)', 12],
    [a.drugUse, 'Drug use or alcohol/drug counselling (Q6-5a)', 15],
    [a.criminalRecord, 'Criminal offence charged or convicted (Q6-5b)', 8],
    [a.bankruptcy, 'Personal/business bankruptcy (Q6-5c)', 10],
    [a.foreignTravel, 'Foreign travel planned, next 12 months (Q6-4a)', 3],
    [a.weightChange, 'Weight change >10 lb in past 12 months (Q7)', 4],
  ]
  for (const [flag, label, pts] of declarations) {
    add(label, flag ? 'Yes' : 'No', flag ? pts : 0)
  }

  const score = Math.min(
    factors.reduce((s, f) => s + f.points, 0),
    100,
  )
  return { score, factors }
}

export function tier(score: number): Tier {
  return score <= 25 ? 'low' : score <= 50 ? 'moderate' : score <= 70 ? 'elevated' : 'high'
}

/* ------------------------------------------------ published Framingham prior -- */

/** D'Agostino et al., Circulation 2008 — office-based (BMI) general-CVD model.
 *  Copied verbatim from src/published_models.py. */
const FRAMINGHAM = {
  F: { lnAge: 2.72107, lnBmi: 0.51125, lnSbp: 2.81291, smoker: 0.61868, diabetes: 0.77763, s0: 0.94833, mean: 26.0145 },
  M: { lnAge: 3.11296, lnBmi: 0.79277, lnSbp: 1.85508, smoker: 0.70953, diabetes: 0.5316, s0: 0.88431, mean: 23.9802 },
}

const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v))

export function framinghamCvd10(
  age: number,
  sex: 'M' | 'F',
  bmi: number,
  sbp: number,
  smokerNow: boolean,
  diabetes: boolean,
): number {
  const p = FRAMINGHAM[sex]
  // the model is only validated over these ranges
  const s =
    p.lnAge * Math.log(clamp(age, 30, 74)) +
    p.lnBmi * Math.log(clamp(bmi, 15, 50)) +
    p.lnSbp * Math.log(clamp(sbp, 90, 200)) +
    p.smoker * (smokerNow ? 1 : 0) +
    p.diabetes * (diabetes ? 1 : 0)
  return 1 - Math.pow(p.s0, Math.exp(s - p.mean))
}

/* ------------------------------------------------- external AUC-weighted prior -- */

interface PriorModel {
  name: string
  features: string[]
  coef: number[]
  intercept: number
  mean: number[]
  std: number[]
  auc: number
  weight: number
}

/** Read through a getter, not captured at import: in live mode the dataset is
 *  replaced after this module has already been evaluated. */
const priorModels = () =>
  (activeReport().risk_models.prior_export ?? []) as unknown as PriorModel[]

const sigmoid = (z: number) => 1 / (1 + Math.exp(-z))

/** Port of external_data.prior_scores — each public dataset's model votes,
 *  weighted by (its AUC − 0.5); models at or near chance are already excluded
 *  upstream and carry no weight here. */
export function externalPrior(f: Record<string, number>): number {
  let total = 0
  let wsum = 0
  for (const m of priorModels()) {
    if (m.weight <= 0) continue
    let z = m.intercept
    for (let i = 0; i < m.features.length; i++) {
      const raw = f[m.features[i]] ?? m.mean[i]
      const std = m.std[i] || 1
      z += m.coef[i] * ((raw - m.mean[i]) / std)
    }
    total += sigmoid(z) * m.weight
    wsum += m.weight
  }
  return wsum > 0 ? total / wsum : 0.5
}

/* --------------------------------------------------------- logistic model -- */

/** Port of engine.ml_scores for the exported logistic regression. Returns 0–100. */
export function mlScore(features: Record<string, number>): number {
  const lr = activeReport().risk_models.lr_export
  let z = lr.intercept
  for (let i = 0; i < lr.features.length; i++) {
    const raw = features[lr.features[i]] ?? 0
    const std = lr.scaler_std[i] || 1
    z += lr.coef[i] * ((raw - lr.scaler_mean[i]) / std)
  }
  return Math.round(sigmoid(z) * 1000) / 10
}

/** Build the 20-feature vector engine.featurize produces. */
export function featurize(a: Application): Record<string, number> {
  const conds =
    a.conditions.trim() === '' || a.conditions === 'None'
      ? []
      : a.conditions.split(',').map((c) => c.trim())
  const diabetes = conds.some((c) => c.toLowerCase().includes('diabetes'))
  const smokerNow = a.smoker === 'Smoker'
  const dti = a.income > 0 ? clamp(a.debt / a.income, 0, 3) : 0

  const extPrior = externalPrior({
    age: a.age,
    bmi: a.bmi,
    smoker: smokerNow ? 1 : 0,
    diabetes: diabetes ? 1 : 0,
    sys_bp: a.systolic,
    chol: a.cholesterol,
    sex: a.sex === 'M' ? 1 : 0,
  })

  return {
    Age: a.age,
    BMI: a.bmi,
    smoker_now: smokerNow ? 1 : 0,
    smoker_former: a.smoker === 'Former smoker' ? 1 : 0,
    n_conditions: conds.length,
    'Family History Flag': a.familyHistory ? 1 : 0,
    'Debt-to-Income Ratio': dti,
    'Credit Score': a.credit,
    hazardous_activity: a.hazard !== 'None' && a.hazard.trim() !== '' ? 1 : 0,
    driving_violations: a.violations,
    alcohol_heavy: a.alcohol === 'Heavy' ? 1 : 0,
    prior_decline: a.priorDecline ? 1 : 0,
    dangerous_driving: a.dangerousDriving ? 1 : 0,
    drug_use: a.drugUse ? 1 : 0,
    criminal_record: a.criminalRecord ? 1 : 0,
    bankruptcy: a.bankruptcy ? 1 : 0,
    foreign_travel: a.foreignTravel ? 1 : 0,
    weight_change: a.weightChange ? 1 : 0,
    external_prior: extPrior,
    published_cvd_prior: framinghamCvd10(a.age, a.sex, a.bmi, a.systolic, smokerNow, diabetes),
  }
}

/* ------------------------------------------------------------- affordability -- */

const POLICY_PREMIUM_MULT: Record<string, number> = {
  'Term Life - 20yr': 1.0,
  'Term Life - 30yr': 1.45,
  'Universal Life': 5.0,
  'Whole Life': 8.5,
}

export const POLICY_TYPES = Object.keys(POLICY_PREMIUM_MULT)

/** Port of engine.estimate_premium — indicative annual premium in USD. */
export function estimatePremium(
  age: number,
  smoker: string,
  coverage: number,
  policy: string,
): number {
  let rate = 0.9 * Math.exp(0.045 * (age - 30))
  if (smoker === 'Smoker') rate *= 2.3
  else if (smoker === 'Former smoker') rate *= 1.25
  return Math.round((coverage / 1000) * rate * (POLICY_PREMIUM_MULT[policy] ?? 1) * 100) / 100
}

const COVERAGE_CAPS: [number, number][] = [
  [40, 25],
  [50, 20],
  [60, 15],
  [999, 10],
]
const NET_INCOME_FACTOR = 0.78
const DEBT_SERVICE_RATE = 0.025

const usd = (n: number) => '$' + Math.round(n).toLocaleString('en-US')

/** Port of engine.affordability_assess — the brief's core financial screen. */
export function affordabilityAssess(
  income: number,
  monthlyExpenses: number,
  debt: number,
  coverage: number,
  existingCov: number,
  age: number,
  premium: number,
): Affordability {
  const inc = Math.max(income, 1)
  const netMonthly = (inc * NET_INCOME_FACTOR) / 12
  const premMonthly = premium / 12
  const pti = premium / inc
  const disposable = netMonthly - monthlyExpenses - premMonthly
  const debtPay = debt * DEBT_SERVICE_RATE
  const dsr = debtPay / netMonthly
  const cap = COVERAGE_CAPS.find(([a]) => age < a)![1]
  const covMult = (coverage + existingCov) / inc

  const indicators: AffordIndicator[] = []
  const reasons: string[] = []
  const add = (label: string, value: string, status: AffordIndicator['status'], detail: string) => {
    indicators.push({ label, value, status, detail })
    if (status === 'fail') reasons.push(`${label}: ${detail}`)
  }

  add(
    'Premium-to-income',
    `${(pti * 100).toFixed(1)}%`,
    pti <= 0.05 ? 'pass' : pti <= 0.1 ? 'strain' : 'fail',
    `annual premium ${usd(premium)} is ${(pti * 100).toFixed(1)}% of gross income (benchmark ≤5%, strained to 10%)`,
  )

  const floor = Math.max(0.05 * netMonthly, 150)
  add(
    'Disposable income after premium',
    `${usd(disposable)}/mo`,
    disposable < 0 ? 'fail' : disposable < floor ? 'strain' : 'pass',
    `net ${usd(netMonthly)}/mo − expenses ${usd(monthlyExpenses)}/mo − premium ${usd(premMonthly)}/mo leaves ${usd(disposable)}/mo (floor ${usd(floor)})`,
  )

  add(
    'Coverage-to-income multiple',
    `${covMult.toFixed(1)}×`,
    covMult <= cap ? 'pass' : covMult <= cap * 1.1 ? 'strain' : 'fail',
    `total coverage sought is ${covMult.toFixed(1)}× income against an age-${age} cap of ${cap}×`,
  )

  add(
    'Debt-service ratio',
    `${(dsr * 100).toFixed(0)}%`,
    dsr <= 0.2 ? 'pass' : dsr <= 0.35 ? 'strain' : 'fail',
    `estimated debt payments ${usd(debtPay)}/mo consume ${(dsr * 100).toFixed(0)}% of net income (benchmark ≤20%)`,
  )

  const statuses = indicators.map((i) => i.status)
  const verdict = statuses.includes('fail') ? 'fail' : statuses.includes('strain') ? 'strain' : 'pass'
  const label = ({ pass: 'AFFORDABLE', strain: 'STRAINED', fail: 'NOT JUSTIFIED' } as const)[verdict]
  if (verdict === 'strain') {
    reasons.push(
      'Affordability indicators are within tolerance but strained: ' +
        indicators.filter((i) => i.status === 'strain').map((i) => i.label).join('; '),
    )
  }

  return {
    verdict,
    label,
    premium: Math.round(premium * 100) / 100,
    premium_monthly: Math.round(premMonthly * 100) / 100,
    pti: Math.round(pti * 1e4) / 1e4,
    disposable: Math.round(disposable * 100) / 100,
    cov_mult: Math.round(covMult * 100) / 100,
    cov_cap: cap,
    dsr: Math.round(dsr * 1e4) / 1e4,
    indicators,
    reasons,
  }
}

/* ------------------------------------------------------------------ decide -- */

const MISREP_TYPES = new Set(['smoker_nondisclosure', 'dob_mismatch'])

export interface Decision {
  decision: 'APPROVE' | 'MANUAL REVIEW' | 'DECLINE'
  rate_class: string
  verdict: Verdict
  risk_score: number
  tier: Tier
  reasons: string[]
  referred: boolean
}

/** Port of engine.decide. The approve/decline lines come from the pipeline's
 *  holdout-tuned thresholds, not from the defaults in engine.py. */
export function decide(
  ruleS: number,
  mlS: number,
  conflicts: Conflict[],
  unique: string | null,
  afford: Affordability | null,
  aLineArg?: number,
  dLineArg?: number,
): Decision {
  const thresholds = activeReport().decisioning.thresholds
  const aLine = aLineArg ?? thresholds.a_line
  const dLine = dLineArg ?? thresholds.d_line
  const composite = Math.round(0.5 * ruleS + 0.5 * mlS)
  const majors = conflicts.filter((c) => c.severity === 'major')
  const misrep = majors.filter((c) => MISREP_TYPES.has(c.type))
  const affordFail = afford?.verdict === 'fail'
  const reasons: string[] = []

  let verdict: Verdict
  let decision: Decision['decision']
  let rate: string

  if (misrep.length) {
    verdict = 'red'
    decision = 'DECLINE'
    rate = 'Declined — Material Misrepresentation'
    reasons.push(
      'Application contradicts medical/identity evidence: ' +
        misrep.map((c) => c.type.replace(/_/g, ' ')).join('; '),
    )
  } else if (composite >= dLine) {
    verdict = 'red'
    decision = 'DECLINE'
    rate = 'Declined — Risk Exceeds Appetite'
    reasons.push(`Composite risk score ${composite}/100 is in the ${dLine}+ decline band`)
  } else if (
    majors.length ||
    unique ||
    affordFail ||
    composite >= aLine ||
    Math.abs(ruleS - mlS) > 20
  ) {
    verdict = 'yellow'
    decision = 'MANUAL REVIEW'
    rate = 'Referred — Senior Underwriter Review'
    if (majors.length) {
      reasons.push(
        `${majors.length} major data conflict(s): ` + majors.map((c) => c.type).join('; '),
      )
    }
    if (unique) {
      rate = 'Referred — Unique Circumstances Disclosed'
      reasons.push(`Applicant disclosed unique circumstances: ${unique}`)
    }
    if (affordFail && afford) {
      rate = 'Referred — Financial Underwriting Review'
      reasons.push(...afford.reasons)
    }
    if (composite >= aLine) {
      reasons.push(`Composite score ${composite} sits in the ${aLine}–${dLine - 1} referral band`)
    }
    if (Math.abs(ruleS - mlS) > 20) {
      reasons.push(
        `Rule engine (${ruleS}) and ML model (${mlS.toFixed(0)}) disagree materially`,
      )
    }
  } else {
    verdict = 'green'
    decision = 'APPROVE'
    rate = composite <= 25 ? 'Preferred Rate Class' : 'Standard Rate Class'
    reasons.push(
      `Composite score ${composite} is below the ${aLine}-point approval line; engines agree and no conflicts or special circumstances were found`,
    )
    if (afford?.verdict === 'strain') {
      reasons.push(
        'Affordability is strained but within tolerance — flagged on the financial viability panel',
      )
    }
  }

  return {
    decision,
    rate_class: rate,
    verdict,
    risk_score: composite,
    tier: tier(composite),
    reasons,
    referred: verdict === 'yellow',
  }
}

/* ---------------------------------------------------------------- one call -- */

export interface ScoreResult extends Decision {
  ruleScore: number
  ruleFactors: RuleFactorOut[]
  mlScore: number
  afford: Affordability
  premium: number
  externalPrior: number
  publishedPrior: number
}

/** Score a complete application end to end, exactly as the pipeline would. */
export function scoreApplication(a: Application): ScoreResult {
  const { score: rule, factors } = ruleScore(a)
  const features = featurize(a)
  const ml = mlScore(features)
  const premium = estimatePremium(a.age, a.smoker, a.coverage, a.policy)
  const afford = affordabilityAssess(
    a.income,
    a.monthlyExpenses,
    a.debt,
    a.coverage,
    a.existingCoverage,
    a.age,
    premium,
  )
  const d = decide(rule, ml, [], a.unique.trim() || null, afford)
  return {
    ...d,
    ruleScore: rule,
    ruleFactors: factors,
    mlScore: ml,
    afford,
    premium,
    externalPrior: features.external_prior,
    publishedPrior: features.published_cvd_prior,
  }
}

/** A neutral net-new applicant. New application starts here rather than seeded
 *  from whatever case happened to be open — exploring a change to an existing
 *  applicant is the case file's what-if, a different task. */
export const BLANK_APPLICATION: Application = {
  name: '',
  sex: 'M',
  age: 40,
  income: 75000,
  monthlyExpenses: 2800,
  debt: 20000,
  credit: 720,
  coverage: 500000,
  existingCoverage: 0,
  policy: 'Term Life - 20yr',
  bmi: 25,
  systolic: 120,
  cholesterol: 190,
  smoker: 'Non-smoker',
  conditions: 'None',
  familyHistory: false,
  hazard: 'None',
  violations: 0,
  alcohol: 'None',
  priorDecline: false,
  dangerousDriving: false,
  drugUse: false,
  criminalRecord: false,
  bankruptcy: false,
  foreignTravel: false,
  weightChange: false,
  unique: '',
}

/** Turn a portfolio case back into an Application so it can seed the what-if. */
export function caseToApplication(c: Case): Application {
  return {
    name: c.name,
    sex: c.sex,
    age: c.age,
    income: c.income,
    monthlyExpenses: c.expenses,
    debt: c.debt,
    credit: c.credit,
    coverage: c.coverage,
    existingCoverage: c.existing_cov,
    policy: c.policy,
    bmi: c.bmi,
    systolic: Number(String(c.bp).split('/')[0]) || 120,
    cholesterol: c.chol,
    smoker: c.smoker as Application['smoker'],
    conditions: c.conditions,
    familyHistory: Boolean(c.family),
    hazard: c.hazard,
    violations: c.violations,
    alcohol: c.alcohol as Application['alcohol'],
    priorDecline: Boolean(c.decl.prior_decline),
    dangerousDriving: Boolean(c.decl.dangerous_driving),
    drugUse: Boolean(c.decl.drug_use),
    criminalRecord: Boolean(c.decl.criminal),
    bankruptcy: Boolean(c.decl.bankruptcy),
    foreignTravel: Boolean(c.decl.foreign_travel),
    weightChange: Boolean(c.decl.weight_change),
    unique: c.unique ?? '',
  }
}
