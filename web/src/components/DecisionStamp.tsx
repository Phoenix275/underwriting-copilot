import { motion, useReducedMotion } from 'motion/react'
import Seal from './Seal'
import type { Verdict } from '../data/types'
import { verdictVar } from '../lib/format'

/** The decision, struck onto the file the way an underwriter's stamp lands on
 *  paper: it arrives at an angle, presses in, and settles. One motion moment
 *  per case, on the thing the whole page exists to say. */
export default function DecisionStamp({
  verdict,
  decision,
  rateClass,
}: {
  verdict: Verdict
  decision: string
  rateClass: string
}) {
  const reduced = useReducedMotion()
  const color = verdictVar(verdict)
  // the word above already says "declined" or "referred" — the stamp only has
  // room for what made it so
  const because = rateClass.replace(/^(Referred|Declined)\s*—\s*/, '')

  return (
    <motion.div
      className="stamp"
      style={{ color }}
      initial={reduced ? false : { scale: 1.45, opacity: 0, rotate: -9 }}
      animate={{ scale: 1, opacity: 1, rotate: -3 }}
      transition={{ duration: 0.42, ease: [0.16, 0.84, 0.28, 1] }}
    >
      <Seal size={124} color={color} petals={11} copies={5} opacity={1} />
      <div className="stamp__text">
        <span className="stamp__word">{decision}</span>
        <span className="stamp__rate">{because}</span>
      </div>
    </motion.div>
  )
}
