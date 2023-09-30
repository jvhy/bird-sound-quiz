import pandas as pd
import requests
import re
import os
from quiz import BirdSound, QuizSpecies


API_TOKEN = os.environ.get('API_TOKEN')


def get_species_info() -> pd.DataFrame:
    """
    Fetches information of each bird species observed in Finland from the laji.fi API.

    :return species_df: dataframe containing bird species info
    """

    endpoint = "https://api.laji.fi/v0/taxa"
    selected_fields = ["id", "parent", "primaryHabitat", "secondaryHabitats", "latestRedListStatusFinland"]
    params = {
                "access_token": API_TOKEN,
                "taxonRanks": "MX.species",
                "parentTaxonId": "MX.37580",  # taxon id for class Aves (birds)
                "lang": "fi",
                "onlyFinnish": True,
                "includeDescriptions": True,
                "includeMedia": True,
                "pageSize": 1000,
                "selectedFields": ",".join(selected_fields),
             }
    response = requests.get(url=endpoint, params=params).json()
    data = response["results"]

    species_rows = []
    for i, species in enumerate(data):
        # Names and taxonomic information
        order = species["parent"].get("order", {}).get("scientificName")
        family = species["parent"].get("family", {}).get("scientificName")
        genus = species["parent"].get("genus", {}).get("scientificName")
        species_names = species["parent"].get("species", {})
        name_fi = species_names.get("vernacularName")
        name_lt = species_names.get("scientificName")

        # Habitats
        habitat_df = get_habitat_metadata()
        primary_habitat = species.get("primaryHabitat")
        secondary_habitats = species.get("secondaryHabitats", [])
        habitat_codes = [habitat.get("habitat") for habitat in [primary_habitat] + secondary_habitats if habitat]
        habitats = []
        for habitat_code in habitat_codes:
            habitat = habitat_df.loc[habitat_code, "value"]
            habitat = re.sub(r"[A-ZÅÄÖ][a-zåäö]* – ", "", habitat)
            habitat = re.sub(r"\(.*\)", "", habitat)
            habitat = habitat.lower().strip()
            if habitat == "perinneympäristöt ja muut ihmisen muuttamat ympäristöt":
                habitat = "perinneympäristöt"
            if habitat not in habitats:
                habitats.append(habitat)

        # Rarity
        rarity_df = get_rarity_metadata()
        rarity_statuses = species.get("redListStatusesFinland", [{}])
        rarity_code = rarity_statuses[0].get("status")  # the latest rarity status
        rarity = rarity_df.loc[rarity_code, "value"] if rarity_code else None

        # Descriptions
        descriptions = []
        description_objs = species.get("descriptions", [])
        for description_obj in description_objs:
            for group in description_obj["groups"]:
                variables = group["variables"]
                for var in variables:
                    if var["title"] in ["Tunnistaminen", "Yleiskuvaus", "Elintavat", "Elinkierto", "Elinympäristö"]:
                        content = re.sub(r"</?\w+>", "", var["content"])
                        content = content.replace("&#xa0;", " ")
                        content = content.replace("&nbsp;", '"')
                        descriptions.append({var["title"]: content})

        # Images, copyrights & licenses
        media = species.get("multimedia", [])
        image_obj = media[0] if media else {}
        owner = image_obj.get("copyrightOwner")
        author = image_obj.get("author")
        cc_license = image_obj.get("licenseAbbreviation")
        url = image_obj.get("squareThumbnailURL")
        caption = image_obj.get("caption", "")
        flickr_match = re.search(r"(http://www.flickr.com/people/(\w+))\b", caption)
        flickr_url = flickr_match.group(1) if flickr_match else None
        flickr_username = flickr_match.group(2) if flickr_match else None

        species_row = {"comNameFI": name_fi,
                       "sciName": name_lt,
                       "taxonomicOrder": order,
                       "taxonomicFamily": family,
                       "taxonomicGenus": genus,
                       "habitats": habitats,
                       "rarity": rarity,
                       "decriptions": descriptions,
                       "imageUrl": url,
                       "imageRightsHolder": owner,
                       "imageAuthor": author,
                       "authorFlickrUrl": flickr_url,
                       "authorFlickrName": flickr_username,
                       "imageLicense": cc_license,
                       }
        species_rows.append(species_row)
    species_df = pd.DataFrame(species_rows)

    return species_df


