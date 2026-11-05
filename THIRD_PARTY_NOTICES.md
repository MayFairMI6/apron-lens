# Third-party software and assets

- **Unity 6000.2.2f1** and Unity packages retain their respective Unity terms.
  The editor, Android toolchain and generated caches are not redistributed here.
- **Vuforia Engine 11.4.4** is a separately licensed dependency. The package
  archive and application license configuration are excluded. Obtain it through
  the official Vuforia distribution: https://developer.vuforia.com/downloads/sdk.
- **Qwen/Qwen2.5-VL-3B-Instruct** is pinned by
  `config/model-manifest.json`. This variant's upstream license is the Qwen
  Research License, described in the model manifest as non-commercial research
  and evaluation. Model weights are excluded. Consult the upstream model/license
  before use: https://huggingface.co/Qwen/Qwen2.5-VL-3B-Instruct.
- **Candidate models** in `backbone/models.json` (Qwen3-VL-4B/8B-Instruct,
  Qwen3.5-9B, Gemma 4 E4B-it) are listed with Apache-2.0 upstream licenses as
  reported by Hugging Face on 2026-10-27. They are optional, downloaded locally
  only, and their weights are excluded. Check each model card before use.
- Python dependencies retain their individual licenses. The verified versions
  are recorded in `requirements-qwen.lock.txt`.
- The fictional board artwork, procedural generic airliner meshes and synthetic
  scenario fixtures were created for this project. No aircraft-manufacturer
  logos, commercial airport maps or downloaded aircraft models are included.
- The phone outline is illustrative. Samsung's specification is linked as the
  source for the base Galaxy S24 viewport dimensions; it is not an official
  Samsung simulator or endorsement.

No open-source license has yet been selected for the original project code.
Third-party terms are not replaced by this notice.

The current environment also includes FlightGear TerraSync Heathrow Terminal 5
scenery. Its AC3D source, textures, converted OBJ, conversion script, attribution
and GPL text are retained. See
`unity/SurfaceSafetyCoach/Assets/SurfaceSafety/WorldAR/Heathrow/ATTRIBUTION.txt`
and `COPYING.txt` for the asset's provenance and terms. Those terms apply to
the third-party scenery independently of the original application code.
