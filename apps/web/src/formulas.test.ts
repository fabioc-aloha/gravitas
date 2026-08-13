import { describe, expect, it } from 'vitest'

import { modelFormulas } from './formulas'

describe('model formulas', () => {
  it('includes the documented redshift and emissivity relationships', () => {
    expect(modelFormulas.map((formula) => formula.expression)).toEqual(
      expect.arrayContaining([
        'I_obs = g^(3 + α) I_emit',
        'T(r) = T_in (r / r_in)^(-p)',
      ]),
    )
  })
})
