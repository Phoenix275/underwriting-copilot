/** A small perspective camera for the portfolio plane.
 *
 *  Deliberately not WebGL. Two hundred markers projected into SVG stay real DOM
 *  nodes, so every case on the plane is focusable, hoverable and reachable by a
 *  screen reader — and the page costs nothing on a phone. The camera is ~20
 *  lines because that is all this view needs. */

export interface Camera {
  /** rake: 0 = flat-on chart, higher = raked into a landscape (radians) */
  rake: number
  /** yaw around the vertical axis (radians) */
  yaw: number
  /** focal length in world units; larger flattens the perspective */
  focal: number
  /** plane extent in world units */
  width: number
  depth: number
  /** viewport */
  cx: number
  cy: number
  /** overall zoom */
  scale: number
}

export interface Projected {
  x: number
  y: number
  /** perspective factor — use it to scale marker size and fade by distance */
  k: number
  /** camera-space depth, for painter's-algorithm sorting */
  depth: number
}

/** Project a point on (or above) the plane.
 *  @param u 0..1 across the plane's width  — the affordability axis
 *  @param v 0..1 across the plane's depth  — the mortality axis
 *  @param h height above the plane in world units */
export function project(cam: Camera, u: number, v: number, h = 0): Projected {
  const x0 = (u - 0.5) * cam.width
  const z0 = (v - 0.5) * cam.depth
  const y0 = -h

  const cy0 = Math.cos(cam.yaw)
  const sy0 = Math.sin(cam.yaw)
  const x1 = x0 * cy0 + z0 * sy0
  const z1 = -x0 * sy0 + z0 * cy0

  const cr = Math.cos(cam.rake)
  const sr = Math.sin(cam.rake)
  const y2 = y0 * cr - z1 * sr
  const z2 = y0 * sr + z1 * cr

  const k = (cam.focal / (cam.focal + z2)) * cam.scale
  return { x: cam.cx + x1 * k, y: cam.cy + y2 * k, k, depth: z2 }
}

/** Project a polyline and return an SVG path. */
export function polyline(
  cam: Camera,
  pts: [number, number, number?][],
  close = false,
): string {
  const d = pts
    .map(([u, v, h], i) => {
      const p = project(cam, u, v, h ?? 0)
      return `${i === 0 ? 'M' : 'L'}${p.x.toFixed(1)} ${p.y.toFixed(1)}`
    })
    .join('')
  return close ? d + 'Z' : d
}

/** Place a caption along an edge of the plane, angled to lie flat on it.
 *  Keeping the axis titles inside the projection means they turn with the
 *  plane instead of floating beside it as detached HTML. */
export function axisLabel(
  cam: Camera,
  from: [number, number],
  to: [number, number],
): { x: number; y: number; angle: number } {
  const a = project(cam, from[0], from[1])
  const b = project(cam, to[0], to[1])
  let angle = (Math.atan2(b.y - a.y, b.x - a.x) * 180) / Math.PI
  // never set a caption upside down
  if (angle > 90) angle -= 180
  if (angle < -90) angle += 180
  return { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2, angle }
}

/** Fit the plane to the viewport by projecting its extremes and solving for the
 *  scale and centre that contain them. Because it re-solves whenever the camera
 *  turns, the view can never overflow its frame while the user drags it — which
 *  is the difference between an orbit control that feels solid and one that
 *  throws half the data off the edge. */
export function fitCamera(
  base: Camera,
  maxHeight: number,
  viewW: number,
  viewH: number,
  pad: { top: number; right: number; bottom: number; left: number },
): Camera {
  const probe: Camera = { ...base, cx: 0, cy: 0, scale: 1 }
  const corners: [number, number, number][] = []
  for (const u of [0, 0.5, 1]) {
    for (const v of [0, 0.5, 1]) {
      for (const h of [0, maxHeight]) corners.push([u, v, h])
    }
  }

  let minX = Infinity
  let maxX = -Infinity
  let minY = Infinity
  let maxY = -Infinity
  for (const [u, v, h] of corners) {
    const p = project(probe, u, v, h)
    minX = Math.min(minX, p.x)
    maxX = Math.max(maxX, p.x)
    minY = Math.min(minY, p.y)
    maxY = Math.max(maxY, p.y)
  }

  const availW = viewW - pad.left - pad.right
  const availH = viewH - pad.top - pad.bottom
  const scale = Math.min(availW / (maxX - minX), availH / (maxY - minY))

  return {
    ...base,
    scale,
    cx: pad.left + availW / 2 - ((minX + maxX) / 2) * scale,
    cy: pad.top + availH / 2 - ((minY + maxY) / 2) * scale,
  }
}

/** A filled quad on the plane surface, optionally lifted to height `h`. */
export function quad(
  cam: Camera,
  u0: number,
  v0: number,
  u1: number,
  v1: number,
  h = 0,
): string {
  return polyline(cam, [
    [u0, v0, h],
    [u1, v0, h],
    [u1, v1, h],
    [u0, v1, h],
  ], true)
}

/** The vertical face joining a lifted region back down to the plane — the
 *  extruded wall that makes a risk band read as terrain rather than as fill. */
export function wall(
  cam: Camera,
  u0: number,
  v: number,
  u1: number,
  h: number,
): string {
  return polyline(cam, [
    [u0, v, 0],
    [u1, v, 0],
    [u1, v, h],
    [u0, v, h],
  ], true)
}
