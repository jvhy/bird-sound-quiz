"""Unit tests for data importing from Xeno-Canto API."""

from model_bakery import baker
import pytest
import requests
import responses

from quiz.importers import xenocanto
from quiz.models import Species, Recording


def test_extract_license_type():
    license_url = "//creativecommons.org/licenses/by-nc-sa/4.0/"
    extracted_type = xenocanto.extract_license_type(license_url)

    assert extracted_type == "CC BY-NC-SA 4.0"


def test_extract_file_extension():
    file_name = "my_audio_file.mp3"
    extracted_extension = xenocanto.extract_file_extension(file_name)

    assert extracted_extension == ".mp3"


def test_construct_audio_url():
    recording = {
        "file-name": "XC123.mp3",
        "sono": {
            "small": "//xeno-canto.org/sounds/uploaded/ABCDEFGHIJ/ffts/XC123-small.png"
        }
    }
    audio_url = xenocanto.construct_audio_url(recording)

    assert audio_url == "https://xeno-canto.org/sounds/uploaded/ABCDEFGHIJ/XC123.mp3"


@responses.activate
def test_get_recordings_by_species_1():
    species = baker.prepare(Species, name_sci="Larus canus")

    url = "https://xeno-canto.org/api/3/recordings"
    api_key = "verysecretapikey"
    params = {
        "query": f'sp:"Larus canus" grp:birds q:A len:5-30',
        "key": api_key
    }

    responses.add(
        responses.GET,
        url=url,
        match=[
            responses.matchers.query_param_matcher(params)
        ],
        json={
            "numRecordings": "1",
            "numPages": 1,
            "results": [
                {"id": "123"}
            ]
        }
    )

    session = requests.Session()
    results = list(xenocanto.get_recordings_by_species(species=species, session=session, api_key=api_key))

    assert len(results) == 1  # one page
    assert len(results[0]["results"]) == 1  # one recording
    assert results[0]["results"][0]["id"] == "123"


@responses.activate
def test_get_recordings_by_species_2():
    """If there are no results when querying with scientific name, should try querying with English name instead."""
    species = baker.prepare(Species, name_sci="Larus canus", name_en="Common Gull")

    url = "https://xeno-canto.org/api/3/recordings"
    api_key = "verysecretapikey"

    params_sci = {
        "query": f'sp:"Larus canus" grp:birds q:A len:5-30',
        "key": api_key
    }
    responses.add(
        responses.GET,
        url=url,
        match=[
            responses.matchers.query_param_matcher(params_sci)
        ],
        json={
            "numRecordings": "0",  # no results when querying with name_sci
            "numPages": 1,
            "results": []
        }
    )

    params_en = {
        "query": f'en:"=Common Gull" grp:birds q:A len:5-30',
        "key": api_key
    }
    responses.add(
        responses.GET,
        url=url,
        match=[
            responses.matchers.query_param_matcher(params_en)
        ],
        json={
            "numRecordings": "1",  # one result with English name
            "numPages": 1,
            "results": [
                {"id": "123"}
            ]
        }
    )

    session = requests.Session()
    results = list(xenocanto.get_recordings_by_species(species=species, session=session, api_key=api_key))

    assert len(results) == 1  # one page
    assert len(results[0]["results"]) == 1  # one recording
    assert results[0]["results"][0]["id"] == "123"


@responses.activate
def test_get_recordings_by_species_3():
    """If there are multiple pages, all pages should be retrieved."""
    species = baker.prepare(Species, name_sci="Larus canus")

    url = "https://xeno-canto.org/api/3/recordings"
    api_key = "verysecretapikey"

    params = {
        "query": f'sp:"Larus canus" grp:birds q:A len:5-30',
        "key": api_key
    }

    # First page:
    responses.add(
        responses.GET,
        url=url,
        match=[
            responses.matchers.query_param_matcher(params)
        ],
        json={
            "numRecordings": "1",
            "numPages": 3,
            "results": [
                {"id": "123"}
            ]
        }
    )

    # Second page:
    responses.add(
        responses.GET,
        url=url,
        match=[
            responses.matchers.query_param_matcher({**params, "page": 2})
        ],
        json={
            "numRecordings": "1",
            "numPages": 3,
            "results": [
                {"id": "456"}
            ]
        }
    )

    # Third page:
    responses.add(
        responses.GET,
        url=url,
        match=[
            responses.matchers.query_param_matcher({**params, "page": 3})
        ],
        json={
            "numRecordings": "1",
            "numPages": 3,
            "results": [
                {"id": "789"}
            ]
        }
    )

    session = requests.Session()
    results = list(xenocanto.get_recordings_by_species(species=species, session=session, api_key=api_key))

    assert len(results) == 3  # three pages
    for page in results:
        assert len(page["results"]) == 1  # three recordings, one on each page


@pytest.mark.django_db
def test_convert_to_recording_1():
    species = baker.make(Species, name_sci="Larus canus")

    recording_obj = {
        "id": "123",
        "url": "//xeno-canto.org/123",
        "rec": "John Doe",
        "cnt": "Antarctica",
        "loc": "South Pole",
        "type": "call",
        "lic": "//creativecommons.org/licenses/by-nc-sa/4.0/",
        "file-name": "XC123.mp3",
        "sono": {
            "small": "//xeno-canto.org/sounds/uploaded/ABCDEFGHIJ/ffts/XC123-small.png"
        }
    }

    recording = xenocanto.convert_to_recording(recording_obj, species)

    assert type(recording) == Recording
    assert recording.audio == "audio/XC123.mp3"


@pytest.mark.django_db
def test_convert_to_recording_2():
    """Trying to convert an invalid recording object should return None."""
    species = baker.make(Species, name_sci="Larus canus")

    recording_obj = {
        "id": "123",
        "url": "//xeno-canto.org/123",
        "rec": "John Doe",
        "cnt": "Antartartartartartartartartartartartartartartarctica",  # country max. length is 50 characters
        "loc": "South Pole",
        "type": "call",
        "lic": "//creativecommons.org/licenses/by-nc-sa/4.0/",
        "file-name": "XC123.mp3",
        "sono": {
            "small": "//xeno-canto.org/sounds/uploaded/ABCDEFGHIJ/ffts/XC123-small.png"
        }
    }

    recording = xenocanto.convert_to_recording(recording_obj, species)

    assert recording is None
