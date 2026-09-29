from dataclasses import dataclass, field
from typing import Any, Protocol

from selectolax.parser import HTMLParser


@dataclass
class Page:
    path: str
    url: str
    html: str
    _tree: HTMLParser | None = None

    @property
    def tree(self) -> HTMLParser:
        # parse lazily, most extractors share the same tree
        if self._tree is None:
            self._tree = HTMLParser(self.html)
        return self._tree

    @property
    def text(self) -> str:
        body = self.tree.body
        return body.text(separator=" ", strip=True) if body else ""


@dataclass
class EnrichmentContext:
    domain: str
    country: str | None = None  # hint for phone parsing
    base_url: str | None = None
    pages: dict[str, Page] = field(default_factory=dict)

    # what the website fetch looked like - used later for site health
    site_status: str | None = None  # alive | dead | blocked | timeout
    has_ssl: bool = False
    http_status: int | None = None

    # extractors write into this; must stay json-friendly (it gets cached)
    result: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    @property
    def home(self) -> Page | None:
        return self.pages.get("/")

    def iter_pages(self):
        return self.pages.values()

    def all_text(self) -> str:
        return "\n".join(p.text for p in self.pages.values())


class Extractor(Protocol):
    name: str

    async def extract(self, ctx: EnrichmentContext) -> None: ...
