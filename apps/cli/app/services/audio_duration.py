from pathlib import Path
import wave


def measure_wav_duration_ms(audio_path: Path) -> int:
    path = Path(audio_path)
    try:
        with wave.open(str(path), "rb") as wav_file:
            frame_count = wav_file.getnframes()
            frame_rate = wav_file.getframerate()
    except (FileNotFoundError, wave.Error) as exc:
        raise ValueError(f"Unable to measure WAV duration for {path}: {exc}") from exc

    if frame_rate <= 0:
        raise ValueError(f"Unable to measure WAV duration for {path}: invalid frame rate")

    return max(1, round(frame_count * 1000 / frame_rate))
