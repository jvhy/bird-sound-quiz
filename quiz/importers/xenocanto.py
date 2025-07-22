import re
import pathlib

from django.core.exceptions import ValidationError
import requests

from quiz.models import Recording, Species


def get_recordings_by_species(species: str, session: requests.Session, api_key: str):
    """
    Fetches metadata of bird call audio recordings for given species from Xeno-Canto API.
    Query filters used in API request:
        - species name
        - only match recordings of birds
        - minimum recording quality A (best quality)
        - lenght between 5 and 30 seconds

    :param species:  Scientific name of a bird species.
    :param session:  Request session.
    :param api_key:  Xeno-Canto API key.
    :return result:
    """
    url = "https://xeno-canto.org/api/3/recordings"
    params = {
        "query": f'sp:"{species}" grp:birds q:A len:5-30',
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


def convert_to_recording(recording: dict, species: Species) -> Recording | None:
    """
    Converts recording object in Xeno-Canto API schema to Recording database object and validates the fields.
    If field validation fails, returns None.

    :param recording: Recording object from Xeno-Canto API response.
    :param species: DB object of the bird species that appears in the recording.
    :return recording: Converted Recording db object or None if validation fails.
    """
    extension = extract_file_extension(recording["file-name"])
    file_name = f"audio/XC{recording["id"]}{extension}"
    recording_obj = Recording(
        id=recording["id"],
        species=species,
        url=recording["url"],
        recordist=recording["rec"],
        country=recording["cnt"],
        location=recording["loc"],
        sound_type=recording["type"],
        license=extract_license_type(recording["lic"]),
        audio=file_name
    )
    try:
        recording_obj.clean_fields()
    except ValidationError:
        return
    return recording_obj


def download_audio(recording: Recording, session: requests.Session) -> bytes:
    """
    Downloads an audio file of a recording object from Xeno-Canto.

    :param recording: Recording object for which an audio file is downloaded.
    :param session: Request session.
    :return audio: Audio file bytes.
    :raises: HTTPError if request fails.
    """
    download_url = "https:" + recording.url + "/download"
    response = session.get(download_url)
    response.raise_for_status()
    audio = response.content
    return audio
