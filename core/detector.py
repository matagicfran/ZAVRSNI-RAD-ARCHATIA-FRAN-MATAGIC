from pathlib import Path

from PIL import Image, ImageOps

from core.architecture_data import ARCHITECTURE_STYLES
from core.model_loader import ModelManager


class ArchitectureDetector:
    def __init__(self, model_manager=None):
        # Detector koristi već učitane modele ako postoje
        self.model_manager = model_manager or ModelManager()

    def detect(self, image_path, top_k=5):
        # Prepoznavanje arhitektonskog stila pomocu CLIP modela
        if not self.model_manager.clip_ready():
            self.model_manager.load_all()

        if not self.model_manager.clip_ready():
            raise RuntimeError("CLIP model nije učitan i detekcija se ne može pokrenuti.")

        image = self._load_image(image_path)
        prompts = []
        prompt_style_indexes = []
        for style_index, style in enumerate(ARCHITECTURE_STYLES):
            style_prompts = style.get("prompts", [style["prompt"]])
            prompts.extend(style_prompts)
            prompt_style_indexes.extend([style_index] * len(style_prompts))

        inputs = self.model_manager.clip_processor(
            text=prompts,
            images=image,
            return_tensors="pt",
            padding=True,
        )
        inputs = {
            key: value.to(self.model_manager.device)
            for key, value in inputs.items()
        }

        import torch

        with torch.no_grad():
            outputs = self.model_manager.clip_model(**inputs)
            prompt_logits = outputs.logits_per_image[0]

            style_logits = []
            for style_index in range(len(ARCHITECTURE_STYLES)):
                indexes = [
                    prompt_index
                    for prompt_index, mapped_style_index in enumerate(prompt_style_indexes)
                    if mapped_style_index == style_index
                ]
                style_logits.append(prompt_logits[indexes].mean())
            scores = torch.stack(style_logits).softmax(dim=0)

        return self._format_results(scores, top_k)

    def _load_image(self, image_path):
        # Učitavanje slike za model
        image = Image.open(Path(image_path))
        image = ImageOps.exif_transpose(image)
        return image.convert("RGB")

    def _format_results(self, scores, top_k):
        # Pretvaranje rezultata u čitljiv oblik
        count = min(top_k, len(ARCHITECTURE_STYLES))
        ranked_indexes = scores.argsort(descending=True)[:count]

        results = []
        for index in ranked_indexes:
            style = ARCHITECTURE_STYLES[int(index)]
            results.append(
                {
                    "style_id": style["id"],
                    "name": style["name"],
                    "confidence": float(scores[index]),
                    "period": style["period"],
                    "regions": style["regions"],
                    "features": style["features"],
                    "materials": style["materials"],
                    "prompt": style["prompt"],
                }
            )
        return results
