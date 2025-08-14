import uuid

from django.db import models
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _

from accounts.models import User
from quiz.utils import create_region_display_name


class Species(models.Model):
    name_en = models.CharField(max_length=50, verbose_name="English name", blank=True, null=True)
    name_fi = models.CharField(max_length=50, verbose_name="Finnish name", blank=True, null=True)
    name_sci = models.CharField(max_length=50, unique=True, verbose_name="Scientific (latin) name")
    order = models.CharField(max_length=50, verbose_name="Taxonomic order", null=True, default=None)
    family = models.CharField(max_length=50, verbose_name="Taxonomic family", null=True, default=None)
    genus = models.CharField(max_length=50, verbose_name="Taxonomic genus", null=True, default=None)
    code = models.CharField(max_length=9, verbose_name="eBird species code", null=True, blank=True, default=None)


class Recording(models.Model):
    id = models.IntegerField(primary_key=True, verbose_name="Xeno-Canto ID")
    species = models.ForeignKey(Species, on_delete=models.CASCADE)
    url = models.CharField(max_length=50, unique=True, verbose_name="Xeno-Canto URL")
    xc_audio_url = models.CharField(max_length=255, verbose_name="Xeno-Canto audio file URL", null=True)
    recordist = models.CharField(max_length=100)
    country = models.CharField(max_length=50)
    location = models.CharField(max_length=255)
    sound_type = models.CharField(max_length=100, null=True)
    license = models.CharField(max_length=30, verbose_name="Creative Commons license type")
    license_url = models.CharField(max_length=255, verbose_name="Creative Commons license info URL", null=True)
    audio = models.FileField(upload_to="audio", max_length=255, unique=True)
    downloaded = models.BooleanField(verbose_name="Audio file downloaded", default=False)


class Region(models.Model):
    code = models.CharField(max_length=9, unique=True)
    name_en = models.CharField(max_length=100)
    name_fi = models.CharField(max_length=100, null=True, blank=True, default=None)
    parent_region = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        default=None,
        related_name='subregions'
    )

    @property
    def display_name(self):
        locale = get_language()
        return create_region_display_name(self, locale)

    def __str__(self):
        return self.display_name


class Observation(models.Model):
    species = models.ForeignKey(Species, on_delete=models.CASCADE)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["species", "region"],
                name="unique_species_region"
            )
        ]


class Quiz(models.Model):
    class QuizMode(models.TextChoices):
        MULTI = "MULTI", _("Multiple choice")
        OPEN = "OPEN", _("Open answer")

    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, default=None)
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True)
    mode = models.CharField(max_length=8, choices=QuizMode)
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(auto_now_add=True)

    @property
    def length(self) -> int:
        return self.answers.count()

    @property
    def score(self) -> int:
        return sum(ans.is_correct for ans in self.answers.all())

    def __str__(self):
        return f"Quiz {self.id} by {self.user}"


class Answer(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="answers")
    recording = models.ForeignKey(Recording, on_delete=models.SET_NULL, null=True)
    user_answer = models.CharField(max_length=255)

    @property
    def is_correct(self) -> bool:
        if not self.recording:
            return False
        # TODO: This should NOT rely on current locale
        lang = get_language()
        name_field = f"name_{lang}"
        fallback_field = "name_en"
        return (getattr(self.recording.species, name_field) or getattr(self.recording.species, fallback_field)).capitalize() == self.user_answer.strip().capitalize()

    def __str__(self):
        return f"Answer {self.id} in Quiz {self.quiz_id}"
