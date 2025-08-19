from collections import defaultdict
from enum import Enum
import random

from django.db.models.query import QuerySet

from quiz.models import Species, Recording, Region


class SelectionMode(str, Enum):
    RANDOM = "random"
    TAXONOMIC = "taxonomic"


def get_species_by_region(region_id: int) -> QuerySet[Species]:
    """
    Select species that have been observed in a region and have at least one recording.

    :param region_id: ID of the region that each selected species has to be observed in.
    :returns: Query set of species from given region.
    """
    region_species = Species.objects.filter(
        observation__region_id=region_id,
        recording__isnull=False
    ).distinct()
    return region_species


def get_multiple_choices(
    target_species: Species,
    available_species: QuerySet[Species],
    num_choices: int = 3,
    mode: SelectionMode = "random"
) -> list[str]:
    """
    Select n species to be used for multiple choice questions for a given species.

    :param target_species: Species for which choices are selected.
    :param available_species: Query set of species from which choices are selected.
    :param num_choices: How many choices to select.
    :param mode: How to select choice species: 
        "random" -> select randomly
        "taxonomic" -> select from species taxonomically close to the target species
    :return choice_species_names: List of choice species names in a random order (target species included)
    """
    match mode:
        case "random":
            choice_species_names = list(
                available_species
                    .exclude(id=target_species.id)
                    .order_by("?")
                    .values_list("name", flat=True)
                )[:num_choices]
        case "taxonomic":
            # TODO: Add taxonomic choice selection
            raise NotImplementedError("To be added")
        case _:
            raise ValueError('Unknown selection mode: mode should be one of {"random", "taxonomic"}')

    choice_species_names.append(target_species.name)
    random.shuffle(choice_species_names)
    return choice_species_names


def get_quiz_recordings(species_set: QuerySet[Species]) -> QuerySet[Recording]:
    """
    Select recordings to be used in a quiz based on a set of species.
    One recording per species is selected.

    :param species_set: Query set of unique species.
    :return selected_recordings: Selected recording objects.
    """
    species_ids = [sp.id for sp in species_set]
    candidate_recordings = Recording.objects.filter(species_id__in=species_ids)

    recordings_by_species = defaultdict(list)
    for rec in candidate_recordings:
        recordings_by_species[rec.species.id].append(rec)

    selected_recordings = []
    for species in species_set:
        recs = recordings_by_species[species.id]
        selected_recordings.append(random.choice(recs))
    return selected_recordings


def get_available_regions() -> QuerySet[Region]:
    """List all regions in the database that appear in at least one observation."""
    regions = Region.objects.filter(observation__isnull=False).distinct().order_by("name")
    return regions
