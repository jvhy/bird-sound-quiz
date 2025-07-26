"""Command for populating the database"""

from django.conf import settings
from django.core.management.base import BaseCommand
from tqdm import tqdm

from quiz.importers.lajifi import get_species_info, convert_to_species
from quiz.importers.xenocanto import get_recordings_by_species, convert_to_recording
from quiz.importers.util import get_retry_request_session
from quiz.models import Species, Recording


class Command(BaseCommand):
    help = "Populate species and recordings database tables"

    def handle(self, *args, **kwargs):
        session = get_retry_request_session()

        taxa = get_species_info(session, settings.LAJIFI_API_TOKEN)
        species_objs = [convert_to_species(taxon) for taxon in taxa]
        valid_species_objs = [obj for obj in species_objs if obj is not None]
        inserted_species_objs = Species.objects.bulk_create(
            valid_species_objs,
            update_conflicts=True,
            update_fields=["name_en", "name_sci"],
            unique_fields=["name_sci"]
        )
        for sp_obj in tqdm(inserted_species_objs):
            recording_pages = get_recordings_by_species(species=sp_obj, session=session, api_key=settings.XENOCANTO_API_KEY)
            for page in recording_pages:
                batch = page["recordings"]
                rec_objs = [convert_to_recording(rec, sp_obj) for rec in batch]
                valid_rec_objs = [obj for obj in rec_objs if obj is not None]
                inserted_species_objs = Recording.objects.bulk_create(
                    valid_rec_objs,
                    ignore_conflicts=True  # silently ignores recordings already found in the db
                )

        self.stdout.write(
            self.style.SUCCESS('Successfully populated the database')
        )
