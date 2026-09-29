import pytest

from app.services.ingestion.column_mapper import map_columns
from app.services.ingestion.csv_parser import CsvImportError, parse_csv, parse_domain_list

SAASQUATCH_CSV = (
    "﻿Company Name,Website,Industry,Owner Name,Owner Title,Email,Phone,City,State,"
    "Country,Employees,Revenue,LinkedIn\n"
    "Acme HVAC LLC,https://www.acmehvac.com,HVAC,John Smith,Owner,john@acmehvac.com,"
    "(512) 555-0100,Austin,TX,US,25,$2.5M,https://linkedin.com/company/acme-hvac\n"
    "Cool Air Inc,coolair.com,HVAC,,,,,Dallas,TX,US,11-50,N/A,\n"
).encode()

GENERIC_CSV = b"name;url;sector;headcount\nBright Books;brightbooks.io;Accounting;8\n"


def test_map_columns_handles_synonyms_and_case():
    mapping, unmapped = map_columns(["Company Name", "WEBSITE", "e-mail", "Favourite Colour"])
    assert mapping == {"Company Name": "name", "WEBSITE": "domain", "e-mail": "email"}
    assert unmapped == ["Favourite Colour"]


def test_map_columns_first_header_wins():
    mapping, unmapped = map_columns(["Website", "URL"])
    assert mapping == {"Website": "domain"}
    assert unmapped == ["URL"]


def test_parse_saasquatch_export():
    parsed = parse_csv(SAASQUATCH_CSV)
    assert len(parsed.leads) == 2
    first, second = parsed.leads
    assert first.name == "Acme HVAC LLC"
    assert first.domain == "https://www.acmehvac.com"
    assert first.owner == "John Smith"
    assert first.title == "Owner"
    assert first.employees == 25
    assert first.revenue == 2_500_000
    assert second.employees == 11
    assert second.revenue is None
    assert second.email is None
    assert first.row_number == 2


def test_parse_generic_semicolon_csv():
    parsed = parse_csv(GENERIC_CSV)
    assert len(parsed.leads) == 1
    lead = parsed.leads[0]
    assert (lead.name, lead.domain, lead.industry, lead.employees) == (
        "Bright Books",
        "brightbooks.io",
        "Accounting",
        8,
    )


def test_rows_without_name_or_domain_are_skipped():
    parsed = parse_csv(b"company,website,city\nAcme,acme.com,Austin\n,,Dallas\n")
    assert len(parsed.leads) == 1
    assert parsed.skipped_rows == 1
    assert parsed.warnings


@pytest.mark.parametrize(
    "data, code",
    [
        (b"", "IMPORT_EMPTY_FILE"),
        (b"foo,bar\n1,2\n", "IMPORT_INVALID_CSV"),
        (b"x" * (5 * 1024 * 1024 + 1), "IMPORT_TOO_LARGE"),
    ],
    ids=["empty", "no-usable-columns", "too-large"],
)
def test_bad_files_raise(data, code):
    with pytest.raises(CsvImportError) as err:
        parse_csv(data)
    assert err.value.code == code


def test_parse_domain_list_ignores_blanks():
    leads = parse_domain_list(["acme.com", "  ", "https://coolair.com/"])
    assert [lead.domain for lead in leads] == ["acme.com", "https://coolair.com/"]
