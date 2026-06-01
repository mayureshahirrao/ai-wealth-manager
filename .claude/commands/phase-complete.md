# /phase-complete

Run this command at the conclusion of every phase to ensure consistent
documentation, versioning, and git hygiene.

## What this command does

Execute ALL of the following steps in order. Do not skip any step.

---

## STEP 1 — Confirm what changed

Run `git status --short` and `git diff --stat HEAD` to identify all modified
and untracked files introduced during this phase. Summarise them.

---

## STEP 2 — Determine the new version number

Read the current `VERSION` file. Apply the versioning policy:
- `MAJOR` (x.0.0) — breaking API or schema changes
- `MINOR` (0.x.0) — new phase or significant feature set completed
- `PATCH` (0.0.x) — bug fixes, dependency pins, config corrections

For a completed phase, increment MINOR. For a bugfix/stabilisation commit,
increment PATCH. Update ALL THREE version locations:
- `VERSION` (root, single line)
- `backend/app/core/config.py` → `APP_VERSION`
- `frontend/package.json` → `"version"`

---

## STEP 3 — Update CHANGELOG.md

Add a new entry at the TOP of CHANGELOG.md (below the header, above the
previous version). Include:
- Version number and date
- Phase name and number
- Every file created or modified with a one-line description
- Any bugs fixed during the phase
- Verified working features (confirmed by user)

Format:
```
## [X.Y.Z] — YYYY-MM-DD

### Added — Phase N: <Name>
- file.py — description
...

### Fixed
- description of bug and fix

### Verified Working
- feature ✅
```

---

## STEP 4 — Update README.md

Make these specific updates:
1. Version badge at top: `> **Version X.Y.Z**`
2. Project Status table: mark completed phase as `✅ Done`
3. Known Limitations: remove items that are now resolved
4. Quick Start: add any new setup steps introduced this phase
5. Versioning table at bottom: update phase row from "planned" to actual description

---

## STEP 5 — Generate the activity log

Create `docs/project_activity_log_vX.Y.Z.txt` with the following sections:

```
SECTION 1  — Project Inception (brief reference or "see v0.4.0 log")
SECTION 2  — Phase 1 summary (reference prior log)
...
SECTION N  — This phase (FULL DETAIL):
  N.1  Instructions — exact user prompts verbatim
  N.2  Recommendations & Decisions — options presented, choice made, rationale
  N.3  Actions Performed — every file created/modified with purpose
  N.4  Testing & Verification — commands run, outputs observed, issues found
  N.5  Deliverables — list of all outputs produced
SECTION N+1 — Artifacts Index (cumulative, all files ever touched)
SECTION N+2 — Pending Work (next phases, itemised checklist)
```

Each log file is self-contained — prior phase summaries can reference the
previous log file rather than reproducing full detail.

---

## STEP 6 — Git commit

Stage ALL changed files from this phase plus the new docs. Write a commit
message following this format:

```
feat/chore/fix: vX.Y.Z — <phase name and one-line summary>

<Phase name> key additions:
- bullet 1
- bullet 2
...

Bug fixes:
- description (if any)

Documentation:
- README.md updated: <what changed>
- CHANGELOG.md: v X.Y.Z entry added
- Activity log: docs/project_activity_log_vX.Y.Z.txt

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

Then push to origin master:
```
git push origin master
```

---

## STEP 7 — Report to user

After completing all steps, report:

1. ✅ Version bumped: OLD → NEW
2. ✅ Files committed: N files, X insertions
3. ✅ Activity log: docs/project_activity_log_vX.Y.Z.txt (N lines)
4. ✅ README and CHANGELOG updated
5. 📋 Phase 6 actions (list the pending work for the next phase)
