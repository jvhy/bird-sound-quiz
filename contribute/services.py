from quiz.models import Region, Observation


def get_observations_to_type_annotate(region: Region):
    observations = Observation.objects.filter(region=region, type__isnull=True)
    return observations
