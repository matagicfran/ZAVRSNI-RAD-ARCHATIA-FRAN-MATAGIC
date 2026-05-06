from pathlib import Path

from PIL import Image, ImageOps


DEFAULT_OUTPUT_DIR = Path("data") / "processed"


def prepare_image(image_path, output_dir=DEFAULT_OUTPUT_DIR):
    # Priprema slike za kasniju analizu modelom
    source_path = Path(image_path)
    output_path = _build_output_path(source_path, output_dir)

    with Image.open(source_path) as image:
        # Ispravlja rotaciju slike ako spremi EXIF orijentaciju
        image = ImageOps.exif_transpose(image)
        original_size = image.size

        # Modelima je najcesce potreban RGB format
        image = image.convert("RGB")

        # Spremamo cijelu sliku bez rezanja i resizea
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path, format="JPEG", quality=95)

    return {
        "source_path": source_path,
        "processed_path": output_path,
        "original_size": original_size,
        "processed_size": original_size,
        "mode": "RGB",
    }


def _build_output_path(source_path, output_dir):
    # Naziv obradjene slike u posebnom folderu
    safe_name = source_path.stem.replace(" ", "_")
    return Path(output_dir) / f"{safe_name}_processed.jpg"


if __name__ == "__main__":
    # Kratka provjera iz terminala
    import sys

    if len(sys.argv) < 2:
        print("Koristenje: python -m core.image_processor putanja/do/slike.jpg")
        raise SystemExit(1)

    result = prepare_image(sys.argv[1])
    print(f"Obradena slika: {result['processed_path']}")
    print(f"Format: {result['mode']}")
    print(f"Velicina: {result['processed_size'][0]}x{result['processed_size'][1]}")
