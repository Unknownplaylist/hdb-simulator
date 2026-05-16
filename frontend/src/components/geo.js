// Equirectangular projection around central Singapore. Good enough at this
// latitude without a real proj library.
const REF_LON = 103.8198
const REF_LAT = 1.3521

// 1 scene unit = ~111 m. Picked so dense estates stop overlapping at ~30 m spacing.
const UNITS_PER_DEGREE = 1000
const METERS_PER_UNIT = 111000 / UNITS_PER_DEGREE

// Vertical exaggeration so 30 m blocks aren't pancakes next to 140 m towers.
const HEIGHT_EXAG = 1.6

export function projectLonLat(lon, lat) {
  const x = (lon - REF_LON) * UNITS_PER_DEGREE
  const z = -(lat - REF_LAT) * UNITS_PER_DEGREE  // north -> -Z
  return [x, z]
}

export function buildingHeight(heightM) {
  return (heightM / METERS_PER_UNIT) * HEIGHT_EXAG
}

export function buildingSide(footprintAreaM2) {
  return Math.sqrt(footprintAreaM2 || 400) / METERS_PER_UNIT
}
