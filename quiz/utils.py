from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from quiz.models import Region


def create_region_display_name(region: "Region") -> str:
    """
    Create a display name for a region with the region name preceded by possible parent region(s) separated by hyphens.
    If region has no parent regions, return region name.

    :param region: Region for which a display name is created.
    :return display_name: Display name in the format {parent region 2} - {parent region 1} - {region}.
    """
    parent_region_1 = region.parent_region if region.parent_region else None
    parent_region_2 = parent_region_1.parent_region if parent_region_1 else None
    return " - ".join([reg.name for reg in [parent_region_2, parent_region_1, region] if reg])
