from django.core.exceptions import ValidationError
import requests

from quiz.models import Species, Region


def get_species_info(session: requests.Session, api_key: str) -> list[dict]:
    """
    Fetches taxonomic information of bird species from the eBird API.

    See eBird API documentation: https://documenter.getpostman.com/view/664302/S1ENwy59#952a4310-536d-4ad1-8f3e-77cfb624d1bc

    :param session:    Request session.
    :param api_token:  Valid eBird API access token.
    :return result:    List of species objects from eBird API response.
    """
    url = "https://api.ebird.org/v2/ref/taxonomy/ebird"
    params = {
        "cat": "species",
        "fmt": "json"
    }
    headers = {"X-eBirdApiToken": api_key}
    response = session.get(url, params=params, headers=headers)
    return response.json()


def convert_to_species(species_obj: dict) -> Species | None:
    """
    Converts eBird species object to Species database object and validates the fields.
    If field validation fails, returns None.

    :param species_obj: Species object from eBird API response.
    :return species: Converted Species db object or None if validation fails.
    """
    species = Species(
        code=species_obj["speciesCode"],
        name_en=species_obj["comName"],
        name_sci=species_obj["sciName"],
        order=species_obj["order"],
        family=species_obj["familySciName"],
        genus=species_obj["sciName"].split()[0]
    )
    try:
        species.clean_fields()
    except ValidationError:
        return
    return species


def get_regions(session: requests.Session, api_key: str, parent_region: str = "world") -> list[dict[str, str]]:
    """
    Get a list of eBird subregions of a parent region from the eBird API.
    If parent region is "world", lists countries.
    If parent region is a country, lists subnational regions.
    If parent region is a subnational regions, lists sub-subnational regions.

    :param parent_region: Region whose subregions are listed.
    :returns: List of region dicts with keys "code" and "name".
    """
    if parent_region == "world":
        region_type = "country"
    else:
        match len(parent_region.split("-")):
            case 1:
                region_type = "subnational1"
            case 2:
                region_type = "subnational2"
            case _:
                raise ValueError("Invalid parent region")
    url = f"https://api.ebird.org/v2/ref/region/list/{region_type}/{parent_region}"
    params = {"fmt": "json"}
    headers = {"X-eBirdApiToken": api_key}
    response = session.get(url, params=params, headers=headers)
    return response.json()


def convert_to_region(region_obj: dict) -> Region | None:
    """
    Converts eBird region object to Region database object and validates the fields.
    If field validation fails, returns None.

    :param region_obj: Region object from eBird API response.
    :return region: Converted Region db object or None if validation fails.
    """
    region = Region(**region_obj)
    try:
        region.clean_fields()
    except ValidationError:
        return
    return region


def get_species_codes_by_region(region_code: str, session: requests.Session, api_key: str) -> list[dict]:
    """
    Get list of codes for species that have been observed in a region from the eBird API.

    :param region_code: Region code.
    :returns: List of species codes.
    """
    url = f"https://api.ebird.org/v2/product/spplist/{region_code}"
    headers = {"X-eBirdApiToken": api_key}
    response = session.get(url, headers=headers)
    return response.json()
