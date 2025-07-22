"""Commmand for downloading audio files of recordings"""

import os
from pathlib import Path

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
            audio_path = Path(settings.MEDIA_ROOT) / recording.audio.name
            if os.path.exists(audio_path):
                continue  # skip files that have already been downloaded
            try:
                audio = download_audio(recording, session)
            except Exception as e:
                self.stderr.write(f"Failed to download {recording.url} with error: {repr(e)}")
                continue
            filename = Path(recording.audio.name).name
            recording.audio.save(filename, ContentFile(audio), save=False)
            recording.downloaded = True
            recording.save()
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
                        dropped, _ = failed.delete()
                        self.stdout.write(self.style.NOTICE(f"Dropped {dropped} rows."))
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
