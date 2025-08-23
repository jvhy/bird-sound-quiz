import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from accounts.models import User
from quiz.utils import create_region_display_name


class Species(models.Model):
    name = models.CharField(max_length=50, verbose_name="Localized common name")
    name_sci = models.CharField(max_length=50, unique=True, verbose_name="Scientific (latin) name")
    order = models.CharField(max_length=50, verbose_name="Taxonomic order", null=True, default=None)
    family = models.CharField(max_length=50, verbose_name="Taxonomic family", null=True, default=None)
    genus = models.CharField(max_length=50, verbose_name="Taxonomic genus", null=True, default=None)
    code = models.CharField(max_length=9, verbose_name="eBird species code", null=True, blank=True, default=None)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Species"
        verbose_name_plural = "Species"


class SoundType(models.TextChoices):
    SONG = "SNG", _("Song")
    CALL = "CAL", _("Call")
    ALARM = "ALR", _("Alarm call")
    FLIGHT = "FLG", _("Flight call")
    BEGGING = "BEG", _("Begging call")
    DUET = "DUE", _("Duet")
    ABERRANT = "ABR", _("Aberrant")
    IMITATION = "IMI", _("Imitation")
    DRUMMING = "DRU", _("Drumming")
    OTHER = "OTH", _("Other")


class Recording(models.Model):
    id = models.IntegerField(primary_key=True, verbose_name="Xeno-Canto ID")
    species = models.ForeignKey(Species, on_delete=models.CASCADE)
    url = models.CharField(max_length=50, unique=True, verbose_name="Xeno-Canto URL")
    xc_audio_url = models.CharField(max_length=255, verbose_name="Xeno-Canto audio file URL", null=True)
    recordist = models.CharField(max_length=100)
    country = models.CharField(max_length=50)
    location = models.CharField(max_length=255)
    sound_type = models.CharField(max_length=3, choices=SoundType, db_index=True)
    license = models.CharField(max_length=30, verbose_name="Creative Commons license type")
    license_url = models.CharField(max_length=255, verbose_name="Creative Commons license info URL", null=True)
    audio = models.FileField(upload_to="audio", max_length=255, unique=True)
    downloaded = models.BooleanField(verbose_name="Audio file downloaded", default=False)


class Region(models.Model):
    code = models.CharField(max_length=9, unique=True)
    name = models.CharField(max_length=100)
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
        return create_region_display_name(self)

    def __str__(self):
        return self.display_name


class OccurrenceType(models.TextChoices):
    REGULAR = "REG", _("Regular breeder")
    IRREGULAR = "IRR", _("Irregular breeder")
    WINTER = "WIN", _("Winter migrant")
    PASSAGE = "PAS", _("Passage migrant")
    VAGRANT = "VAG", _("Vagrant")
    ESCAPEE = "ESC", _("Escapee")


OCC_TYPE_DESCRIPTIONS = {
    OccurrenceType.REGULAR: _(
        "A species that breeds consistently in the region every year."
    ),
    OccurrenceType.IRREGULAR: _(
        "A species that breeds in the region only occasionally or under certain conditions."
    ),
    OccurrenceType.WINTER: _(
        "A species that migrates to and stays in the region during the non-breeding (winter) season."
    ),
    OccurrenceType.PASSAGE: _(
        "A species that passes through the region during migration but does not breed or overwinter there."
    ),
    OccurrenceType.VAGRANT: _(
        "A species found outside its normal range, typically due to unusual weather or navigation errors."
    ),
    OccurrenceType.ESCAPEE: _(
        "A non-native species that has escaped from captivity and appears in the wild."
    ),
}


class Observation(models.Model):
    species = models.ForeignKey(Species, on_delete=models.CASCADE)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    type = models.CharField(max_length=3, choices=OccurrenceType, null=True, default=None)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["species", "region"],
                name="unique_species_region"
            )
        ]

    def get_type_description(self):
        return self.OCC_TYPE_DESCRIPTIONS.get(self.type)


class Quiz(models.Model):
    class QuizMode(models.TextChoices):
        MULTI = "MULTI", _("Multiple choice")
        OPEN = "OPEN", _("Open answer")

    class QuizDifficulty(models.TextChoices):
        BEGINNER = ("BGN", _("Beginner / Easy difficulty"))
        NORMAL = ("NML", _("Normal / default difficulty"))

    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, default=None)
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True)
    difficulty = models.CharField(max_length=3, choices=QuizDifficulty)
    mode = models.CharField(max_length=8, choices=QuizMode)
    length = models.IntegerField()
    score = models.IntegerField()
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Quiz {self.id} by {self.user}"


class Answer(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="answers")
    recording = models.ForeignKey(Recording, on_delete=models.SET_NULL, null=True)
    user_answer = models.CharField(max_length=255)
    is_correct = models.BooleanField()

    def __str__(self):
        return f"Answer {self.id} in Quiz {self.quiz_id}"


class SpeciesListType(models.TextChoices):
    BEGINNER = ("BGN", _("List of easily recognizable species, used for regional beginner quizzes"))


class SpeciesList(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    name = models.CharField(max_length=50)
    description = models.TextField()
    type = models.CharField(max_length=3, choices=SpeciesListType, db_index=True, blank=True, null=True, default=None)
    regions = models.ManyToManyField(Region, blank=True)

    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="species_lists")
    is_official = models.BooleanField(default=False, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            # Lists created by same user must be uniquely named
            models.UniqueConstraint(
                fields=["created_by", "name"],
                name="unique_user_list_name"
            )
        ]


class ListSpecies(models.Model):
    species = models.ForeignKey(Species, on_delete=models.CASCADE)
    list = models.ForeignKey(SpeciesList, on_delete=models.CASCADE, related_name="species_entries")

    class Meta:
        constraints = [
            # species can only appear once in a given list
            models.UniqueConstraint(
                fields=["list", "species"],
                name="unique_species_per_list"
            )
        ]
