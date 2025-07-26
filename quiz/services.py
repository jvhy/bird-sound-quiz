from collections import defaultdict
import random

from quiz.models import Recording


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
