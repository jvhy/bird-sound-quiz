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


def get_quiz_recordings_postgres(n_species: int)  -> list[Recording]:
    """
    Select recordings to be used in a quiz. One recording per each of n species is selected.
    Uses DISTINCT ON which is only supported by postgres.

    :param n_species: How many species a recording is selected for.
    :returns recordings: Selected recording objects.
    """
    # NOTE: This function makes two SQL queries. Could be optimized with CTE, but it isn't natively supported by django.
    species_ids = Recording.objects.values_list('species_id', flat=True).distinct()
    random_species_ids = random.sample(list(species_ids), n_species)
    recordings = list(
        Recording.objects
        .filter(species_id__in=random_species_ids)
        .order_by('species_id', '?')
        .distinct('species_id')
        .select_related('species')
    )
    random.shuffle(recordings)
    return recordings


def get_quiz_recordings_mysql(n_species: int)  -> list[Recording]:
    """
    Select recordings to be used in a quiz. One recording per each of n species is selected.

    :param n_species: How many species a recording is selected for.
    :returns recordings: Selected recording objects.
    """
    species_ids = (
        Recording.objects
        .values_list('species_id', flat=True)
        .distinct()
    )
    random_species_ids = random.sample(list(species_ids), n_species)
    candidate_recordings = Recording.objects.filter(
        species_id__in=random_species_ids
    ).select_related('species')

    recordings_by_species = defaultdict(list)
    for rec in candidate_recordings:
        recordings_by_species[rec.species_id].append(rec)

    selected_recordings = [
        random.choice(recordings)
        for recordings in recordings_by_species.values()
    ]

    random.shuffle(selected_recordings)
    return selected_recordings


def get_available_regions() -> QuerySet[Region]:
    """List all regions in the database that appear in at least one observation."""
    regions = Region.objects.filter(observation__isnull=False).distinct().order_by("name")
    return regions
