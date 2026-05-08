import json
from pathlib import Path


HISTORY_FILE = Path("data") / "history" / "analysis_history.json"


def load_analysis_history():
    # Učitavanje lokalne povijesti analiza
    if not HISTORY_FILE.exists():
        return []

    try:
        with HISTORY_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError):
        return []

    if isinstance(data, list):
        return data
    return []


def save_analysis_history(history):
    # Spremanje lokalne povijesti analiza
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with HISTORY_FILE.open("w", encoding="utf-8") as file:
        json.dump(history, file, ensure_ascii=False, indent=2)


def clear_analysis_history():
    # Brisanje lokalne povijesti analiza
    if HISTORY_FILE.exists():
        HISTORY_FILE.unlink()


def shorten_filename(filename, max_length=18):
    # Skraćivanje naziva datoteke da ne širi GUI
    if len(filename) <= max_length:
        return filename
    return filename[: max_length - 3] + "..."
