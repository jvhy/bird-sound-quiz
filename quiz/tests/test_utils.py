"""Unit tests for utility functions"""

from django.utils.translation import override

from quiz.models import Species, Region
from quiz import utils


def test_check_answer():
    sp = Species(
        name_en="Great Black-backed Gull",
        name_fi="merilokki",
        name_sci="Larus marinus",
        order="Charadriiformes",
        family="Laridae",
        genus="Larus",
        code="gbbgul"
    )

    # Accepted answers
    answer_1 = "Great Black-backed Gull"
    answer_2 = "merilokki"
    answer_3 = "Larus marinus"
    assert all(utils.check_answer(answer, sp) for answer in (answer_1, answer_2, answer_3))

    # Accepted answers, variations
    answer_4 = "MeriLokki"          # answer checking should be case insensitive
    answer_5 = " Larus marinus \n"  # surrounding whitespace should be stripped before checking
    assert all(utils.check_answer(answer, sp) for answer in (answer_4, answer_5))

    # Incorrect answers
    answer_6 = "Great Black backed Gull"
    answer_7 = "Meri lokki"
    answer_8 = ""
    assert not any(utils.check_answer(answer, sp) for answer in (answer_6, answer_7, answer_8))


def test_create_region_display_name_1():
    region_1 = Region(
        code="US",
        name_en="United States",
        name_fi="Yhdysvallat",
        parent_region=None
    )
    region_2 = Region(
        code="US-TX",
        name_en="Texas",
        name_fi="Texas",
        parent_region=region_1
    )
    region_3 = Region(
        code="US-TX-015",
        name_en="Austin",
        name_fi="Austin",
        parent_region=region_2
    )

    display_name_en_1 = utils.create_region_display_name(region_1)
    display_name_en_2 = utils.create_region_display_name(region_2)
    display_name_en_3 = utils.create_region_display_name(region_3)

    assert display_name_en_1 == "United States"
    assert display_name_en_2 == "United States - Texas"
    assert display_name_en_3 == "United States - Texas - Austin"

    with override("fi"):
        display_name_fi_1 = utils.create_region_display_name(region_1)
        display_name_fi_2 = utils.create_region_display_name(region_2)
        display_name_fi_3 = utils.create_region_display_name(region_3)

    assert display_name_fi_1 == "Yhdysvallat"
    assert display_name_fi_2 == "Yhdysvallat - Texas"
    assert display_name_fi_3 == "Yhdysvallat - Texas - Austin"


def test_create_region_display_name_2():
    """Region display name should fall back to English if current locale is empty."""
    region = Region(
        code="JP",
        name_en="Japan",
        parent_region=None
    )

    with override("fi"):
        display_name = utils.create_region_display_name(region)  # name_fi is empty -> use name_en

    assert display_name == "Japan"
