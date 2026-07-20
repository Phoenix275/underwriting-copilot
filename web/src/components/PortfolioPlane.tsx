import { useEffect, useMemo, useRef, useState } from 'react'
import { useReducedMotion } from 'motion/react'
import { report } from '../data'
import type { Case } from '../data/types'
import { planePosition } from '../lib/plane'
import {
  axisLabel,
  fitCamera,
  polyline,
  project,
  quad,
  wall,
  type Camera,
} from '../lib/projection'
import { verdictVar } from '../lib/format'

/* The plane's two axes are the product's whole argument: mortality risk on one,
   financial strain on the other. Risk appetite is drawn as terrain — the
   decline band is a raised plateau and the financial-referral strip a low step,
   so a case that has to leave the automated path is visibly standing on higher
   ground rather than merely tinted a different colour. */

const A_LINE = report.decisioning.thresholds.a_line / 100
const D_LINE = report.decisioning.thresholds.d_line / 100
/** strainScore puts the affordability fail line at 80 of 100 */
const FAIL_U = 0.8

const H_DECLINE = 62
const H_STRAIN = 26

function terrainHeight(u: number, v: number): number {
  if (v >= D_LINE) return H_DECLINE
  if (u >= FAIL_U) return H_STRAIN
  return 0
}

interface Props {
  items: Case[]
  selectedId: string
  onOpen: (id: string) => void
  onHover: (c: Case | null) => void
  hovered: Case | null
}

