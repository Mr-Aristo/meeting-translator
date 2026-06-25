# Meeting Translator — RU→TR

Personal Claude Code agent that translates Russian meeting recordings
(video/audio) into Turkish. You give a file path; you get two files: the full
Russian transcript + the Turkish translation (summary + timestamped full text).

## How it works

1. `ffmpeg` extracts audio from the video.
2. `faster-whisper` (large-v3, GPU) transcribes the audio to **Russian** → `docs/ru/<name>_RU.md`
3. Claude translates the text to **Turkish** → `docs/tr/<name>_TR.md` (summary + full translation)
4. (optional) Claude turns the recording into an **action plan** → `docs/plans/<name>_PLAN_<LANG>.md`
   (action items / decisions / open questions; language TR or RU, asked each time, default TR)

> Note: the agent does not "listen live" to the video. It takes the file and
> processes it offline — so recording length is not a limit (a 3-hour recording
> is fine too).

## Setup (once)

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

This command:
- installs `ffmpeg` via winget if missing,
- creates `.venv` and installs `faster-whisper` plus CUDA libraries,
- tests the GPU (RTX 5060 → large-v3 is fast on GPU; if the GPU misbehaves the
  agent falls back to CPU automatically).

## Usage

Open Claude Code in this folder, then:

```
/translate-meeting C:\Users\Emre\Videos\meeting1.mp4
```

or in natural language: "translate this meeting: <file-path>".

## Layout

```
meeting-translator/
├── .claude/
│   ├── agents/meeting-translator.md   # agent definition
│   └── skills/
│       ├── translate-meeting/         # main skill: STT + translation
│       ├── meeting-plan/              # action plan from a translated recording
│       └── self-improve/              # self-review / improvement
├── scripts/
│   ├── transcribe.py                  # ffmpeg + whisper STT (Russian transcript only)
│   └── setup.ps1                       # one-time setup
├── docs/
│   ├── ru/                             # Russian transcripts
│   ├── tr/                             # Turkish translations
│   └── plans/                          # action plans (TR or RU)
└── requirements.txt
```

## Known risks / notes

- **No speaker diarization** (no "who spoke" labels). Can be added via the
  `self-improve` skill (pyannote-based diarization) if needed.
- **New GPU (Blackwell / RTX 5060):** if the CUDA/cuDNN layer stalls on the first
  try, the script falls back to CPU; the permanent fix is up-to-date CUDA
  libraries in setup.
- **Privacy:** everything runs locally, recordings never leave the machine.

## Changelog

- Initial version: STT (faster-whisper) + Claude translation + summary, RU/TR
  separated archive.
- Added `meeting-plan` skill: after a translation, extracts an action plan
  (action items / decisions / open questions) from the RU transcript; asks the
  plan language (TR/RU, default TR); saves to `docs/plans/`. Turkish skill content.
