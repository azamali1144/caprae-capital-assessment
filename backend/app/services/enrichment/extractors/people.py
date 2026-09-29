import re

from app.services.enrichment.base import EnrichmentContext

DECISION_TITLES = (
    "owner",
    "co-owner",
    "founder",
    "co-founder",
    "ceo",
    "chief executive officer",
    "president",
    "managing director",
    "managing partner",
    "principal",
    "proprietor",
    "general manager",
)
OTHER_TITLES = ("vice president", "vp", "coo", "cfo", "cto", "director", "manager", "partner")

_TITLE = r"(?:co-)?(?:founder|owner)(?:\s*(?:&|and|/)\s*(?:ceo|president|owner))?|" + "|".join(
    re.escape(t) for t in sorted(DECISION_TITLES + OTHER_TITLES, key=len, reverse=True)
)
# optional word in front of the title - "Office Manager", "Service Director"
_QUALIFIER = r"(?:[A-Z][a-z]+\s+)?"
# "John Smith" / "Mary-Ann O'Neil" / "J. R. Smith"
_NAME = r"[A-Z][a-zA-Z'\-]+(?:\s+[A-Z]\.?)?(?:\s+[A-Z][a-zA-Z'\-]+){1,2}"

# "John Smith, Owner" / "John Smith - Founder & CEO" / "John Smith (President)"
NAME_THEN_TITLE = re.compile(rf"({_NAME})\s*(?:,|-|–|\||\()\s*({_QUALIFIER}(?i:{_TITLE}))\b")
# "Owner: John Smith" / "Founder & CEO John Smith"
TITLE_THEN_NAME = re.compile(rf"\b({_QUALIFIER}(?i:{_TITLE}))\s*(?::|,|-|–)?\s+({_NAME})")

_STOPWORDS = {"Contact", "About", "Our", "The", "Meet", "Call", "Email", "Team", "Home", "Us"}
# nav/button words that look like names when capitalised ("Search Extended, Director")
_UI_WORDS = {
    "Search",
    "Extended",
    "Read",
    "More",
    "Learn",
    "Sign",
    "Login",
    "Log",
    "Get",
    "Started",
    "Free",
    "Book",
    "Demo",
    "Download",
    "News",
    "Blog",
    "Events",
    "Donate",
    "Board",
    "Directors",
    "Advisory",
    "Privacy",
    "Policy",
    "Terms",
    "Services",
    "Careers",
    "Menu",
    "View",
    "Latest",
    # function words that start marketing copy ("With Akron...", "You Can Rely...")
    "With",
    "You",
    "Your",
    "We",
    "Can",
    "Rely",
    "For",
    "And",
    "From",
    "Estimating",
}
_TITLE_WORDS = {w for t in DECISION_TITLES + OTHER_TITLES for w in t.split()}


def _looks_like_name_word(w: str) -> bool:
    if w in _STOPWORDS or w in _UI_WORDS or w.lower() in _TITLE_WORDS:
        return False
    # "LEED AP", "HVAC" - acronyms, not names (single initials like "J." are fine)
    return not (len(w) > 2 and w.isupper())


def _clean_name(name: str) -> str | None:
    words = name.split()
    # drop stray nav words that got glued to the front ("Meet John Smith")
    while words and words[0] in _STOPWORDS:
        words = words[1:]
    if len(words) < 2 or not all(_looks_like_name_word(w) for w in words):
        return None
    return " ".join(words)


def is_decision_maker(title: str) -> bool:
    t = title.lower()
    return any(k in t for k in DECISION_TITLES) and "assistant" not in t


def find_people(text: str) -> list[dict]:
    """Expects one text block per line - matching across <li>s glues names together."""
    people: dict[str, dict] = {}

    for line in text.splitlines():
        line = line.strip()
        if not line or len(line) > 200:
            continue
        for m in NAME_THEN_TITLE.finditer(line):
            name, title = _clean_name(m.group(1)), m.group(2)
            if name and name not in people:
                people[name] = {"full_name": name, "title": title.strip().title()}
        for m in TITLE_THEN_NAME.finditer(line):
            title, name = m.group(1), _clean_name(m.group(2))
            if name and name not in people:
                people[name] = {"full_name": name, "title": title.strip().title()}

    out = []
    for p in people.values():
        p["title"] = p["title"].replace("Ceo", "CEO").replace("Coo", "COO").replace("Cfo", "CFO")
        p["is_decision_maker"] = is_decision_maker(p["title"])
        out.append(p)
    # owners/founders first
    return sorted(out, key=lambda p: not p["is_decision_maker"])


class PeopleExtractor:
    name = "people"

    async def extract(self, ctx: EnrichmentContext) -> None:
        # about/team pages first, the homepage is mostly marketing copy
        pages = sorted(ctx.iter_pages(), key=lambda p: p.path == "/")
        people: list[dict] = []
        seen = set()
        for page in pages:
            body = page.tree.body
            lines = body.text(separator="\n", strip=True) if body else ""
            for p in find_people(lines):
                if p["full_name"] not in seen:
                    seen.add(p["full_name"])
                    people.append(p)
        ctx.result["people"] = people[:10]
