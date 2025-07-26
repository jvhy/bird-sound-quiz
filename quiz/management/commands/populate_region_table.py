from django.conf import settings
from django.core.management.base import BaseCommand

from quiz.importers.ebird import get_regions, convert_to_region
from quiz.importers.util import get_retry_request_session
from quiz.models import Region


class Command(BaseCommand):
    help = "Populate region database table"

    def handle(self, *args, **kwargs):
        session = get_retry_request_session()
        regions = get_regions(session, settings.EBIRD_API_KEY)
        region_objs = [convert_to_region(region) for region in regions]
        valid_region_objs = [obj for obj in region_objs if obj is not None]
        if len(region_objs) > len(valid_region_objs):
            self.style.WARNING(f"Validation failed for {len(region_objs) - len(valid_region_objs)} regions. Omitting failed regions.")

        Region.objects.bulk_create(
            valid_region_objs,
            update_conflicts=False
        )
        self.stdout.write(
            self.style.SUCCESS('Successfully populated the region table')
        )
