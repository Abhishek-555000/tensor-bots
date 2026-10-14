# Tensor Bots — Instructor Event Runbook

This runbook guides the workshop instructor through advancing branches on `main` during the live workshop.

---

## Golden Rules for the Instructor

1. **NEVER force-push to `main` (`git push --force` is strictly forbidden).**
2. **Always use `--ff-only` (`git merge --ff-only <branch>`).** If `--ff-only` fails, STOP and diagnose before proceeding.
3. **If a wrong branch was merged, fix it with `git revert`, NEVER `git reset`.**
4. **Exactly ONE designated person** executes git merge and push commands per stage.
5. **Verify the push on github.com** before announcing to attendees to pull.
6. **Clearly announce the stage number** to the room when the push completes.

---

## Linear Stage Progression Order

Merge branches in this exact sequential order at the **END** of each stage:

1. `stage-0-setup`
2. `stage-1-first-agent`
3. `stage-2-manager`
4. `stage-3-parallel`
5. `stage-4-developer`
6. `stage-5-reviewer-loop`
7. `stage-6-ui`

---

## Stage-by-Stage Merge Commands

### At the end of Stage 0 (Setup & Verification)
```bash
git switch main
git pull
git merge --ff-only stage-0-setup
git push origin main
```
*Verify on GitHub, then announce: "Stage 0 is merged to main. Please discard changes, fetch, and pull!"*

### At the end of Stage 1 (First Agent - Researcher)
```bash
git switch main
git pull
git merge --ff-only stage-1-first-agent
git push origin main
```
*Verify on GitHub, then announce: "Stage 1 is merged to main. Please discard changes, fetch, and pull!"*

### At the end of Stage 2 (Manager Decomposition)
```bash
git switch main
git pull
git merge --ff-only stage-2-manager
git push origin main
```
*Verify on GitHub, then announce: "Stage 2 is merged to main. Please discard changes, fetch, and pull!"*

### At the end of Stage 3 (Parallel Fan-Out & Join)
```bash
git switch main
git pull
git merge --ff-only stage-3-parallel
git push origin main
```
*Verify on GitHub, then announce: "Stage 3 is merged to main. Please discard changes, fetch, and pull!"*

### At the end of Stage 4 (Real Developer & Sandbox Tools)
```bash
git switch main
git pull
git merge --ff-only stage-4-developer
git push origin main
```
*Verify on GitHub, then announce: "Stage 4 is merged to main. Please discard changes, fetch, and pull!"*

### At the end of Stage 5 (Reviewer Feedback Loop)
```bash
git switch main
git pull
git merge --ff-only stage-5-reviewer-loop
git push origin main
```
*Verify on GitHub, then announce: "Stage 5 is merged to main. Please discard changes, fetch, and pull!"*

### At the end of Stage 6 (FastAPI SSE & Desktop UI)
```bash
git switch main
git pull
git merge --ff-only stage-6-ui
git push origin main
```
*Verify on GitHub, then announce: "Stage 6 is merged to main. Full stack application complete!"*

---

## Emergency Troubleshooting

- **Merge fails with "Not possible to fast-forward":**
  Do NOT force or create a merge commit. Check `git log -n 5 --graph --oneline main <branch>` to identify diverged commits.
- **Accidental commit made directly on `main`:**
  Revert the commit using `git revert <commit-sha>`.
- **Attendee is stuck or fell behind:**
  Direct them to download the ZIP archive of the current stage branch directly:
  `https://github.com/md-Yusha/tensor-bots/archive/refs/heads/<branch>.zip`
