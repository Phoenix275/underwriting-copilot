/** Engraved line icons — single-weight strokes, drawn to match the hairlines
 *  used everywhere else rather than imported from a generic icon set. */

const box = { viewBox: '0 0 24 24', 'aria-hidden': true, focusable: 'false' } as const

export const IconPlane = (p: { className?: string }) => (
  <svg {...box} {...p}>
    <path d="M2 16 12 9l10 7-10 5z" />
    <path d="M12 9V3" />
    <circle cx="12" cy="3" r="1.6" />
  </svg>
)

export const IconFile = (p: { className?: string }) => (
  <svg {...box} {...p}>
    <path d="M5 3h9l5 5v13H5z" />
    <path d="M14 3v5h5" />
    <path d="M8.5 13h7M8.5 17h4.5" />
  </svg>
)

export const IconFlow = (p: { className?: string }) => (
  <svg {...box} {...p}>
    <circle cx="5" cy="6" r="2" />
    <circle cx="5" cy="18" r="2" />
    <circle cx="19" cy="12" r="2" />
    <path d="M7 6h5a5 5 0 0 1 5 5v.5M7 18h5a5 5 0 0 0 5-5v-.5" />
  </svg>
)

export const IconEvidence = (p: { className?: string }) => (
  <svg {...box} {...p}>
    <path d="M4 20V9M9.33 20V5M14.67 20v-8M20 20v-5" />
    <path d="M3 20h18" />
  </svg>
)

export const IconScore = (p: { className?: string }) => (
  <svg {...box} {...p}>
    <path d="M12 4v16M4 12h16" />
    <circle cx="12" cy="12" r="9" />
  </svg>
)

export const IconArrow = (p: { className?: string }) => (
  <svg {...box} {...p}>
    <path d="M5 12h14M13 6l6 6-6 6" />
  </svg>
)

export const IconClose = (p: { className?: string }) => (
  <svg {...box} {...p}>
    <path d="M6 6l12 12M18 6L6 18" />
  </svg>
)
