/** Guilloché — the engraved rosette printed on policy certificates, bonds and
 *  banknotes. It is the house pattern of the document class this system reads,
 *  so it is generated properly rather than faked with a gradient.
 *
 *  A rosette is a hypotrochoid: a point held at distance `d` from the centre of
 *  a circle of radius `r` rolling inside a circle of radius `R`. Drawing the
 *  same curve repeatedly at incrementing phase produces the interference lattice
 *  that makes the pattern hard to photocopy — and, here, hard to mistake for
 *  any other dashboard. */

export interface RosetteOptions {
  /** radius of the fixed outer circle */
  R: number
  /** radius of the rolling inner circle — R/r sets the number of petals */
  r: number
  /** pen offset from the rolling circle's centre */
  d: number
  /** how many phase-shifted copies to overlay */
  copies?: number
  /** samples per copy; higher is smoother and heavier */
  steps?: number
}

/** One hypotrochoid as an SVG path, centred on (0,0). */
function hypotrochoid(
  { R, r, d }: Pick<RosetteOptions, 'R' | 'r' | 'd'>,
  phase: number,
  steps: number,
): string {
  const k = (R - r) / r
  const parts: string[] = []
  for (let i = 0; i <= steps; i++) {
    const t = (i / steps) * Math.PI * 2
    const x = (R - r) * Math.cos(t) + d * Math.cos(k * t + phase)
    const y = (R - r) * Math.sin(t) - d * Math.sin(k * t + phase)
    parts.push(`${i === 0 ? 'M' : 'L'}${x.toFixed(2)} ${y.toFixed(2)}`)
  }
  return parts.join('') + 'Z'
}

/** A full rosette as an array of paths — one per phase-shifted copy. */
export function rosette(opts: RosetteOptions): string[] {
  const { copies = 5, steps = 260 } = opts
  return Array.from({ length: copies }, (_, i) =>
    hypotrochoid(opts, (i / copies) * ((Math.PI * 2) / 12), steps),
  )
}

/** Sinusoidally modulated parallel rules — the other half of the security-print
 *  vocabulary, used as a field background where a rosette would be too loud. */
export function waveLines(
  width: number,
  height: number,
  count: number,
  amplitude: number,
  wavelength: number,
): string[] {
  const step = height / (count - 1)
  const samples = Math.max(24, Math.round(width / 8))
  return Array.from({ length: count }, (_, row) => {
    const y0 = row * step
    // each rule is phase-offset from the last, so the field shears slowly
    const phase = row * 0.55
    const pts: string[] = []
    for (let i = 0; i <= samples; i++) {
      const x = (i / samples) * width
      const y = y0 + Math.sin((x / wavelength) * Math.PI * 2 + phase) * amplitude
      pts.push(`${i === 0 ? 'M' : 'L'}${x.toFixed(1)} ${y.toFixed(2)}`)
    }
    return pts.join('')
  })
}
