"""Unit tests for data importing from eBird API."""

from model_bakery import baker
import pytest
import requests
import responses

from quiz.importers import ebird
from quiz.models import Species, Region


def test_is_finnish_locale():
    finnish_name = "naurulokki"
    non_finnish_name = "Black-headed Gull"

    assert ebird.is_finnish_locale(finnish_name)
    assert not ebird.is_finnish_locale(non_finnish_name)


@responses.activate
def test_get_species_info_1():
    """eBird API call for species info should use the correct params and headers."""
    url = "https://api.ebird.org/v2/ref/taxonomy/ebird"
    params = {
        "cat": "species",
        "fmt": "json",
        "locale": "en"
    }
    api_key = "verysecretapikey"

    responses.add(
        responses.GET,
        url=url,
        json=[
            {
                "speciesCode": "whiwag",
                "comName": "White Wagtail",
                "sciName": "Motacilla alba",
                "order": "Passeriformes",
                "familySciName": "Motacillidae"
            }
        ],
        match=[
            responses.matchers.header_matcher({"X-eBirdApiToken": api_key}),
            responses.matchers.query_param_matcher(params)
        ]
    )

    session = requests.Session()
    results = ebird.get_species_info(session=session, api_key=api_key)

    assert len(results) == 1
    assert set(results[0].keys()) == {"speciesCode", "comName", "sciName", "order", "familySciName"}
    assert results[0]["speciesCode"] == "whiwag"


@responses.activate
def test_get_species_info_2():
    """Species info should be retrieved in the specified locale."""
    url = "https://api.ebird.org/v2/ref/taxonomy/ebird"
    api_key = "verysecretapikey"
    shared_params = {
        "cat": "species",
        "fmt": "json",
    }

    sp_obj = {  # missing locale-specific "comName" field
        "speciesCode": "whiwag",
        "sciName": "Motacilla alba",
        "order": "Passeriformes",
        "familySciName": "Motacillidae"
    }

    # Finnish response
    params_fi = {
        **shared_params,
        "locale": "fi"
    }
    responses.add(
        responses.GET,
        url=url,
        json=[
            {
                **sp_obj,
                "comName": "Västäräkki"
            }
        ],
        match=[
            responses.matchers.header_matcher({"X-eBirdApiToken": api_key}),
            responses.matchers.query_param_matcher(params_fi)
        ]
    )

    # English response, shouldn't be returned when "locale" == "fi"
    params_en = {
        **shared_params,
        "locale": "en"
    }
    responses.add(
        responses.GET,
        url=url,
        json=[
            {
                **sp_obj,
                "comName": "White Wagtail"
            }
        ],
        match=[
            responses.matchers.header_matcher({"X-eBirdApiToken": api_key}),
            responses.matchers.query_param_matcher(params_en)
        ]
    )

    session = requests.Session()
    results = ebird.get_species_info(session=session, api_key=api_key, locale="fi")

    assert len(results) == 1
    assert results[0]["comName"] == "Västäräkki"


def test_convert_to_species_1():
    sp_obj = {
        "speciesCode": "whiwag",
        "comName": "White Wagtail",
        "sciName": "Motacilla alba",
        "order": "Passeriformes",
        "familySciName": "Motacillidae"
    }

    species = ebird.convert_to_species(sp_obj)

    assert type(species) == Species
    assert species.name_en == "White Wagtail"
    assert species.name_fi is None
    assert species.name_sci == "Motacilla alba"
    assert species.order == "Passeriformes"
    assert species.family == "Motacillidae"
    assert species.genus == "Motacilla"
    assert species.code == "whiwag"


def test_convert_to_species_2():
    """Non-Finnish names should be detected and not saved under name_fi."""
    sp_obj = {
        "speciesCode": "whiwag",
        "comName": "White Wagtail",  # non-Finnish name
        "sciName": "Motacilla alba",
        "order": "Passeriformes",
        "familySciName": "Motacillidae"
    }

    species = ebird.convert_to_species(sp_obj, locale="fi")

    assert species.name_fi is None  # should be empty


