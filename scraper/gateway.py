from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.request import Request, urlopen


class _TextHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[str] = []
        self._title: str = ""
        self._in_title = False

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[override]
        if tag in {"p", "div", "section", "article", "br", "li", "h1", "h2", "h3"}:
            self._chunks.append("\n")
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:  # type: ignore[override]
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:  # type: ignore[override]
        text = data.strip()
        if not text:
            return
        if self._in_title and not self._title:
            self._title = text
        self._chunks.append(text)

    def to_markdown(self) -> tuple[str, str]:
        title = self._title or "Untitled"
        lines = [line.strip() for line in "\n".join(self._chunks).splitlines() if line.strip()]
        body = "\n\n".join(lines)
        markdown = f"# {title}\n\n{body}" if body else f"# {title}"
        return title, markdown


@dataclass(slots=True)
class ScrapeResult:
    url: str
    title: str
    markdown: str


class ScraperGateway:
    def fetch_markdown(self, url: str, timeout_seconds: int = 15) -> ScrapeResult:
        request = Request(url=url, headers={"User-Agent": "Universe-648-Scraper/0.1"})
        with urlopen(request, timeout=timeout_seconds) as response:
            raw_bytes = response.read()
            encoding = response.headers.get_content_charset() or "utf-8"
            html = raw_bytes.decode(encoding, errors="replace")

        parser = _TextHTMLParser()
        parser.feed(html)
        title, markdown = parser.to_markdown()
        return ScrapeResult(url=url, title=title, markdown=markdown)
