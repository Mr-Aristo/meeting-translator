#!/usr/bin/env python
"""Meeting Translator — STT step.

Produces a Russian transcript from a video/audio file (faster-whisper + ffmpeg).
The translation step is done by Claude; this script ONLY does speech-to-text.

Usage:
    python transcribe.py <video-path> --out docs/ru/<name>_RU.md
"""
import sys
import os
import subprocess
import tempfile
import argparse
import datetime

# Use the repo-local model cache (.models) so the agent is self-contained and does
# not depend on an ambient HF_HOME being set on the machine. HuggingFace stores
# models under <HF_HOME>/hub, which is exactly the layout already in .models/.
# setdefault: an explicitly-set HF_HOME still wins, otherwise we point at .models.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("HF_HOME", os.path.join(_ROOT, ".models"))


def fmt_ts(seconds: float) -> str:
    """Format seconds as H:MM:SS."""
    return str(datetime.timedelta(seconds=int(seconds)))


def extract_audio(src: str, wav: str) -> None:
    """Extract 16kHz mono wav from video/audio via ffmpeg."""
    cmd = [
        "ffmpeg", "-y", "-i", src,
        "-vn", "-ac", "1", "-ar", "16000", "-f", "wav", wav,
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _register_cuda_dlls() -> None:
    """Make the pip-installed CUDA DLLs (nvidia-*-cu12) loadable on Windows.

    The wheels drop cublas/cudnn/nvrtc DLLs under site-packages/nvidia/*/bin.
    ctranslate2 loads them by name, so those dirs must be on the DLL search
    path; otherwise GPU encode fails with 'cublas64_12.dll is not found'.
    """
    if os.name != "nt":
        return
    import site
    roots = list(site.getsitepackages()) + [site.getusersitepackages()]
    for root in roots:
        nvidia = os.path.join(root, "nvidia")
        if not os.path.isdir(nvidia):
            continue
        for pkg in os.listdir(nvidia):
            bin_dir = os.path.join(nvidia, pkg, "bin")
            if os.path.isdir(bin_dir):
                os.add_dll_directory(bin_dir)
                os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")


def load_model(model_size: str):
    """Try GPU (float16) first, fall back to CPU (int8) on failure.

    On very new cards (e.g. RTX 5060 / Blackwell) the GPU layer can fail on the
    first attempt; in that case we silently fall back to CPU and print a warning.
    """
    _register_cuda_dlls()
    from faster_whisper import WhisperModel
    try:
        m = WhisperModel(model_size, device="cuda", compute_type="float16")
        return m, "cuda"
    except Exception as e:  # noqa: BLE001 - intentional broad catch for fallback
        print(f"[meeting-translator] GPU init failed ({e}); falling back to CPU (int8)...",
              file=sys.stderr)
        m = WhisperModel(model_size, device="cpu", compute_type="int8")
        return m, "cpu"


def main() -> int:
    ap = argparse.ArgumentParser(description="Meeting Translator STT (faster-whisper)")
    ap.add_argument("input", help="video or audio file path")
    ap.add_argument("--out", required=True, help="RU markdown output path")
    ap.add_argument("--model", default="large-v3", help="whisper model (default large-v3)")
    ap.add_argument("--language", default="ru", help="source language (default ru)")
    args = ap.parse_args()

    if not os.path.isfile(args.input):
        print(f"[meeting-translator] ERROR: file not found: {args.input}", file=sys.stderr)
        return 2

    model, device = load_model(args.model)
    print(f"[meeting-translator] device={device} model={args.model}", file=sys.stderr)

    with tempfile.TemporaryDirectory() as td:
        wav = os.path.join(td, "audio.wav")
        print("[meeting-translator] extracting audio (ffmpeg)...", file=sys.stderr)
        extract_audio(args.input, wav)

        print("[meeting-translator] transcription started...", file=sys.stderr)
        segments, info = model.transcribe(wav, language=args.language, vad_filter=True)

        out_dir = os.path.dirname(os.path.abspath(args.out))
        os.makedirs(out_dir, exist_ok=True)
        base = os.path.splitext(os.path.basename(args.input))[0]

        n = 0
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(f"# {base} — Russian transcript\n\n")
            f.write(f"- Source: `{args.input}`\n")
            f.write(f"- Model: {args.model} ({device})\n")
            f.write(f"- Language: {info.language} (probability {info.language_probability:.2f})\n\n")
            f.write("---\n\n")
            for seg in segments:
                ts = fmt_ts(seg.start)
                text = seg.text.strip()
                f.write(f"[{ts}] {text}\n")
                n += 1
                if n % 25 == 0:
                    print(f"[meeting-translator] {n} segments... ({ts})", file=sys.stderr)

    print(f"[meeting-translator] done -> {args.out} ({n} segments)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
