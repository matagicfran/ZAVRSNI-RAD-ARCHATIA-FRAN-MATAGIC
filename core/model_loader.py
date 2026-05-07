import os
from dataclasses import dataclass
from pathlib import Path


MODEL_CACHE_DIR = Path("models") / "huggingface"
LOCAL_CLIP_DIR = Path("models") / "clip-vit-base-patch32"
CLIP_MODEL_NAME = "openai/clip-vit-base-patch32"


@dataclass
class ModelStatus:
    name: str
    loaded: bool
    message: str
    device: str = "cpu"


class ModelManager:
    def __init__(self, cache_dir=MODEL_CACHE_DIR, clip_model_name=CLIP_MODEL_NAME):
        # Centralno mjesto za sve lokalne AI modele
        self.cache_dir = Path(cache_dir)
        self.clip_model_name = clip_model_name
        self.device = "cpu"
        self.clip_model = None
        self.clip_processor = None
        self.statuses = []

    def load_all(self, progress_callback=None):
        # Automatsko učitavanje modela pri pokretanju aplikacije
        self._report_progress(progress_callback, 5)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("HF_HOME", str(self.cache_dir.resolve()))
        os.environ.setdefault("TRANSFORMERS_CACHE", str(self.cache_dir.resolve()))

        self.statuses = [self._load_clip(progress_callback)]
        if all(status.loaded for status in self.statuses):
            self._report_progress(progress_callback, 100)
        return self.statuses

    def _load_clip(self, progress_callback=None):
        # CLIP se koristi za usporedbu slike s tekstualnim opisima stilova
        try:
            import torch
            from transformers import CLIPModel, CLIPProcessor

            self._report_progress(progress_callback, 20)
            self.device = "cuda" if torch.cuda.is_available() else "cpu"

            if not self._local_clip_exists():
                self._report_progress(progress_callback, 30)
                download_clip_model(
                    cache_dir=self.cache_dir,
                    clip_model_name=self.clip_model_name,
                    progress_callback=progress_callback,
                )

            model_path = str(LOCAL_CLIP_DIR)

            self._report_progress(progress_callback, 45)
            self.clip_processor = CLIPProcessor.from_pretrained(
                model_path,
                local_files_only=True,
            )
            self._report_progress(progress_callback, 70)
            self.clip_model = CLIPModel.from_pretrained(
                model_path,
                local_files_only=True,
            ).to(self.device)
            self.clip_model.eval()
            self._report_progress(progress_callback, 95)

            return ModelStatus(
                name="CLIP",
                loaded=True,
                message="CLIP model je učitan lokalno.",
                device=self.device.upper(),
            )
        except Exception as error:
            self._report_progress(progress_callback, 100)
            return ModelStatus(
                name="CLIP",
                loaded=False,
                message=f"CLIP nije učitan: {error}",
                device=self.device.upper(),
            )

    def _report_progress(self, progress_callback, value):
        # Slanje postotka učitavanja prema GUI-u
        if progress_callback:
            progress_callback(value)

    def _resolve_clip_path(self):
        # Ako korisnik ručno spremi model u models folder, koristi se ta putanja
        if LOCAL_CLIP_DIR.exists():
            return str(LOCAL_CLIP_DIR)
        return self.clip_model_name

    def _local_clip_exists(self):
        # Provjera jesu li najvažnije datoteke modela već spremljene lokalno
        if not LOCAL_CLIP_DIR.exists():
            return False

        has_config = (LOCAL_CLIP_DIR / "config.json").exists()
        has_model = (
            (LOCAL_CLIP_DIR / "model.safetensors").exists()
            or (LOCAL_CLIP_DIR / "pytorch_model.bin").exists()
        )
        has_processor = (
            (LOCAL_CLIP_DIR / "preprocessor_config.json").exists()
            and (LOCAL_CLIP_DIR / "tokenizer_config.json").exists()
        )
        return has_config and has_model and has_processor

    def clip_ready(self):
        # Provjera je li CLIP spreman za detekciju
        return self.clip_model is not None and self.clip_processor is not None

    def status_text(self):
        # Kratki tekst za status u GUI-u
        if not self.statuses:
            return "Modeli: nisu učitani"

        loaded_count = sum(1 for status in self.statuses if status.loaded)
        total_count = len(self.statuses)
        details = ", ".join(
            f"{status.name} {'OK' if status.loaded else 'nije učitan'}"
            for status in self.statuses
        )
        return f"Modeli: {loaded_count}/{total_count} učitano ({details})"


def download_clip_model(
    cache_dir=MODEL_CACHE_DIR,
    clip_model_name=CLIP_MODEL_NAME,
    progress_callback=None,
):
    # Jednokratno preuzimanje besplatnog CLIP modela u models folder
    from transformers import CLIPModel, CLIPProcessor

    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    LOCAL_CLIP_DIR.mkdir(parents=True, exist_ok=True)

    _report_download_progress(progress_callback, 35)
    processor = CLIPProcessor.from_pretrained(
        clip_model_name,
        cache_dir=str(cache_dir),
        local_files_only=False,
    )
    _report_download_progress(progress_callback, 55)
    model = CLIPModel.from_pretrained(
        clip_model_name,
        cache_dir=str(cache_dir),
        local_files_only=False,
    )

    _report_download_progress(progress_callback, 80)
    processor.save_pretrained(LOCAL_CLIP_DIR)
    model.save_pretrained(LOCAL_CLIP_DIR)
    _report_download_progress(progress_callback, 90)
    return LOCAL_CLIP_DIR


def _report_download_progress(progress_callback, value):
    # Progress kod prvog preuzimanja modela
    if progress_callback:
        progress_callback(value)


if __name__ == "__main__":
    # Kratka provjera i opcionalno preuzimanje modela
    import sys

    if "--download-clip" in sys.argv:
        path = download_clip_model()
        print(f"CLIP model je spremljen u: {path}")
    else:
        manager = ModelManager()
        manager.load_all()
        print(manager.status_text())
