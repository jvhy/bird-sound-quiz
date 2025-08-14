"""Unit tests for business logic"""

from model_bakery import baker
import pytest

from quiz.models import Region, Species, Observation
from quiz import services


@pytest.mark.django_db
def test_get_available_regions_1():
    """Available regions should include only regions that have observations."""
    region_1 = Region(
        code="AQ",
        name_en="Antarctica"
    )
    region_2 = Region(
        code="BB",
        name_en="Barbados"
    )
    region_3 = Region(
        code="CL",
        name_en="Chile"
    )
    region_4 = Region(
        code="DE",
        name_en="Denmark"
    )
    for region in [region_1, region_2, region_3, region_4]:
        region.save()

    baker.make(Species)
    baker.make(Observation, region=region_1)
    baker.make(Observation, region=region_2)
    # no observations for region 3
    baker.make(Observation, region=region_4)

    available_regions = services.get_available_regions(locale="en")

    assert len(available_regions) == 3
    assert [region.code for region in available_regions] == ["AQ", "BB", "DE"]  # ordered by English name


@pytest.mark.django_db
def test_get_available_regions_2():
    """Available regions should be ordered by name field that is determined by "locale" argument."""
    region_1 = baker.make(
        Region,
        name_en="Z Region",
        name_fi="A-Alue"
    )
    region_2 = baker.make(
        Region,
        name_en="Y Region",
        name_fi="B-Alue"
    )
    region_3 = baker.make(
        Region,
        name_en="Z Region",
        name_fi="C-Alue"
    )

    baker.make(Species)
    baker.make(Observation, region=region_1)
    baker.make(Observation, region=region_2)
    baker.make(Observation, region=region_3)

    available_regions = services.get_available_regions(locale="fi")

    assert len(available_regions) == 3
    assert [region.name_fi for region in available_regions] == ["A-Alue", "B-Alue", "C-Alue"]  # ordered by Finnish name, as specified by locale arg
