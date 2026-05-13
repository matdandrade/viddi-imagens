import os
from pathlib import Path
from urllib.parse import urlparse

import requests
from PIL import Image

from app.config import RAW_DIR, USER_AGENT
from app.utils import reset_dir


class ImageDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Referer": "https://www.bhphotovideo.com/",
        })

    def _guess_extension(self, url: str, content_type: str) -> str:
        ext = os.path.splitext(urlparse(url).path)[1].lower()

        if ext in {".jpg", ".jpeg", ".png", ".webp"}:
            return ext

        content_type = (content_type or "").lower()

        if "jpeg" in content_type or "jpg" in content_type:
            return ".jpg"
        if "png" in content_type:
            return ".png"
        if "webp" in content_type:
            return ".webp"

        return ".jpg"

    def _normalize_url(self, url: str) -> str:
        marker = "/https://"
        if "cdn-cgi/image" in url and marker in url:
            url = "https://" + url.split(marker, 1)[1]

        if url.startswith("http://"):
            url = url.replace("http://", "https://", 1)

        return url

    def _upgrade_candidates(self, url: str) -> list[str]:
        url = self._normalize_url(url)
        candidates = []

        patterns = [
            ("thumbnails", "images2500x2500"),
            ("thumbnails", "images2000x2000"),
            ("thumbnails", "images1500x1500"),
            ("smallimages", "images2500x2500"),
            ("smallimages", "images2000x2000"),
            ("smallimages", "images1500x1500"),
            ("images500x500", "images2500x2500"),
            ("images500x500", "images2000x2000"),
            ("images500x500", "images1500x1500"),
            ("images1000x1000", "images2500x2500"),
            ("images1000x1000", "images2000x2000"),
            ("images1500x1500", "images2500x2500"),
        ]

        for old, new in patterns:
            if old in url:
                upgraded = url.replace(old, new)
                if upgraded not in candidates:
                    candidates.append(upgraded)

        if url not in candidates:
            candidates.append(url)

        return candidates

    def download_images(self, image_urls: list[str], folder_name: str) -> list[Path]:
        target_dir = RAW_DIR / folder_name
        reset_dir(target_dir)

        downloaded = []
        seen_final = set()

        for index, original_url in enumerate(image_urls, start=1):
            for candidate_url in self._upgrade_candidates(original_url):
                try:
                    response = self.session.get(candidate_url, timeout=30)
                    response.raise_for_status()

                    ext = self._guess_extension(
                        candidate_url,
                        response.headers.get("Content-Type", "")
                    )

                    file_path = target_dir / f"raw-{index:02d}{ext}"
                    file_path.write_bytes(response.content)

                    with Image.open(file_path) as img:
                        width, height = img.size

                    if width < 700 or height < 700:
                        file_path.unlink(missing_ok=True)
                        continue

                    fingerprint = f"{width}x{height}:{file_path.stat().st_size}"
                    if fingerprint in seen_final:
                        file_path.unlink(missing_ok=True)
                        break

                    seen_final.add(fingerprint)
                    downloaded.append(file_path)
                    break

                except Exception:
                    continue

        return downloaded