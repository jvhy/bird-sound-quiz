from django.db import models


class Species(models.Model):
    name_en = models.CharField(max_length=50, verbose_name="English name")
    name_sci = models.CharField(max_length=50, unique=True, verbose_name="Scientific (latin) name")


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
