from django.conf import settings
from django.core.management.base import BaseCommand

from quiz.importers.ebird import get_regions, convert_to_region
from quiz.importers.util import get_retry_request_session
from quiz.models import Region


class Command(BaseCommand):
    help = "Populate region database table"

    def add_arguments(self, parser):
        parser.add_argument(
            "-p", "--parent-region",
            type=str,
            default="world",
            help='Add subregions from specified parent region. For example, to add all US states to the region table, use set value to "US". By default, adds countries (default parent: "%(default)s").'
        )

    def handle(self, *args, **kwargs):
        session = get_retry_request_session()
        if kwargs["parent_region"] == "world":
            parent_region = None
        else:
            parent_region = Region.objects.filter(code=kwargs["parent_region"]).first()
            if not parent_region:
                self.stderr.write(
                    f'Parent region not found in region table. Please run this command with higher level parent region first.'
                )
                return
        regions = get_regions(session, settings.EBIRD_API_KEY, kwargs["parent_region"])
        region_objs = [convert_to_region(region, parent_region) for region in regions]
        valid_region_objs = [obj for obj in region_objs if obj is not None]
        if len(region_objs) > len(valid_region_objs):
            self.stdout.write(
                self.style.WARNING(f"Validation failed for {len(region_objs) - len(valid_region_objs)} regions. Omitting failed regions.")
            )
        for region in valid_region_objs:
            Region.objects.update_or_create(
                code=region.code,
                defaults={
                    "name": region.name,
                    "parent_region": region.parent_region
                }
            )
        self.stdout.write(
            self.style.SUCCESS('Successfully populated the region table')
        )
