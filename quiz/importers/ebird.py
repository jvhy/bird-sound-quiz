from django.core.exceptions import ValidationError
import requests

from quiz.models import Species


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
