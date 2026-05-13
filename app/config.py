from pathlib import Path

APP_NAME = "Viddi Imagens"
BASE_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
LOGS_DIR = DATA_DIR / "logs"

FINAL_IMAGE_SIZE = (2000, 2000)
FINAL_IMAGE_BG = (255, 255, 255)
FINAL_IMAGE_FORMAT = "JPEG"
FINAL_IMAGE_QUALITY = 95
FINAL_MARGIN_PERCENT = 0.12

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

for folder in [DATA_DIR, RAW_DIR, PROCESSED_DIR, LOGS_DIR]:
    folder.mkdir(parents=True, exist_ok=True)