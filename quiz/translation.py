from modeltranslation.translator import translator, TranslationOptions

from quiz.models import Species, Region


class SpeciesTranslationOptions(TranslationOptions):
    fields = ("name",)
    required_languages = ("en",)


class RegionTranslationOptions(TranslationOptions):
    fields = ("name",)
    required_languages = ("en",)


translator.register(Species, SpeciesTranslationOptions)
translator.register(Region, RegionTranslationOptions)
