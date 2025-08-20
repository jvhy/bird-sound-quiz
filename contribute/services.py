from django.contrib.auth import get_user_model

from quiz.models import Region, Observation


User = get_user_model()

def get_observations_to_type_annotate(region: Region, user: User):
    observations = Observation.objects.select_related("species").filter(region=region, type__isnull=True).exclude(observationtypeannotation__user=user)
    return observations
