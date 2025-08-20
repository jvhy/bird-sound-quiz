"""Command for populating the database"""

import pathlib

from django.conf import settings
from django.core.management.base import BaseCommand
from tqdm import tqdm

from quiz.importers.util import get_retry_request_session
from quiz.importers.xenocanto import get_recordings_by_species, convert_to_recording
from quiz.models import Recording, Species, Observation, Region


class Command(BaseCommand):
    help = "Populate recording database table"

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "-r", "--region",
            type=str,
            nargs="+",
            help="Include recordings of species observed in selected regions (multiple regions can be selected)"
        )
        group.add_argument(
            "-f", "--region-file",
            type=str,
            help="Path to a file containing regions (one per line)",
        )
        parser.add_argument(
            "-s", "--skip-existing",
            type=bool,
            default=True,
            help="Skip recordings of species that already have recordings in the database (default: %(default)s)"
        )

    def handle(self, *args, **kwargs):
        session = get_retry_request_session()
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
        observed_species_ids = Observation.objects.filter(region__in=regions).values_list("species", flat=True).distinct()
        observed_species = Species.objects.filter(id__in=observed_species_ids)
        if kwargs["skip_existing"]:
            observed_species = observed_species.filter(recording__isnull=True).distinct()
        for species in tqdm(observed_species):
            recording_pages = get_recordings_by_species(species=species, session=session, api_key=settings.XENOCANTO_API_KEY)
            for page in recording_pages:
                batch = page["recordings"]
                rec_objs = [convert_to_recording(rec, species) for rec in batch]
                valid_rec_objs = [obj for obj in rec_objs if obj is not None]
                Recording.objects.bulk_create(
                    valid_rec_objs,
                    ignore_conflicts=True  # silently ignores recordings already found in the db
                )

        self.stdout.write(
            self.style.SUCCESS('Successfully populated the recording table')
        )
