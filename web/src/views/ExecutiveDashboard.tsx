import { useMemo } from 'react'
import { motion } from 'motion/react'
import { useData } from '../data/DataContext'
import { useAuth } from '../auth/AuthContext'
import { usd, usdShort, pct } from '../lib/format'
import '../styles/exec.css'

/** The executive's screen. Not a queue — the book as money.
 *
 *  An underwriter reads one case; a chief underwriting officer reads the whole
 *  book's financial shape: how much cover the portfolio is taking onto its own
 *  balance sheet, the approve/decline mix that produced it, the premium it earns,
 *  and the risk-appetite lines that are theirs to set. */
export default function ExecutiveDashboard() {
  const { cases, report } = useData()
  const { persona } = useAuth()
  const t = report.decisioning.thresholds

  const m = useMemo(() => {
    const g = { n: 0, cover: 0, premium: 0 }
    const y = { n: 0, cover: 0, premium: 0 }
    const r = { n: 0, cover: 0, premium: 0 }
    for (const c of cases) {
      const bucket = c.verdict === 'green' ? g : c.verdict === 'yellow' ? y : r
      bucket.n += 1
      bucket.cover += c.coverage
      bucket.premium += c.premium
    }
    const n = cases.length || 1
    const requested = g.cover + y.cover + r.cover
    return {
      g,
      y,
      r,
      n: cases.length,
      requested,
      approveRate: g.n / n,
      referRate: y.n / n,
      declineRate: r.n / n,
      avgApprovedCover: g.n ? g.cover / g.n : 0,
    }
  }, [cases])

  return (
    <>
      <div className="exectop">
        <div className="exectop__say">
          <p className="eyebrow">Executive · book of {report.n_applicants.toLocaleString('en-US')}</p>
          <h1 className="viewhead__title">
            The book,
            <br />
            as money
          </h1>
          <p className="viewhead__lede">
            {persona?.name} — {persona?.title.toLowerCase()}. This is the portfolio the underwriting
            desks produced: what the book takes on, what it turns away, and the appetite lines that
            are yours to set.
          </p>
        </div>

        <div className="exposure">
          <span className="eyebrow">Exposure taken on (approved cover)</span>
          <motion.div
            className="exposure__figure figure"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            {usd(m.g.cover)}
          </motion.div>
          <p className="exposure__sub">
            across {m.g.n} approved {m.g.n === 1 ? 'policy' : 'policies'} · earning{' '}
            <b>{usd(m.g.premium)}</b> in annual premium
          </p>
        </div>
      </div>

      <div className="viewbody">
        {/* ---- the approve / refer / decline split ---- */}
        <div className="srule">
          <span className="eyebrow">The decision mix</span>
        </div>

        <div className="mixbar" role="img"
          aria-label={`Approve ${pct(m.approveRate)}, refer ${pct(m.referRate)}, decline ${pct(m.declineRate)}`}>
          <motion.span className="mixbar__seg v-pass" initial={{ width: 0 }}
            animate={{ width: `${m.approveRate * 100}%` }} transition={{ duration: 0.6 }} />
          <motion.span className="mixbar__seg v-watch" initial={{ width: 0 }}
            animate={{ width: `${m.referRate * 100}%` }} transition={{ duration: 0.6, delay: 0.05 }} />
          <motion.span className="mixbar__seg v-fail" initial={{ width: 0 }}
            animate={{ width: `${m.declineRate * 100}%` }} transition={{ duration: 0.6, delay: 0.1 }} />
        </div>

        <div className="stats">
          <Stat tone="pass" label="Approved" pct={pct(m.approveRate)} n={m.g.n}
            money={usdShort(m.g.cover)} sub="cover on the books" />
          <Stat tone="watch" label="Referred" pct={pct(m.referRate)} n={m.y.n}
            money={usdShort(m.y.cover)} sub="cover pending a human" />
          <Stat tone="fail" label="Declined" pct={pct(m.declineRate)} n={m.r.n}
            money={usdShort(m.r.cover)} sub="cover turned away" />
        </div>

        {/* ---- headline financials ---- */}
        <div className="srule">
          <span className="eyebrow">Portfolio financials</span>
        </div>

        <div className="stats stats--fin">
          <FinTile label="Requested cover" value={usd(m.requested)} sub={`${m.n} applications read`} />
          <FinTile label="Approved premium / yr" value={usd(m.g.premium)} sub="the book's annual income" />
          <FinTile label="Avg approved cover" value={usd(Math.round(m.avgApprovedCover))} sub="per approved policy" />
          <FinTile label="Straight-through rate" value={pct(t.stp_est, 1)} sub="auto-decided, no human" />
        </div>

        {/* ---- the appetite the executive owns ---- */}
        <div className="srule">
          <span className="eyebrow">Risk appetite — the levers you own</span>
        </div>

        <div className="panel appetite">
          <div className="panel__body">
            <div className="appetite__lines">
              <div className="appetite__line">
                <span className="appetite__num figure v-pass">{t.a_line}</span>
                <span className="appetite__cap">Approve line</span>
                <p>Risk under {t.a_line}/100 clears automatically when the cover is affordable.</p>
              </div>
              <div className="appetite__line">
                <span className="appetite__num figure v-fail">{t.d_line}</span>
                <span className="appetite__cap">Decline line</span>
                <p>Risk at {t.d_line}/100 and above is declined; the band between is referred.</p>
              </div>
            </div>
            <p className="appetite__note">
              These lines set how much risk the book takes on. They were tuned on a held-out half of
              the portfolio ({t.evaluation}). In a live deployment they are the executive's to move —
              raising the decline line grows the book and its exposure; lowering it protects the loss
              ratio.
            </p>
          </div>
        </div>
      </div>
    </>
  )
}

function Stat({
  tone, label, pct: p, n, money, sub,
}: { tone: 'pass' | 'watch' | 'fail'; label: string; pct: string; n: number; money: string; sub: string }) {
  return (
    <div className={`stat stat--${tone}`}>
      <span className="stat__label">{label}</span>
      <span className={`stat__pct figure v-${tone}`}>{p}</span>
      <span className="stat__n figure">{n} cases</span>
      <span className="stat__money figure">{money}</span>
      <span className="stat__sub">{sub}</span>
    </div>
  )
}

function FinTile({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <div className="fintile">
      <span className="fintile__label">{label}</span>
      <span className="fintile__value figure">{value}</span>
      <span className="fintile__sub">{sub}</span>
    </div>
  )
}
