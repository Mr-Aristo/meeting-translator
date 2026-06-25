---
name: translate-meeting
description: >
  Produces a Russian transcript + Turkish translation from a meeting recording
  (video/audio in Russian). The user gives a file path; the skill first extracts
  the Russian text via ffmpeg+whisper (docs/ru/), then Claude translates it to
  Turkish (docs/tr/, summary + full translation) and writes a standalone summary
  (docs/summary/). Triggers — "translate this meeting", "translate the video",
  "/translate-meeting <path>", "transcribe and translate this recording".
---

# Translate Meeting (Meeting Translator)

Goal: take a recording file the user provides (video or audio, Russian speech),
first transcribe it to Russian text, then translate to Turkish, and save both files.

**Important note (remind the user if needed):** the agent does NOT "listen live"
to the video. It takes the file and processes it offline — so length is not a limit.

## Input

Get a file path from the user (e.g. `C:\Users\Emre\Videos\meeting1.mp4`).
If no path is given, ask for it. Use Windows paths with spaces/quotes as-is.

## Step 0 — Preflight (auto-setup)

Find the agent root (3 levels above this skill: `.../meeting-translator`). The
environment needed to run the agent is auto-installed if missing — do NOT block on
asking the user for approval first.

1. Check each requirement:
   - `.venv` python exists? (`<root>\.venv\Scripts\python.exe`)
   - `ffmpeg` on PATH? (`Get-Command ffmpeg`)
   - `faster_whisper` importable in the venv?
     (`<root>\.venv\Scripts\python.exe -c "import faster_whisper"`)
   - Whisper model present in the repo-local cache `<root>\.models`? The
     transcription model lives under `<root>\.models\hub\models--Systran--faster-whisper-large-v3`.
     `transcribe.py` pins `HF_HOME` to `<root>\.models`, so the model is always
     read from / downloaded into the repo — never a machine-wide cache.
2. If **any** check fails, tell the user what's missing in one line, then run setup
   automatically (it is idempotent — safe to re-run, only installs what's missing):
   `powershell -ExecutionPolicy Bypass -File <root>\scripts\setup.ps1`
   (Installs ffmpeg via winget + faster-whisper into the venv, pre-downloads the
   whisper model into `<root>\.models`, and tests the GPU.) The model is a few GB,
   so the first setup on a fresh machine may take a while — that is expected, not a hang.
   If only the model is missing, the first transcription run will also fetch it
   automatically into `<root>\.models`; running setup just front-loads that download.
3. Re-check the requirements after setup. If ffmpeg was just installed, its PATH may
   not be live in the current shell — locate the winget `ffmpeg.exe` and use its full
   path for the run (or have the user reopen the terminal). Then continue.
4. If all checks already pass, skip setup silently and continue.

## Step 1 — Russian transcript (STT)

Derive the output name from the input file (basename without extension). Then run
the venv python:

```
<root>\.venv\Scripts\python.exe <root>\scripts\transcribe.py "<input-path>" --out "<root>\docs\ru\<name>_RU.md"
```

- The script writes progress to stderr (segment count, device). Be patient on long files.
- With a GPU, large-v3 is fast; otherwise the script falls back to CPU (slow but works).
- When done, `docs/ru/<name>_RU.md` holds the timestamped Russian transcript.

## Step 2 — Turkish translation (done by Claude)

Read `docs/ru/<name>_RU.md` and translate it to Turkish. Output:
`<root>\docs\tr\<name>_TR.md`. Structure:

```markdown
# <name> — Turkish

## Summary
- Topic:
- Decisions made:
- Who owns what (if any):
- Key points / open questions:

## Full translation
[0:00:00] ...
[0:00:12] ...
```

Translation rules:
- Preserve proper nouns and technical terms; give the original in parentheses if needed.
- Carry timestamps ([H:MM:SS]) over unchanged.
- For very long transcripts, translate section by section but keep terminology/name
  consistency (translate the same way you did earlier).
- Mark unclear/uncertain parts with `[?]`; do not invent.

## Step 2.5 — Standalone summary

Write a separate, self-contained summary file so the user can read the key points
without opening the (often long) full translation. Output:
`<root>\docs\summary\<name>_SUMMARY.md`. Default language Turkish (match the TR
translation's terminology/names); if the user asked for the summary in another
language, follow that. Create the `docs/summary/` folder if it does not exist.

Structure:

```markdown
# <name> — Özet (Summary)

- Kaynak (Source): <input-path>
- Tarih (Date): <recording date if known>

## Konu (Topic)
...

## Kararlar (Decisions)
- ...

## Sorumlular (Owners)
- <kişi>: <ne yapıyor>

## Önemli noktalar / açık sorular (Key points / open questions)
- ...

## Aksiyonlar (Action items)
- [ ] ...
```

Keep it concise — bullet points, no full transcript. Reuse the same `[?]` markers
for uncertain parts; do not invent. This file is also a superset of the "## Summary"
block embedded in the TR translation, so the two should stay consistent.

## Step 3 — Report

Give the user all three file paths (RU transcript, TR translation, summary) and also
show the Turkish summary in chat, so they see the key points without opening any file.

In the same message, offer the action plan so the user decides while the summary is
in front of them and the session context is still alive:
**"Aksiyon planı çıkarayım mı? (TR / RU, varsayılan TR)"**. If the user accepts, run
the `meeting-plan` skill with this recording's name — it reads the RU transcript as the
source of truth and writes the plan to `docs/plans/<name>_PLAN_<LANG>.md`.
