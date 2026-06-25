---
name: self-improve
description: >
  Self-review and improvement skill for the Meeting Translator agent. Detects
  shortcomings in recent runs (bad translation, slowness, missing feature,
  errors) and proposes concrete improvements; applies them if the user approves.
  Triggers — "improve yourself", "find your shortcomings", "what can you
  improve", "/self-improve", or when the user expresses dissatisfaction after
  a translation.
---

# Self Improve (Meeting Translator)

Goal: let the agent notice its own shortcomings and propose its own evolution.
Do not change code silently — **detect + propose first, then apply on approval.**

## When it triggers
- The user explicitly asks.
- A translation/STT run gives a poor result (user says "translation is broken",
  "names are wrong", "it was too slow", "speakers are mixed up").
- A periodic review is requested.

## Steps

1. **Collect:** read the files at the agent root (`scripts/`, `.claude/skills/`,
   `README.md`) and review recent outputs (`docs/ru`, `docs/tr`). If the user
   raised a complaint, center on that.

2. **Diagnose:** make the shortcoming concrete — where, and why. Example candidates:
   - No speaker diarization → "who said what" is unclear (pyannote).
   - Term inconsistency on long transcripts → glossary/term list for translation.
   - GPU layer stalls on a new card → setup / compute_type tuning.
   - No batch mode → process all videos in a folder sequentially.
   - Summary format doesn't fit the user → change the template.
   - Weak ffmpeg/whisper error handling → better error messages.

3. **Propose:** for each shortcoming give a 1-2 sentence concrete proposal +
   cost (small/medium) + reversible or not. Prioritize if there are several.

4. **Approve and apply:** after the user picks, edit the relevant file
   (`scripts/transcribe.py`, a SKILL.md, `requirements.txt`, etc.). If a new
   dependency is needed, add it to `requirements.txt` and remind about setup.

5. **Record:** write the change as a one-line entry in the "Changelog" section
   of `README.md` (date if the user gives one; otherwise "undated").

## Rule
- Prefer root-cause fixes over symptom suppression (e.g. if translation is bad,
  fix the parameter/prompt — do not swallow the error).
- Break large changes into small steps; approve each one separately.
