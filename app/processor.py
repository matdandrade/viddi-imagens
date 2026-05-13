from pathlib import Path

from PIL import Image

from app.config import (
    PROCESSED_DIR,
    FINAL_IMAGE_SIZE,
    FINAL_IMAGE_BG,
    FINAL_IMAGE_FORMAT,
    FINAL_IMAGE_QUALITY,
    FINAL_MARGIN_PERCENT,
)
from app.utils import reset_dir


class ImageProcessor:
    def process_images(self, image_paths: list[Path], folder_name: str) -> list[Path]:
        target_dir = PROCESSED_DIR / folder_name
        reset_dir(target_dir)

        processed = []

        canvas_width, canvas_height = FINAL_IMAGE_SIZE
        usable_width = int(canvas_width * (1 - FINAL_MARGIN_PERCENT * 2))
        usable_height = int(canvas_height * (1 - FINAL_MARGIN_PERCENT * 2))

        for index, path in enumerate(image_paths, start=1):
            try:
                with Image.open(path) as img:
                    img = img.convert("RGB")

                    original_width, original_height = img.size
                    scale = min(
                        usable_width / original_width,
                        usable_height / original_height
                    )

                    new_width = max(1, int(original_width * scale))
                    new_height = max(1, int(original_height * scale))

                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

                    canvas = Image.new("RGB", FINAL_IMAGE_SIZE, FINAL_IMAGE_BG)
                    x = (canvas_width - new_width) // 2
                    y = (canvas_height - new_height) // 2
                    canvas.paste(img, (x, y))

                    output_path = target_dir / f"produto-{index:02d}.jpg"
                    canvas.save(
                        output_path,
                        FINAL_IMAGE_FORMAT,
                        quality=FINAL_IMAGE_QUALITY,
                        optimize=True,
                    )
                    processed.append(output_path)

            except Exception:
                continue

        return processed