"""Command for populating the database"""

from django.conf import settings
from django.core.management.base import BaseCommand

from quiz.importers.ebird import get_species_codes_by_region
from quiz.importers.util import get_retry_request_session
from quiz.models import Observation, Species, Region


class Command(BaseCommand):
    help = "Populate observation database table"

    def add_arguments(self, parser):
        parser.add_argument(
            "region",
            type=str,
            nargs="+",
            help="Regions to search observations from (multiple regions can be entered)"
        )

    def handle(self, *args, **kwargs):
        session = get_retry_request_session()
        species = Species.objects.all()
        regions = Region.objects.filter(code__in=kwargs["region"])
        for region in regions:
            observed_species_codes = get_species_codes_by_region(region.code, session, settings.EBIRD_API_KEY)
            observed_species = [sp for sp in species if sp.code in observed_species_codes]
            observations = [
                Observation(
                    species=sp,
                    region=region
                )
                for sp in observed_species
            ]
            Observation.objects.bulk_create(observations, ignore_conflicts=True)

        self.stdout.write(
            self.style.SUCCESS('Successfully populated the observation table')
        )
