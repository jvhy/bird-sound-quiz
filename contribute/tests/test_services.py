"""Unit tests for business logic"""

from django.contrib.auth import get_user_model
from model_bakery import baker
import pytest

from contribute import services, models
from quiz.models import Region, Species, Observation


User = get_user_model()

@pytest.mark.django_db
def test_get_observations_to_type_annotate_1():
    """Only observations from a given region should be included."""
    user = baker.make(User)

    target_region = baker.make(Region)
    other_region = baker.make(Region)

    species_in_region = baker.make(Species, _quantity=3)
    species_outside_region = baker.make(Species, _quantity=3)

    target_observations = []  # All of these should be in selected observations
    other_observations = []  # None of these should be in selected observations
    for sp in species_in_region:
        observation = baker.make(Observation, species=sp, region=target_region)
        target_observations.append(observation)
    for sp in species_outside_region:
        observation = baker.make(Observation, species=sp, region=other_region)
        other_observations.append(observation)

    selected_observations = services.get_observations_to_type_annotate(region=target_region, user=user)

    selected_observation_ids = {observation.id for observation in selected_observations}
    target_observation_ids = {t_observation.id for t_observation in target_observations}

    assert selected_observation_ids == target_observation_ids


@pytest.mark.django_db
def test_get_observations_to_type_annotate_2():
    """Observations that have already been annotated by the user shouldn't be included."""
    user = baker.make(User)

    region = baker.make(Region)

    annotated_species = baker.make(Species, _quantity=3)  # Observations of these species should NOT be included
    not_annotated_species = baker.make(Species, _quantity=3)  # Observations of these species should be included

    for sp in annotated_species:
        observation = baker.make(Observation, species=sp, region=region)
        baker.make(models.ObservationTypeAnnotation, user=user, observation=observation)
    for sp in not_annotated_species:
        baker.make(Observation, species=sp, region=region)

    selected_observations = services.get_observations_to_type_annotate(region=region, user=user)

    selected_observation_species_ids = {observation.species.id for observation in selected_observations}
    not_annotated_species_ids = {species.id for species in not_annotated_species}

    assert selected_observation_species_ids == not_annotated_species_ids
