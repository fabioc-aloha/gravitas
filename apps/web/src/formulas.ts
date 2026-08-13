export const modelFormulas = [
  {
    expression: 'I_obs = g^(3 + α) I_emit',
    note: 'Observed intensity is transferred by the redshift factor g and spectral index α.',
    title: 'Relativistic transfer',
  },
  {
    expression: 'T(r) = T_in (r / r_in)^(-p)',
    note: 'Temperature decreases radially; p is represented by the emissivity-slope control in this preview.',
    title: 'Disk temperature profile',
  },
  {
    expression: 'r_in ≥ r_ISCO(a, flow)',
    note: 'The physical inner edge is constrained by spin and prograde or retrograde flow.',
    title: 'Inner disk boundary',
  },
  {
    expression: 'H / R = disk thickness',
    note: 'A larger H/R produces a geometrically thicker accretion flow.',
    title: 'Disk geometry',
  },
  {
    expression: 'θ_FOV ∝ 1 / zoom',
    note: 'Zoom narrows the field of view; it does not change black-hole physics.',
    title: 'Camera framing',
  },
]
