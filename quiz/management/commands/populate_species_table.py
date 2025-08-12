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
        parser.add_argument(
            "--locale", "-l",
            type=str,
            nargs="+",
            choices=[lang[0] for lang in settings.LANGUAGES],
            default=["en", "fi"],
            help="Which locale(s) to include for the common names of species. Multiple locales can be entered (default: %(default)s). Only applicable if using eBird as source."
        )

    def handle(self, *args, **kwargs):
        session = get_retry_request_session()
        match kwargs["source"]:
            case "ebird":
                all_species_objs = []
                for locale in kwargs["locale"]:
                    species_list = ebird.get_species_info(session, settings.EBIRD_API_KEY, locale)
                    all_species_objs.extend([ebird.convert_to_species(species, locale) for species in species_list])
                merged_species = {}
                for sp in all_species_objs:
                    if sp.code not in merged_species:
                        merged_species[sp.code] = sp
                    else:
                        target = merged_species[sp.code]
                        # Merge localized name fields
                        for field in sp._meta.fields:
                            if field.name.startswith("name_") and getattr(sp, field.name):
                                setattr(target, field.name, getattr(sp, field.name))
                species_objs = merged_species.values()
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
            defaults={
                "order": species.order,
                "family": species.family,
                "genus": species.genus,
                "code": species.code,
            }

            if species.name_en is not None:
                defaults["name_en"] = species.name_en
            if species.name_fi is not None:
                defaults["name_fi"] = species.name_fi

            Species.objects.update_or_create(
                name_sci=species.name_sci,
                defaults=defaults
            )
        self.stdout.write(
            self.style.SUCCESS('Successfully populated the species table')
        )
