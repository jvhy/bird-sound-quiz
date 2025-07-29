from collections import defaultdict
import random

from django.db.models.query import QuerySet

from quiz.models import Species, Recording, Region


def get_species_by_region(region_id: int, num_species: int) -> QuerySet[Species]:
    """
    Select n random species that have been observed in a region and have at least one recording.

    :param region_id: ID of the region that each selected species has to be observed in.
    :param num_species: Number of random species to be selected.
    :returns species_set: Query set of random species.
    """
    species_set = Species.objects.filter(
        observation__region_id=region_id,
        recording__isnull=False
    ).distinct().order_by("?")[:num_species]
    return species_set


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