def get_habitat_metadata():
    endpoint = "https://api.laji.fi/v0/metadata/properties/MKV.habitat/ranges"
    params = {
                "access_token": API_TOKEN,
                "lang": "fi"
             }
    response = requests.get(url=endpoint, params=params).json()
    habitat_df = pd.DataFrame(response)
    habitat_df = habitat_df.set_index("id")

    return habitat_df


def get_rarity_metadata():
    endpoint = "https://api.laji.fi/v0/metadata/ranges/MX.iucnStatuses"
    params = {
                "access_token": API_TOKEN,
                "lang": "fi"
             }
    response = requests.get(url=endpoint, params=params).json()
    rarity_df = pd.DataFrame(response)
    rarity_df = rarity_df.set_index("id")

    return rarity_df


def get_atlas_info() -> pd.DataFrame():
    atlas_df = pd.read_csv("data/atlasdata.csv")

    return atlas_df


def get_recording_info() -> pd.DataFrame:
    """
    Fetches all bird sound recordings from the Xeno-Canto API from 5 countries.

    :return recording_df: dataframe of bird sound recordings and their metadata
    """

    recordings = []
    endpoint = "https://xeno-canto.org/api/2/recordings"
    for country in ["finland", "sweden", "norway", "denmark", "estonia"]:
        current_page = 1
        more_pages = True
        params = {"query": f'grp:birds cnt:{country} q:A len:0-60', "page": current_page}
        while more_pages:
            response = requests.get(url=endpoint, params=params).json()
            data = response.get("recordings")
            recordings.extend(data)
            total_pages = response.get("numPages")
            if total_pages == current_page:
                more_pages = False
            else:
                current_page += 1
                params["page"] = current_page

    recording_df = pd.DataFrame(recordings)
    recording_df["sciName"] = recording_df["gen"] + " " + recording_df["sp"]  # scientific name = genus + species
    recording_df["lic"] = recording_df["lic"].map(extract_license_type)
    recording_df = recording_df[["id", "url", "file", "rec", "cnt", "loc", "type", "lic", "sciName"]]
    recording_df = recording_df.dropna(subset=["id", "url", "file", "rec", "lic", "sciName"])
    recording_df = recording_df.rename(columns={"id": "recId",
                                                "url": "recUrl",
                                                "file": "recFileUrl",
                                                "rec": "recAuthor",
                                                "cnt": "recCountry",
                                                "loc": "recLocation",
                                                "type": "recType",
                                                "lic": "recLicense"})
    return recording_df


def extract_license_type(license_url: str):
    """
    Reformats the Creative Commons license URL of a sound recording to the name of the license for display purposes.

    :param license_url: URL to the CC license type page
    :return license_type: name of the CC license type
    """

    m = re.match(r"//creativecommons.org/licenses/([a-z-]+)/(\d\.\d)/", license_url)
    license_type = f"CC {m.group(1).upper()} {m.group(2)}" if m else None
    return license_type


def merge_species_info(recording_df: pd.DataFrame, species_df: pd.DataFrame, atlas_df: pd.DataFrame) -> pd.DataFrame:
    species_df = species_df.merge(atlas_df, how="left", on="comNameFI", validate="1:1")
    recording_df = recording_df.merge(species_df, how="left", on="sciName", validate="m:1")
    recording_df = recording_df.dropna(subset=["atlasSquareCount", "imageUrl"])

    return recording_df


def reformat_recordings(recording_df: pd.DataFrame) -> []:
    """
    Reformats the dataframe of bird sound recordings to a list of MysterySpecies objects.

    :param recording_df: dataframe of bird sound recordings
    :return species_list: list containing all nesting species in Finland.
    """

    species_list = []
    for species in recording_df["sciName"].unique():
        subdf = recording_df.loc[recording_df["sciName"] == species]
        species_sounds = [BirdSound(*values) for values in
                          subdf[["recId", "recUrl", "recFileUrl", "recAuthor",
                                 "recCountry", "recLocation", "recType", "recLicense"]].values]
        mystery_species = QuizSpecies(common_name_FI=subdf["comNameFI"].values[0],
                                      scientific_name=species,
                                      sounds=species_sounds,
                                      square_count=subdf["atlasSquareCount"].values[0])
        species_list.append(mystery_species)

    return species_list


def main():
    species_df = get_species_info()
    recordings_df = get_recording_info()
    atlas_df = get_atlas_info()
    df = merge_species_info(recording_df=recordings_df, species_df=species_df, atlas_df=atlas_df)
    df.to_csv("data/recordings.csv", index=False)


if __name__ == "__main__":
    main()
