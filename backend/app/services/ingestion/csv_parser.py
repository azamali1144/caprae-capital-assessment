import csv
import io
from dataclasses import dataclass, field

from app.schemas.raw_lead import RawLead
from app.services.ingestion.column_mapper import map_columns

MAX_BYTES = 5 * 1024 * 1024
MAX_ROWS = 5000


class CsvImportError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class ParsedCsv:
    leads: list[RawLead]
    mapping: dict[str, str]
    unmapped: list[str]
    skipped_rows: int = 0
    warnings: list[str] = field(default_factory=list)


def _decode(data: bytes) -> str:
    # utf-8-sig eats the BOM excel likes to add; fall back to latin-1 for old exports
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("latin-1")


def parse_csv(data: bytes) -> ParsedCsv:
    if not data:
        raise CsvImportError("IMPORT_EMPTY_FILE", "The uploaded file is empty.")
    if len(data) > MAX_BYTES:
        raise CsvImportError("IMPORT_TOO_LARGE", "CSV is larger than 5 MB.")

    text = _decode(data)
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel

    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    headers = [h for h in (reader.fieldnames or []) if h]
    if not headers:
        raise CsvImportError("IMPORT_INVALID_CSV", "Couldn't find a header row.")

    mapping, unmapped = map_columns(headers)
    fields = set(mapping.values())
    if "domain" not in fields and "name" not in fields:
        raise CsvImportError(
            "IMPORT_INVALID_CSV", "Column 'domain'/'website' or 'company name' is required."
        )

    leads: list[RawLead] = []
    skipped = 0
    for i, row in enumerate(reader, start=2):  # row 1 is the header
        if len(leads) >= MAX_ROWS:
            raise CsvImportError("IMPORT_TOO_MANY_ROWS", f"Max {MAX_ROWS} rows per import.")
        values = {mapping[h]: row.get(h) for h in mapping}
        lead = RawLead(**values, row_number=i)
        if not lead.domain and not lead.name:
            skipped += 1
            continue
        leads.append(lead)

    parsed = ParsedCsv(leads=leads, mapping=mapping, unmapped=unmapped, skipped_rows=skipped)
    if skipped:
        parsed.warnings.append(f"{skipped} rows had no company name or website and were skipped.")
    return parsed


def parse_domain_list(domains: list[str]) -> list[RawLead]:
    """For the 'paste domains' flow - one domain/url per entry, blanks ignored."""
    leads = []
    for i, d in enumerate(domains, start=1):
        d = (d or "").strip()
        if d:
            leads.append(RawLead(domain=d, row_number=i))
    if len(leads) > MAX_ROWS:
        raise CsvImportError("IMPORT_TOO_MANY_ROWS", f"Max {MAX_ROWS} domains per import.")
    return leads
