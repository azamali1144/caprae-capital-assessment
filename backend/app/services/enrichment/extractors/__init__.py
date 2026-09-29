from app.services.enrichment.extractors.emails import EmailExtractor
from app.services.enrichment.extractors.founded import FoundedExtractor
from app.services.enrichment.extractors.hiring import HiringExtractor
from app.services.enrichment.extractors.meta import MetaExtractor
from app.services.enrichment.extractors.people import PeopleExtractor
from app.services.enrichment.extractors.phones import PhoneExtractor
from app.services.enrichment.extractors.socials import SocialExtractor
from app.services.enrichment.extractors.tech_stack import TechStackExtractor


def default_extractors():
    return [
        MetaExtractor(),
        EmailExtractor(),
        PhoneExtractor(),
        SocialExtractor(),
        FoundedExtractor(),
        HiringExtractor(),
        TechStackExtractor(),
        PeopleExtractor(),
    ]