export default function PortfolioPlane({ items, selectedId, onOpen, onHover, hovered }: Props) {
  const reduced = useReducedMotion()
  const svgRef = useRef<SVGSVGElement>(null)
  const [rake, setRake] = useState(reduced ? 0.82 : 0.16)
  const [yaw, setYaw] = useState(-0.2)
  const drag = useRef<{ x: number; y: number; rake: number; yaw: number } | null>(null)

  /* The viewBox tracks the element's real aspect ratio. Without this the SVG
     letterboxes inside its box and the plane floats in dead margin — the frame
     has to match the frame it was given before fitCamera can fill it. */
  const [box, setBox] = useState({ w: 1000, h: 560 })
  useEffect(() => {
    const el = svgRef.current
    if (!el) return
    const ro = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect
      if (width > 0 && height > 0) setBox({ w: Math.round(width), h: Math.round(height) })
    })
    ro.observe(el)
    return () => ro.disconnect()
  }, [])
  const VIEW_W = box.w
  const VIEW_H = box.h

  /* On load the plane lifts from a flat chart into a raked landscape. It is the
     one camera move in the product, and it exists to say that these are two
     independent axes and not one ranked list. */
  useEffect(() => {
    if (reduced) return
    let raf = 0
    const start = performance.now()
    const from = 0.16
    const to = 0.82
    const dur = 1150
    const tick = (now: number) => {
      const t = Math.min((now - start) / dur, 1)
      const eased = 1 - Math.pow(1 - t, 3)
      setRake(from + (to - from) * eased)
      if (t < 1) raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [reduced])

  const cam: Camera = useMemo(
    () =>
      fitCamera(
        { rake, yaw, focal: 1600, width: 800, depth: 800, cx: 0, cy: 0, scale: 1 },
        H_DECLINE,
        VIEW_W,
        VIEW_H,
        // gutters for the ticks and captions, proportional so a phone-width
        // frame does not lose a third of itself to a fixed 64px margin
        {
          top: 14,
          right: Math.max(16, VIEW_W * 0.03),
          bottom: Math.max(26, VIEW_H * 0.08),
          left: Math.max(30, VIEW_W * 0.06),
        },
      ),
    [rake, yaw, VIEW_W, VIEW_H],
  )

  const uCaption = axisLabel(cam, [0, -0.13], [1, -0.13])
  const vCaption = axisLabel(cam, [-0.16, 0], [-0.16, 1])

  /* Painter's algorithm — far markers drawn first, so near ones overlap them. */
  const markers = useMemo(() => {
    return items
      .map((c) => {
        const { u, v } = planePosition(c)
        const h = terrainHeight(u, v)
        const p = project(cam, u, v, h)
        return { c, u, v, h, p }
      })
      .sort((a, b) => b.p.depth - a.p.depth)
  }, [items, cam])

  const gridLines = useMemo(() => {
    const lines: string[] = []
    for (let i = 0; i <= 10; i++) {
      const t = i / 10
      lines.push(polyline(cam, [[t, 0], [t, 1]]))
      lines.push(polyline(cam, [[0, t], [1, t]]))
    }
    return lines
  }, [cam])

  function onPointerDown(e: React.PointerEvent) {
    ;(e.target as Element).setPointerCapture?.(e.pointerId)
    drag.current = { x: e.clientX, y: e.clientY, rake, yaw }
  }

  function onPointerMove(e: React.PointerEvent) {
    const d = drag.current
    if (!d) return
    const w = svgRef.current?.clientWidth || 900
    setYaw(Math.max(-0.6, Math.min(0.6, d.yaw + ((e.clientX - d.x) / w) * 1.6)))
    setRake(Math.max(0.12, Math.min(1.15, d.rake + ((e.clientY - d.y) / w) * 1.6)))
  }

  function endDrag() {
    drag.current = null
  }

  const axisTicks = [0, 25, 50, 75, 100]

  return (
    <div className="plane">
      <svg
        ref={svgRef}
        className="plane__svg"
        viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
        role="img"
        aria-label={`Portfolio plane. ${items.length} cases plotted by mortality risk and financial strain. Each case is also listed in the queue below.`}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={endDrag}
        onPointerCancel={endDrag}
        onPointerLeave={() => {
          endDrag()
          onHover(null)
        }}
      >
        {/* ---- decision regions, lowest first ---- */}
        <path className="plane__region plane__region--pass" d={quad(cam, 0, 0, FAIL_U, A_LINE)} />
        <path className="plane__region plane__region--refer" d={quad(cam, 0, A_LINE, FAIL_U, D_LINE)} />

        {/* financial-referral step */}
        <path className="plane__wall plane__wall--strain" d={wall(cam, FAIL_U, D_LINE, 1, H_STRAIN)} />
        <path
          className="plane__region plane__region--strain"
          d={quad(cam, FAIL_U, 0, 1, D_LINE, H_STRAIN)}
        />

        {/* decline plateau */}
        <path className="plane__wall plane__wall--decline" d={wall(cam, 0, D_LINE, 1, H_DECLINE)} />
        <path
          className="plane__region plane__region--decline"
          d={quad(cam, 0, D_LINE, 1, 1, H_DECLINE)}
        />

        {/* ---- engraved grid ---- */}
        <g className="plane__grid">
          {gridLines.map((d, i) => (
            <path key={i} d={d} />
          ))}
        </g>
        <path className="plane__edge" d={quad(cam, 0, 0, 1, 1)} />

        {/* ---- axis ticks and captions, projected so they turn with the plane ---- */}
        <g className="plane__ticks">
          {axisTicks.map((t) => {
            const p = project(cam, -0.04, t / 100, 0)
            return (
              <text key={`v${t}`} x={p.x} y={p.y} textAnchor="end" dominantBaseline="middle">
                {t}
              </text>
            )
          })}
          {axisTicks.map((t) => {
            const p = project(cam, t / 100, -0.045, 0)
            return (
              <text key={`u${t}`} x={p.x} y={p.y} textAnchor="middle" dominantBaseline="middle">
                {t}
              </text>
            )
          })}
        </g>
        <g className="plane__caption">
          <text
            x={uCaption.x}
            y={uCaption.y}
            transform={`rotate(${uCaption.angle} ${uCaption.x} ${uCaption.y})`}
            textAnchor="middle"
          >
            Financial strain →
          </text>
          <text
            x={vCaption.x}
            y={vCaption.y}
            transform={`rotate(${vCaption.angle} ${vCaption.x} ${vCaption.y})`}
            textAnchor="middle"
          >
            Mortality risk →
          </text>
        </g>

        {/* ---- markers ---- */}
        <g className="plane__markers">
          {markers.map(({ c, u, v, h, p }, i) => {
            const isSel = c.id === selectedId
            const isHov = hovered?.id === c.id
            const lift = isSel ? 46 : isHov ? 24 : 0
            const top = lift ? project(cam, u, v, h + lift) : p
            const r = Math.max(3.4, 5.2 * p.k) * (isSel ? 1.7 : isHov ? 1.35 : 1)
            return (
              <g
                key={c.id}
                className={`plane__marker${isSel ? ' is-selected' : ''}`}
                style={
                  reduced ? undefined : ({ ['--i' as string]: i } as React.CSSProperties)
                }
              >
                {lift > 0 && (
                  <line className="plane__stem" x1={p.x} y1={p.y} x2={top.x} y2={top.y} />
                )}
                <circle
                  className="plane__dot"
                  cx={top.x}
                  cy={top.y}
                  r={r}
                  fill={verdictVar(c.verdict)}
                  tabIndex={0}
                  role="button"
                  aria-label={`${c.name}, ${c.id}. Risk ${c.risk_score} of 100, ${c.afford.label.toLowerCase()}. ${c.decision}.`}
                  onPointerEnter={() => onHover(c)}
                  onFocus={() => onHover(c)}
                  onBlur={() => onHover(null)}
                  onClick={() => onOpen(c.id)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault()
                      onOpen(c.id)
                    }
                  }}
                />
              </g>
            )
          })}
        </g>
      </svg>

      <p className="plane__hint eyebrow">Drag to turn · click a case to open it</p>
    </div>
  )
}
