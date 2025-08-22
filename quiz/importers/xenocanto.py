from collections.abc import Iterator
import re
import pathlib

from django.core.exceptions import ValidationError
import requests

from quiz.models import Recording, SoundType, Species


SOUND_TYPE_MAPPING = {
    "song": SoundType.SONG,
    "dawn song": SoundType.SONG,
    "subsong": SoundType.SONG,
    "call": SoundType.CALL,
    "flight call": SoundType.FLIGHT,
    "nocturnal flight call": SoundType.FLIGHT,
    "alarm call": SoundType.ALARM,
    "begging call": SoundType.BEGGING,
    "duet": SoundType.DUET,
    "drumming": SoundType.DRUMMING,
    "drum": SoundType.DRUMMING,
    "aberrant": SoundType.ABERRANT,
    "imitation": SoundType.IMITATION
}


def get_recordings_by_species(species: Species, session: requests.Session, api_key: str) -> Iterator[dict]:
    """
    Fetches metadata of bird call audio recordings for given species from Xeno-Canto API.
    Query filters used in API request:
        - species name (scientific by default, English is used if that yields no results)
        - only match recordings of birds
        - minimum recording quality A (best quality)
        - length between 5 and 30 seconds

    :param species:  Species object with scientific and English names.
    :param session:  Request session.
    :param api_key:  Xeno-Canto API key.
    :return: Iterator that contains Xeno-Canto response dicts.
    """
    url = "https://xeno-canto.org/api/3/recordings"
    params = {
        "query": f'sp:"{species.name_sci}" grp:birds q:A len:5-30',
        "key": api_key
    }
    first_page = session.get(url, params=params).json()
    if first_page["numRecordings"] == "0":  # on empty result, try querying with English name
        params = {
            "query": f'en:"={species.name_en}" grp:birds q:A len:5-30',
            "key": api_key
        }
        first_page = session.get(url, params=params).json()
    yield first_page
    num_pages = first_page['numPages']
    for page in range(2, num_pages + 1):
        next_page = session.get(url, params={**params, 'page': page}).json()
        yield next_page


def extract_license_type(license_url: str) -> str:
    """
    Extracts a short license name from a Creative Commons license URL.

    :param license_url: URL of the CC license type page
    :return license_type: Name of the CC license type
    """
    match = re.match(r"//creativecommons.org/licenses/([a-z-]+)/(\d\.\d)/", license_url)
    license_type = f"CC {match.group(1).upper()} {match.group(2)}" if match else None
    return license_type


def extract_file_extension(file_name: str) -> str:
    """
    Extracts the file extension from a file name.

    :param file_name: Name of the file.
    :returns extension: Extracted file extension.
    """
    extension = pathlib.Path(file_name).suffix
    return extension


def construct_audio_url(recording: dict) -> str:
    """
    Constructs a URL to Xeno-Canto hosted audio file.

    :param recording: Recording object from Xeno-Canto API response.
    :returns audio_url: URL to audio file hosted by Xeno-Canto.
    """
    filename = recording["file-name"]
    sono_path = pathlib.Path(recording["sono"]["small"])
    audio_path_parent = str(sono_path.parents[1])
    audio_url = f"https:{audio_path_parent}/{filename}"
    return audio_url


def extract_primary_sound_type(sound_type: str) -> SoundType:
    """
    Extracts the primary sound type from a comma-separated list of sound types in a Xeno-Canto recoding object.

    :param sound_type: Comma-separated list of sound types.
    :returns primary_type: Extracted primary sound type.
    """
    primary_type_str = sound_type.split(",")[0]
    primary_type = SOUND_TYPE_MAPPING.get(primary_type_str, SoundType.OTHER)
    return primary_type


def convert_to_recording(recording_obj: dict, species: Species) -> Recording | None:
    """
    Converts recording object in Xeno-Canto API schema to Recording database object and validates the fields.
    If field validation fails, returns None.

    :param recording: Recording object from Xeno-Canto API response.
    :param species: DB object of the bird species that appears in the recording.
    :return recording: Converted Recording db object or None if validation fails.
    """
    extension = extract_file_extension(recording_obj["file-name"])
    file_name = f"audio/XC{recording_obj["id"]}{extension}"
    recording = Recording(
        id=recording_obj["id"],
        species=species,
        url=recording_obj["url"],
        xc_audio_url=construct_audio_url(recording_obj),
        recordist=recording_obj["rec"],
        country=recording_obj["cnt"],
        location=recording_obj["loc"],
        sound_type=extract_primary_sound_type(recording_obj["type"]),
        license=extract_license_type(recording_obj["lic"]),
        license_url=recording_obj["lic"],
        audio=file_name
    )
    try:
        recording.clean_fields()
    except ValidationError:
        return
    return recording


def download_audio(recording: Recording, session: requests.Session) -> bytes:
    """
    Downloads an audio file of a recording object from Xeno-Canto.

    :param recording: Recording object for which an audio file is downloaded.
    :param session: Request session.
    :return audio: Audio file bytes.
    :raises: HTTPError if request fails.
    """
    download_url = f"https:{recording.url}/download"
    response = session.get(download_url)
    response.raise_for_status()
    audio = response.content
    return audio
