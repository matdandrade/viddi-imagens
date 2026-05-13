from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from app.config import USER_AGENT
from app.utils import clean_text


class BHImageScraper:
    def fetch_html(self, url: str) -> str:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,
                args=["--disable-blink-features=AutomationControlled"],
            )

            context = browser.new_context(
                user_agent=USER_AGENT,
                locale="pt-BR",
                viewport={"width": 1400, "height": 900},
            )

            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(3000)

            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except PlaywrightTimeoutError:
                pass

            page.wait_for_timeout(2000)
            html = page.content()
            browser.close()
            return html

    def parse_title(self, soup: BeautifulSoup) -> str:
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            title = clean_text(og_title["content"])
        elif soup.title:
            title = clean_text(soup.title.get_text(" ", strip=True))
        else:
            title = "produto"

        if " | B&H" in title:
            title = title.split(" | B&H", 1)[0].strip()

        return title

    def parse_images(self, soup: BeautifulSoup) -> list[str]:
        images = []
        seen = set()

        selectors = soup.select('[data-selenium="thumbnailImage"], img')

        for img in selectors:
            candidates = [
                img.get("src"),
                img.get("data-src"),
                img.get("data-lazy"),
            ]

            srcset = img.get("srcset")
            if srcset:
                for part in srcset.split(","):
                    piece = part.strip().split(" ")
                    if piece:
                        candidates.append(piece[0])

            for url in candidates:
                if not url:
                    continue

                url = url.strip()

                if url.startswith("//"):
                    url = "https:" + url
                elif url.startswith("/"):
                    url = "https://www.bhphotovideo.com" + url

                lower = url.lower()

                valid_pattern = any(token in lower for token in [
                    "multiple_images",
                    "smallimages",
                    "images500x500",
                    "images1000x1000",
                    "images1500x1500",
                    "images2500x2500",
                    "thumbnails",
                ])

                blocked_pattern = any(token in lower for token in [
                    ".svg",
                    ".gif",
                    "currencies",
                    "manufacturers",
                    "bat.bing.com",
                    "explora",
                    "cdn-cgi/image/fit=scale-down,width=100",
                ])

                if not valid_pattern or blocked_pattern:
                    continue

                if url not in seen:
                    seen.add(url)
                    images.append(url)

        return images[:30]

    def scrape(self, url: str) -> dict:
        html = self.fetch_html(url)
        soup = BeautifulSoup(html, "html.parser")

        title = self.parse_title(soup)
        images = self.parse_images(soup)

        return {
            "title": title,
            "images": images,
        }