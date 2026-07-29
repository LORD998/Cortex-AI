"""Descarrega os modelos de voz neural usados pela Cortex.

Pode ser executado novamente: ficheiros completos são ignorados e downloads
interrompidos ficam com a extensão .part.
"""

from pathlib import Path
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DESTINATION = PROJECT_ROOT / "assets" / "tts"

ASSETS = (
    (
        "pt_PT-tugao-medium.onnx",
        "https://huggingface.co/rhasspy/piper-voices/resolve/main/"
        "pt/pt_PT/tug%C3%A3o/medium/pt_PT-tug%C3%A3o-medium.onnx?download=true",
        63_201_294,
    ),
    (
        "pt_PT-tugao-medium.onnx.json",
        "https://huggingface.co/rhasspy/piper-voices/resolve/main/"
        "pt/pt_PT/tug%C3%A3o/medium/pt_PT-tug%C3%A3o-medium.onnx.json?download=true",
        5_026,
    ),
    (
        "kokoro-v1.0.int8.onnx",
        "https://github.com/thewh1teagle/kokoro-onnx/releases/download/"
        "model-files-v1.0/kokoro-v1.0.int8.onnx",
        92_361_271,
    ),
    (
        "voices-v1.0.bin",
        "https://github.com/thewh1teagle/kokoro-onnx/releases/download/"
        "model-files-v1.0/voices-v1.0.bin",
        28_214_398,
    ),
)


def download(name: str, url: str, expected_size: int) -> None:
    destination = DESTINATION / name
    if destination.is_file() and destination.stat().st_size == expected_size:
        print(f"[já existe] {name}")
        return

    partial = destination.with_suffix(destination.suffix + ".part")
    request = Request(url, headers={"User-Agent": "Cortex-local-voice/1.0"})
    print(f"[download] {name}")
    with urlopen(request, timeout=60) as response, partial.open("wb") as output:
        total = int(response.headers.get("Content-Length", expected_size))
        copied = 0
        while True:
            block = response.read(1024 * 1024)
            if not block:
                break
            output.write(block)
            copied += len(block)
            print(
                f"\r  {copied / 1_048_576:.1f} / {total / 1_048_576:.1f} MB",
                end="",
                flush=True,
            )
    print()

    actual_size = partial.stat().st_size
    if actual_size != expected_size:
        raise RuntimeError(
            f"{name}: esperado {expected_size} bytes, recebido {actual_size}."
        )
    partial.replace(destination)


def main() -> None:
    DESTINATION.mkdir(parents=True, exist_ok=True)
    for asset in ASSETS:
        download(*asset)
    print("Voz local pronta.")


if __name__ == "__main__":
    main()
