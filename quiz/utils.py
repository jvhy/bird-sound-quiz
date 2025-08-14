from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from quiz.models import Region, Species


def create_region_display_name(region: "Region", locale: str) -> str:
    """
    Create a display name for a region with the region name preceded by possible parent region(s) separated by hyphens.
    If region has no parent regions, return region name.

    :param region: Region for which a display name is created.
    :param locale: Which locale to use for the name.
    :return display_name: Display name in the format {parent region 2} - {parent region 1} - {region}.
    """
    name_field = f"name_{locale}"
    fallback_field = "name_en"  # if region name is not available in selected locale, use English instead
    parent_region_1 = region.parent_region if region.parent_region else None
    parent_region_2 = parent_region_1.parent_region if parent_region_1 else None
    return " - ".join([getattr(reg, name_field) or getattr(reg, fallback_field) for reg in [parent_region_2, parent_region_1, region] if reg])


def check_answer(user_answer: str, correct_species: "Species") -> bool:
    """
    Check if user answer to a quiz question is correct.

    :param user_answer: Answer given by user.
    :param correct_species: The species that is the correct answer to the quiz question.
    :returns is_correct: Boolean that indicates whether answer is correct.
    """
    user_answer_normalized = user_answer.lower().strip()
    name_fields = (field.name for field in correct_species._meta.fields if field.name.startswith("name_"))
    is_correct = any(user_answer_normalized == getattr(correct_species, name_field, "").lower().strip() for name_field in name_fields)
    return is_correct
