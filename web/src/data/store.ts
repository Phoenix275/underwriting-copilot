import { BUNDLED, type Dataset } from './source'

/** The dataset the scoring engine is currently working against.
 *
 *  `score.ts` needs the model coefficients and decision thresholds outside of
 *  React — it is a pure module the verification script also runs under Node.
 *  This is the one piece of shared mutable state, set once when the app loads
 *  and read through a getter so a live dataset replaces the bundled defaults
 *  everywhere rather than only in the components that re-render. */

let active: Dataset = BUNDLED

export const activeDataset = () => active
export const activeReport = () => active.report

export function setActiveDataset(next: Dataset) {
  active = next
}
