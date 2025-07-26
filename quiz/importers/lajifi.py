from django.core.exceptions import ValidationError
import requests

from quiz.models import Species


def get_species_info(session: requests.Session, access_token: str) -> list[dict[str, str]]:
    """
    Fetches information of bird species observed in Finland from the laji.fi API.

    :param session:    Request session.
    :param api_token:  Valid laji.fi API access token.
    :return result:    List of dicts with keys "vernacularName" and "scientificName".
    """
    url = "https://api.laji.fi/v0/taxa"
    params = {
        "access_token": access_token,
        "taxonRanks": "MX.species",
        "parentTaxonId": "MX.37580",  # taxon id for class Aves (birds)
        "onlyFinnish": True,  # include only Finnish species
        "selectedFields": "vernacularName,scientificName,parent",
        "lang": "en",
        "pageSize": 1000  # will fit all species, no need to paginate further
    }
    response = session.get(url=url, params=params)
    result = response.json().get("results", [])
    return result


def convert_to_species(species_obj: dict) -> Species | None:
    """
    Converts laji.fi species object to Species database object and validates the fields.
    If field validation fails, returns None.

    :param taxon_obj: Species object from laji.fi API response.
    :return species: Converted Species db object or None if validation fails.
    """
    species = Species(
        name_en=species_obj["vernacularName"],
        name_sci=species_obj["scientificName"],
        order=species_obj["parent"]["order"]["scientificName"],
        family=species_obj["parent"]["family"]["scientificName"],
        genus=species_obj["parent"]["genus"]["scientificName"]
    )
    try:
        species.clean_fields()
    except ValidationError:
        return
    return species
