import random

from quiz.models import Recording


def get_quiz_recordings(n_species: int)  -> list[Recording]:
    """
    Select recordings to be used in a quiz. One recording per each of n species is selected.

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
