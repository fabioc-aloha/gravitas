export function dopplerAsymmetry(axisInclinationDegrees: number) {
  return Math.sin(axisInclinationDegrees * Math.PI / 180)
}

export function observerOrbitRadians(orbitDegrees: number) {
  return orbitDegrees * Math.PI / 180
}

export function fieldOfViewForZoom(zoom: number) {
  return 48 / zoom
}
