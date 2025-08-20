"""Command for populating the database"""

import pathlib

from django.conf import settings
from django.core.management.base import BaseCommand

from quiz.importers.ebird import get_species_codes_by_region
from quiz.importers.util import get_retry_request_session
from quiz.models import Observation, Species, Region


class Command(BaseCommand):
    help = "Populate observation database table"

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "-r", "--region",
            type=str,
            nargs="+",
            help="Regions to search observations from (multiple regions can be entered)"
        )
        group.add_argument(
            "-f", "--region-file",
            type=str,
            help="Path to a file containing regions (one per line)",
        )

    def handle(self, *args, **kwargs):
        session = get_retry_request_session()
        species = Species.objects.all()
        region_provided = kwargs.get("region") or kwargs.get("region_file")
        if not region_provided:
            self.stdout.write(
                self.style.ERROR("No region(s) provided. Please provide region(s) with --region or --region-file options.")
            )
            return
        region_codes = kwargs.get("region")
        if not region_codes:
            region_file_path = pathlib.Path(kwargs["region_file"])
            if not region_file_path.exists():
                self.stdout.write(
                    self.style.ERROR("Region file doesn't exist. Please check the path.")
                )
                return
            with open(region_file_path, "r") as f_in:
                region_codes = [code.strip() for code in f_in.readlines() if code]
        regions = Region.objects.filter(code__in=region_codes)
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
