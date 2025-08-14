"""Unit tests for business logic"""

from model_bakery import baker
import pytest

from quiz.models import Region, Species, Observation, Recording
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


@pytest.mark.django_db
def test_get_species_by_region_1():
    """Species for a given region should only include species that have been observed in that region."""
    region = baker.make(Region)

    species_1 = baker.make(Species, name_en="Blue-footed Booby")
    species_2 = baker.make(Species, name_en="Tufted Titmouse")
    species_3 = baker.make(Species, name_en="Andean Cock-of-the-rock")

    baker.make(Observation, region=region, species=species_1)
    baker.make(Observation, region=region, species=species_2)
    # species 3 has no observations in the region

    # all species have a recording
    baker.make(Recording, species=species_1, _create_files=True)
    baker.make(Recording, species=species_2, _create_files=True)
    baker.make(Recording, species=species_3, _create_files=True)

    region_species = services.get_species_by_region(region.id)

    assert {species.name_en for species in region_species} == {"Blue-footed Booby", "Tufted Titmouse"}


@pytest.mark.django_db
def test_get_species_by_region_2():
    """Species for a given region should only include species that have at least one recording."""
    region = baker.make(Region)

    species_1 = baker.make(Species, name_en="Blue-footed Booby")
    species_2 = baker.make(Species, name_en="Tufted Titmouse")
    species_3 = baker.make(Species, name_en="Andean Cock-of-the-rock")

    # all species have observations in region
    baker.make(Observation, region=region, species=species_1)
    baker.make(Observation, region=region, species=species_2)
    baker.make(Observation, region=region, species=species_3)

    baker.make(Recording, species=species_1, _create_files=True)
    # no recording for species 2
    baker.make(Recording, species=species_3, _create_files=True)

    region_species = services.get_species_by_region(region.id)

    assert {species.name_en for species in region_species} == {"Blue-footed Booby", "Andean Cock-of-the-rock"}


@pytest.mark.django_db
def test_get_species_by_region_3():
    """Species for a given region should only be listed once, i.e. retuned species objects should be distinct."""
    region = baker.make(Region)

    species_1 = baker.make(Species, name_en="Blue-footed Booby")
    species_2 = baker.make(Species, name_en="Tufted Titmouse")
    species_3 = baker.make(Species, name_en="Andean Cock-of-the-rock")

    baker.make(Observation, region=region, species=species_1)
    baker.make(Observation, region=region, species=species_2)
    baker.make(Observation, region=region, species=species_3)

    baker.make(Recording, species=species_1, _create_files=True)
    baker.make(Recording, species=species_1, _create_files=True)  # species 1 has two recordings
    baker.make(Recording, species=species_2, _create_files=True)
    baker.make(Recording, species=species_3, _create_files=True)

    region_species = services.get_species_by_region(region.id)

    assert len(region_species) == 3


@pytest.mark.django_db
def test_get_species_by_region_4():
    """Species observed outside the specified region shouldn't show up in results."""
    target_region = baker.make(Region)
    irrelevant_region = baker.make(Region)

    species_1 = baker.make(Species, name_en="Blue-footed Booby")
    species_2 = baker.make(Species, name_en="Tufted Titmouse")
    species_3 = baker.make(Species, name_en="Andean Cock-of-the-rock")

    baker.make(Observation, region=irrelevant_region, species=species_1)  # shouldn't show up when querying species from target_region
    baker.make(Observation, region=target_region, species=species_2)
    baker.make(Observation, region=target_region, species=species_3)

    baker.make(Recording, species=species_1, _create_files=True)
    baker.make(Recording, species=species_2, _create_files=True)
    baker.make(Recording, species=species_3, _create_files=True)

    region_species = services.get_species_by_region(target_region.id)

    assert {species.name_en for species in region_species} == {"Tufted Titmouse", "Andean Cock-of-the-rock"}