@responses.activate
def test_get_regions_1():
    """Countries should be fetched succesfully from eBird API."""
    url = "https://api.ebird.org/v2/ref/region/list/country/world"
    params = {"fmt": "json"}
    api_key = "verysecretapikey"

    responses.add(
        responses.GET,
        url=url,
        match=[
            responses.matchers.header_matcher({"X-eBirdApiToken": api_key}),
            responses.matchers.query_param_matcher(params)
        ],
        json=[
            {"code": "US", "name": "United States"},
            {"code": "FI", "name": "Finland"},
            {"code": "AQ", "name": "Antarctica"},
        ]
    )

    session = requests.Session()
    result = ebird.get_regions(session=session, api_key=api_key)  # use default parent_region = "world"

    assert len(result) == 3
    assert {region["code"] for region in result} == {"US", "FI", "AQ"}


@responses.activate
def test_get_regions_2():
    """Subnational regions of type 1 should be fetched succesfully from eBird API."""
    url = "https://api.ebird.org/v2/ref/region/list/subnational1/US"
    params = {"fmt": "json"}
    api_key = "verysecretapikey"

    responses.add(
        responses.GET,
        url=url,
        match=[
            responses.matchers.header_matcher({"X-eBirdApiToken": api_key}),
            responses.matchers.query_param_matcher(params)
        ],
        json=[
            {"code": "US-TX", "name": "Texas"},
            {"code": "US-FL", "name": "Florida"},
            {"code": "US-NY", "name": "New York"},
        ]
    )

    session = requests.Session()
    result = ebird.get_regions(session=session, api_key=api_key, parent_region="US")

    assert len(result) == 3
    assert {region["code"] for region in result} == {"US-TX", "US-NY", "US-FL"}


@responses.activate
def test_get_regions_3():
    """Subnational regions of type 2 should be fetched succesfully from eBird API."""
    url = "https://api.ebird.org/v2/ref/region/list/subnational2/US-TX"
    params = {"fmt": "json"}
    api_key = "verysecretapikey"

    responses.add(
        responses.GET,
        url=url,
        match=[
            responses.matchers.header_matcher({"X-eBirdApiToken": api_key}),
            responses.matchers.query_param_matcher(params)
        ],
        json=[
            {"code": "US-TX-015", "name": "Austin"},
            {"code": "US-TX-113", "name": "Dallas"},
            {"code": "US-TX-141", "name": "El Paso"},
        ]
    )

    session = requests.Session()
    result = ebird.get_regions(session=session, api_key=api_key, parent_region="US-TX")

    assert len(result) == 3
    assert {region["code"] for region in result} == {"US-TX-015", "US-TX-113", "US-TX-141"}


@responses.activate
def test_get_regions_4():
    """Invalid parent region format should raise an error."""
    api_key = "verysecretapikey"
    session = requests.Session()

    with pytest.raises(ValueError):
        # invalid parent region format (more than 1 hyphen) should raise an error
        ebird.get_regions(session=session, api_key=api_key, parent_region="US-TX-141")


def test_convert_to_region_1():
    """Converted region should have the correct fields and values."""
    region_obj = {"code": "FI", "name": "Finland"}
    region = ebird.convert_to_region(region_obj, parent_region=None)

    assert type(region) == Region
    assert region.code == "FI"
    assert region.name_en == "Finland"
    assert region.parent_region is None


def test_convert_to_region_2():
    """Parent region should be set successfully when converting to a region."""
    region_obj = {"code": "US-TX", "name": "Texas"}
    parent_region = baker.prepare(Region, code="US", name_en="United States", parent_region=None)
    region = ebird.convert_to_region(region_obj, parent_region=parent_region)

    assert region.parent_region == parent_region


def test_convert_to_region_3():
    """Trying to convert an invalid region object should return None."""
    region_obj = {
        "code": "Suomi Finland Prkl",  # code has max length 9 -> validation should fail
        "name": "Finland"
    }
    region = ebird.convert_to_region(region_obj, parent_region=None)

    assert region is None


@responses.activate
def test_get_species_codes_by_region():
    url = "https://api.ebird.org/v2/product/spplist/FI"
    api_key = "verysecretapikey"

    responses.add(
        responses.GET,
        url=url,
        match=[
            responses.matchers.header_matcher({"X-eBirdApiToken": api_key})
        ],
        json=["whiwag", "yelwag", "grywag"]
    )

    session = requests.Session()
    result = ebird.get_species_codes_by_region(region_code="FI", session=session, api_key=api_key)

    assert result == ["whiwag", "yelwag", "grywag"]
