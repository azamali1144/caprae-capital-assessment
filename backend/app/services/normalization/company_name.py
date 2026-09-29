import re
import unicodedata

# legal suffixes that don't help tell companies apart
SUFFIXES = {
    "inc",
    "incorporated",
    "llc",
    "ltd",
    "limited",
    "co",
    "company",
    "corp",
    "corporation",
    "pvt",
    "plc",
    "gmbh",
    "lp",
    "llp",
    "pllc",
    "pc",
    "sa",
    "ag",
    "bv",
}

_PUNCT_RE = re.compile(r"[^\w\s&]")
_SPACE_RE = re.compile(r"\s+")


def normalize_company_name(name: str | None) -> str:
    """'ACME, Inc.' -> 'acme'. Used for fuzzy dedup, not for display."""
    if not name:
        return ""
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    text = text.lower().replace("&", " and ")
    text = _PUNCT_RE.sub(" ", text)
    text = _SPACE_RE.sub(" ", text).strip()

    words = text.split(" ")
    # drop suffixes from the end only, "co" in the middle can be real ("co op")
    while len(words) > 1 and words[-1] in SUFFIXES:
        words.pop()
    if len(words) > 2 and " ".join(words[-3:]) == "l l c":
        words = words[:-3]
    if words and words[0] == "the" and len(words) > 1:
        words = words[1:]
    return " ".join(words)


def clean_display_name(name: str | None) -> str:
    """Light tidy for showing in the UI - keep casing, just trim the junk."""
    if not name:
        return ""
    return _SPACE_RE.sub(" ", name).strip(" ,.-")
