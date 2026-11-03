# AirfieldLens scenery workflow

For rendering, scenery, airport geometry and visual movement changes, use the
multi-agent workflow requested by the project owner. Keep work within AirfieldLens (the existing apron-lens repository).

- Assign a reference/placement agent to verify source geometry, dimensions,
  coordinate conventions, visual references and free-asset reuse terms.
- Assign an implementation agent a bounded set of files. Combine suitable free
  assets with custom geometry when this improves a coherent, recognisable scene.
- Have a different agent review placement and geometry independently. The root
  agent integrates the work and inspects the rendered result in the native app.
- Give agents separate file ownership. Share discovered coordinate or source
  errors promptly; do not duplicate a full source model and a replacement mesh.
- Scale the depth of review to the change. Reuse verified sources and audits for
  small adjustments; do not restart broad renderer or asset searches without a
  concrete need. For a small change, the reference and independent review may be
  combined, but the reviewer must be different from its implementer.
- Preserve source attribution, original free-model inputs, conversion settings
  and a clear distinction between mapped geometry and authored approximations.
  Do not claim an exact current reconstruction from historical or incomplete data.
- Verify the visible result, movement alignment, lighting and relevant source-clock
  behavior. Record failures honestly and keep learner-facing text simple.

This workflow does not expand product scope, change existing research results,
or authorise paid assets. The external driver remains responsible for scenario
time, movement, conditions and reports; scenery must not invent report evidence.
