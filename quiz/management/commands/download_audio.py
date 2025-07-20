"""Commmand for downloading audio files of recordings"""

import os

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from tqdm import tqdm

from quiz.importers.xenocanto import download_audio
from quiz.importers.util import get_retry_request_session
from quiz.models import Recording


class Command(BaseCommand):
    help = "Download audio files of recordings from Xeno-Canto."

    def handle(self, *args, **kwargs):
        # TODO: multithreading
        session = get_retry_request_session()
        recordings = Recording.objects.all()
        for recording in tqdm(recordings):
            if os.path.exists(settings.MEDIA_ROOT / f"audio/{recording.audio.name}"):
               continue  # skip files that have already been downloaded
            try:
                audio = download_audio(recording, session)
            except Exception as e:
                self.stderr.write(f"Failed to download {recording.url} with error: {repr(e)}")
                continue
            recording.downloaded = True
            recording.save()
            recording.audio.save(recording.audio.name, ContentFile(audio), save=False)  # saving here would mess up audio.name
        self.stdout.write(
            self.style.SUCCESS('Finished downloading files.')
        )
        failed = Recording.objects.filter(downloaded=False)
        if failed:
            self.stdout.write(
                self.style.NOTICE(f"Download failed for {len(failed)} rows. Drop rows? (y/n) ")
            )
            while True:
                answer = input().lower()
                match answer:
                    case "y" | "yes":
                        dropped = failed.delete()[0]
                        self.stdout.write(self.style.NOTICE(f"Dropped {len(dropped)} rows."))
                        break
                    case "n" | "no":
                        break
                    case _:
                        self.stdout.write(
                            self.style.NOTICE("Please enter (y)es or (n)o")
                        )
        self.stdout.write(
            self.style.SUCCESS('Download process finished successfully.')
        )
