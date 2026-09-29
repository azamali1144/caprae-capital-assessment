from dataclasses import dataclass

import phonenumbers

from app.services.enrichment.extractors.phones import region_for


@dataclass
class PhoneCheck:
    raw: str
    e164: str | None
    valid: bool
    kind: str | None = None  # mobile | fixed_line | toll_free | voip | ...


_KINDS = {
    phonenumbers.PhoneNumberType.MOBILE: "mobile",
    phonenumbers.PhoneNumberType.FIXED_LINE: "fixed_line",
    phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: "fixed_line_or_mobile",
    phonenumbers.PhoneNumberType.TOLL_FREE: "toll_free",
    phonenumbers.PhoneNumberType.VOIP: "voip",
}


def check_phone(raw: str | None, country: str | None = None) -> PhoneCheck:
    raw = (raw or "").strip()
    if not raw:
        return PhoneCheck(raw=raw, e164=None, valid=False)
    try:
        num = phonenumbers.parse(raw, region_for(country))
    except phonenumbers.NumberParseException:
        return PhoneCheck(raw=raw, e164=None, valid=False)

    if not phonenumbers.is_valid_number(num):
        # "555-0100" would format as +15550100 which is just wrong - better to store nothing
        return PhoneCheck(raw=raw, e164=None, valid=False)

    return PhoneCheck(
        raw=raw,
        e164=phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.E164),
        valid=True,
        kind=_KINDS.get(phonenumbers.number_type(num)),
    )
