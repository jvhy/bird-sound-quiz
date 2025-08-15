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


@pytest.mark.django_db
def test_get_quiz_recordings_1():
    """Selection of quiz recordings should be random."""
    species_set = baker.make(Species, _quantity=10, _fill_optional=True)
    for species in species_set:
        baker.make(Recording, species=species, _quantity=10, _create_files=True)

    selected_recordings_1 = services.get_quiz_recordings(species_set)
    selected_recordings_2 = services.get_quiz_recordings(species_set)

    assert {rec.id for rec in selected_recordings_1} != {rec.id for rec in selected_recordings_2}


@pytest.mark.django_db
def test_get_quiz_recordings_2():
    """Recordings selected for a quiz should include one recording per species."""
    species_set = baker.make(Species, _quantity=10, _fill_optional=True)
    for species in species_set:
        baker.make(Recording, species=species, _quantity=10, _create_files=True)

    selected_recordings = services.get_quiz_recordings(species_set)

    assert len(selected_recordings) == 10  # there is the correct number of recordings (1 per species)
    assert len({rec.species.id for rec in selected_recordings}) == 10  # species ids are unique


@pytest.mark.django_db
def test_get_multiple_choices_1():
    """There should be the correct number of multiple choice species and they should include the target species."""
    target_species = baker.make(Species, _fill_optional=True)
    available_species = baker.make(Species, _quantity=9, _fill_optional=True)
    available_species.append(target_species)
    available_species_qs = Species.objects.filter(id__in=[sp.id for sp in available_species])

    multiple_choice_species = services.get_multiple_choices(
        target_species=target_species,
        available_species=available_species_qs,
        locale="en",
        num_choices=3,
        mode="random"
    )

    assert target_species.name_en in multiple_choice_species
    assert len(multiple_choice_species) == 4  # num_choices + target_species


@pytest.mark.django_db
def test_get_multiple_choices_2():
    """Multiple choice species should be randomly selected."""
    target_species = baker.make(Species, _fill_optional=True)
    available_species = baker.make(Species, _quantity=99, _fill_optional=True)
    available_species.append(target_species)
    available_species_qs = Species.objects.filter(id__in=[sp.id for sp in available_species])

    multiple_choice_species_1 = services.get_multiple_choices(
        target_species=target_species,
        available_species=available_species_qs,
        locale="en",
        num_choices=9,
        mode="random"
    )

    multiple_choice_species_2 = services.get_multiple_choices(
        target_species=target_species,
        available_species=available_species_qs,
        locale="en",
        num_choices=9,
        mode="random"
    )

    assert multiple_choice_species_1 != multiple_choice_species_2


@pytest.mark.django_db
def test_get_multiple_choices_3():
    """Multiple choices should be randomly ordered."""
    target_species = baker.make(Species, _fill_optional=True)
    available_species = baker.make(Species, _quantity=9, _fill_optional=True)
    available_species.append(target_species)
    available_species_qs = Species.objects.filter(id__in=[sp.id for sp in available_species])

    multiple_choice_species_1 = services.get_multiple_choices(
        target_species=target_species,
        available_species=available_species_qs,
        locale="en",
        num_choices=9,
        mode="random"
    )

    multiple_choice_species_2 = services.get_multiple_choices(
        target_species=target_species,
        available_species=available_species_qs,
        locale="en",
        num_choices=9,
        mode="random"
    )

    assert len(multiple_choice_species_1) == len(multiple_choice_species_2) == 10
    assert set(multiple_choice_species_1) == set(multiple_choice_species_2)  # species should be the same...
    assert multiple_choice_species_1 != multiple_choice_species_2  # ... but order should be different


@pytest.mark.django_db
def test_get_multiple_choices_4():
    """Multiple choice species names should use English name as fallback if name in specified locale is unavailable."""
    target_species = baker.make(Species, name_en="Fallback name 1", name_fi=None)
    species_no_fi_name = baker.make(Species, name_en="Fallback name 2", name_fi=None)
    species_with_fi_name_1 = baker.make(Species, name_fi="Finnish name 1")
    species_with_fi_name_2 = baker.make(Species, name_fi="Finnish name 2")

    available_species = [target_species, species_no_fi_name, species_with_fi_name_1, species_with_fi_name_2]
    available_species_qs = Species.objects.filter(id__in=[sp.id for sp in available_species])

    multiple_choice_species = services.get_multiple_choices(
        target_species=target_species,
        available_species=available_species_qs,
        locale="fi",  # if not available, should fallback to English name
        num_choices=3,
        mode="random"
    )

    assert set(multiple_choice_species) == {"Fallback name 1", "Fallback name 2", "Finnish name 1", "Finnish name 2"}
