import { useMemo } from 'react'
import { rosette } from '../lib/guilloche'

interface SealProps {
  size?: number
  /** stroke colour; defaults to the engraving teal */
  color?: string
  /** petal count is R/r — different cases get visibly different rosettes */
  petals?: number
  copies?: number
  opacity?: number
  className?: string
  /** seconds per rotation; 0 disables the drift */
  spin?: number
}

/** A guilloché rosette — the engraving printed on the certificates, bonds and
 *  policy documents this system reads. Used as the product mark and, at larger
 *  sizes, as the seal on a decided case file. */
export default function Seal({
  size = 34,
  color = 'var(--engrave)',
  petals = 9,
  copies = 4,
  opacity = 0.9,
  className,
  spin = 0,
}: SealProps) {
  const { paths, extent } = useMemo(() => {
    const R = 46
    const r = R / petals
    const d = r + 12
    // a hypotrochoid reaches (R − r) + d from the centre, which is wider than R
    // whenever d > r — size the viewBox to that or the rosette gets cropped
    return {
      paths: rosette({ R, r, d, copies, steps: 220 }),
      extent: Math.ceil(R - r + d) + 2,
    }
  }, [petals, copies])

  return (
    <svg
      className={className}
      width={size}
      height={size}
      viewBox={`${-extent} ${-extent} ${extent * 2} ${extent * 2}`}
      aria-hidden="true"
      focusable="false"
    >
      <g
        fill="none"
        stroke={color}
        strokeWidth={0.7}
        opacity={opacity}
        style={
          spin
            ? { transformOrigin: 'center', animation: `seal-drift ${spin}s linear infinite` }
            : undefined
        }
      >
        {paths.map((d, i) => (
          <path key={i} d={d} />
        ))}
      </g>
    </svg>
  )
}
