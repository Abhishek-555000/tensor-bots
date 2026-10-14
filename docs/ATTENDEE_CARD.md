# 🚀 Attendee Quick Reference Card

Keep this sheet open throughout today's workshop.

---

## 1. Cloning the Repository (Start Here)

> **IMPORTANT:** Do **NOT** fork the repository. Clone directly so you stay in sync with the instructor.

### Using GitHub Desktop
1. Open **GitHub Desktop**.
2. Click **File > Clone repository...** (or press `Ctrl+Shift+O` / `Cmd+Shift+O`).
3. Click the **URL** tab.
4. Repository URL:
   ```text
   https://github.com/md-Yusha/tensor-bots.git
   ```
5. Choose your local folder and click **Clone**.

---

## 2. Catching Up After Each Stage (3 Simple Steps)

At the end of each stage, the instructor merges new code into `main`. Follow these 3 steps to sync:

### In GitHub Desktop:
1. **Discard local changes:**
   - Go to the **Changes** tab on the left.
   - Right-click anywhere in the changed files list and select **Discard all changes...**
   - Confirm discard. *(Never click Commit to save scratch edits!)*
2. **Fetch updates:**
   - Click **Fetch origin** in the top bar.
3. **Pull latest code:**
   - Click **Pull origin** (or `Pull origin with rebase`).

> **Safety note:** Your `.env` and `venv/` are gitignored — discarding changes will **never** delete your API keys or virtual environment!

### Command-Line Alternative (macOS / Linux):
```bash
git restore . && git clean -fd -e .env -e venv && git pull
```

---

## 3. What to Do If "Pull" Is Blocked or Errors

If GitHub Desktop shows a conflict or says pull is blocked:
1. Switch to the **Changes** tab.
2. Select all files, right-click, and click **Discard all changes**.
3. If an untracked file was created inside the repo (outside `.env` / `venv`), delete it.
4. Click **Fetch origin**, then click **Pull origin**.

---

## 4. Emergency Backup: Stage ZIP Download

If git gets stuck or you join late, download the exact solution ZIP for any stage:

```text
https://github.com/md-Yusha/tensor-bots/archive/refs/heads/<stage-name>.zip
```

Replace `<stage-name>` with:
- `stage-0-setup`
- `stage-1-first-agent`
- `stage-2-manager`
- `stage-3-parallel`
- `stage-4-developer`
- `stage-5-reviewer-loop`
- `stage-6-ui`

Unzip into your workshop folder, copy over your `.env`, and resume coding immediately!
