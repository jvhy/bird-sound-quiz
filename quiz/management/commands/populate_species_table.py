"""Command for populating the database"""

from django.conf import settings
from django.core.management.base import BaseCommand
from tqdm import tqdm

import quiz.importers.ebird as ebird
import quiz.importers.lajifi as lajifi
from quiz.importers.util import get_retry_request_session
from quiz.models import Species


class Command(BaseCommand):
    help = "Populate species database table"

    def add_arguments(self, parser):
        parser.add_argument(
            "--source", "-s",
            type=str,
            choices=["ebird", "laji.fi"],
            default="ebird",
            help="Which API to get species information from (default: %(default)s)"
        )

    def handle(self, *args, **kwargs):
        session = get_retry_request_session()
        match kwargs["source"]:
            case "ebird":
                species_list = ebird.get_species_info(session, settings.EBIRD_API_KEY)
                species_objs = [ebird.convert_to_species(species) for species in species_list]
            case "laji.fi":
                species_list = lajifi.get_species_info(session, settings.LAJIFI_API_KEY)
                species_objs = [lajifi.convert_to_species(species) for species in species_list]
            case _:
                raise ValueError("Invalid species info source")
        valid_species_objs = [obj for obj in species_objs if obj is not None]
        if len(species_objs) > len(valid_species_objs):
            self.stdout.write(
                self.style.WARNING(f"Validation failed for {len(species_objs) - len(valid_species_objs)} species. Omitting failed species.")
            )
        for species in tqdm(valid_species_objs):
            Species.objects.update_or_create(
                name_sci=species.name_sci,
                defaults={
                    "name_en": species.name_en,
                    "order": species.order,
                    "family": species.family,
                    "genus": species.genus,
                    "code": species.code,
                }
            )
        self.stdout.write(
            self.style.SUCCESS('Successfully populated the species table')
        )
