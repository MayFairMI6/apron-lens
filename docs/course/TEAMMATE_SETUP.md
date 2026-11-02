# Teammate setup

The current code is on `codex/checkpoint1-controller-training` in [the Checkpoint 1 pull request](https://github.com/MayFairMI6/apron-lens/pull/22).
Until it is merged, cloning only `main` does not give you the demonstrated version.

## Read or run without making a fork

```sh
git clone --branch codex/checkpoint1-controller-training --single-branch https://github.com/MayFairMI6/apron-lens.git apronlens-checkpoint1
cd apronlens-checkpoint1
git rev-parse HEAD
```

Read `docs/course/CHECKPOINT1_CURRENT.md` before installing dependencies. It has
model-free tests and separate native simulator/model setup. A clone does not include
model weights, Unity, Xcode, simulator runtimes or the original machine's token.

## Fork and experiment

Use **Fork** on the repository page and choose your own account. Copying only the
default branch is sufficient if you then fetch the Checkpoint 1 branch explicitly:

```sh
git clone https://github.com/YOUR-USERNAME/apron-lens.git
cd apron-lens
git remote add upstream https://github.com/MayFairMI6/apron-lens.git
git fetch upstream codex/checkpoint1-controller-training
git switch -c my-checkpoint1-preparation upstream/codex/checkpoint1-controller-training
git rev-parse HEAD
```

Replace YOUR-USERNAME with your GitHub account. If an upstream remote already
exists, inspect `git remote -v` and use the existing correct remote instead of adding
it again. Work on your preparation branch. After reviewing your own changes,
commit only the intended files and push that branch to your fork. Open a pull
request to share any proposed changes; do not alter the frozen research records.

GitHub also lets a new fork copy all branches by clearing its default-branch-only
option. Fetching the named upstream branch works even when a fork initially
contains only main. [Official GitHub fork guidance](https://docs.github.com/en/pull-requests/how-tos/work-with-forks/fork-a-repo).

## Prepare with an agent

Give the agent `TEAMMATE_AGENT_PROMPT.txt`, your presenter letter/name and the
role plan. Supply the video or selected clips separately if the agent supports
them. The source recording is large and is not stored in Git history. An agent
without video access can check documents and code, but must not claim to have
visually reviewed the footage. The handoff bundle includes representative frames.

## Smartphone boundary

The app is a native Unity-built iOS Simulator app. Its virtual camera and external
driver are working, but it has not been verified on a physical smartphone in this
delivery. The assignment explicitly asks for smartphone execution. Keep that gap
visible; simulator success is not proof of physical AR tracking or phone performance.

Visual environment settings

Add `--environment rain`, `--environment snow` or `--environment dusk` to the existing `backend.training` launch command. Default clear daytime remains unchanged. The same external source clock drives weather/light visuals and traffic, including acceleration and pauses. These settings do not yet change aircraft performance or operational reports. The dusk profile is one late-afternoon-to-night source hour, not a full 24-hour cycle. See IMPLEMENTATION_DOCKET.md for the remaining weather work.
