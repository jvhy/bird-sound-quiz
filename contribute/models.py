from django.db import models
from django.contrib.auth import get_user_model

from quiz.models import Observation, OccurrenceType


User = get_user_model()

class ObservationTypeAnnotation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    observation = models.ForeignKey(Observation, on_delete=models.CASCADE)

    annotation = models.CharField(max_length=3, choices=OccurrenceType)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "observation"],
                name="unique_user_observation"
            )
        ]
