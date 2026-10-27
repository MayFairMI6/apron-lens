# Collaboration

Use short branches and pull requests for app, backend and research changes.
The repository is private; its owner can add teammates through GitHub's
collaborator settings. No collaborators are automatically invited.

## GitHub Desktop

- On the original machine: **File → Add local repository**, then select the
  project root. Its `origin` points to this GitHub repository.
- On another machine: **File → Clone repository**, then select
  `MayFairMI6/airfield-context-ar`.
- Create a branch, make changes, review the changed files, commit, push, and
  open a pull request. Use descriptive commits such as `Improve source report navigation`.

Open the `unity/SurfaceSafetyCoach` subfolder in Unity Hub. The repository root
also contains the Python service and evaluation records; do not create another
Git repository inside the Unity folder.

## Review and checks

Run the model-free tests documented in the README. For a Unity change, record
relevant editor/device checks. For inference changes, compare raw model results
with the baseline; a withheld answer is a model failure, not a correct answer.
Use the development suite for iteration. A new held-out claim requires a new
untouched set and a frozen protocol.

Preserve `.meta` files for Unity assets. Prefer editing different scenes/assets
when working concurrently. Resolve scene/prefab merges in Unity with the change
author when needed; do not blindly accept both YAML versions. Unity caches,
local licenses, tokens and model weights must remain ignored.

Keep frozen source snapshots, datasets and recorded evaluation artifacts intact.
Add a new version for a new experiment. Historical local paths in audit evidence
are provenance, not portable setup instructions; use the root README/docs instead.

## Sensitive or proprietary configuration

Never commit `.env`, model connection tokens, Vuforia licenses, signing keys,
SDK archives or operational airport data. Synthetic report fixtures and original
board/aircraft visuals are the data used here. APK binaries belong in Releases,
not ordinary Git commits.
