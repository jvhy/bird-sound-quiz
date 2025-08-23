from django.contrib import admin

from quiz.models import Region, Species, SpeciesList, ListSpecies


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('code', 'display_name', 'parent_region')
    search_fields = ('code', 'name_en', 'name_fi')
    list_filter = ('parent_region',)
    ordering = ('code',)

    # Optional: make display_name sortable by code
    def display_name(self, obj):
        return obj.display_name

    display_name.admin_order_field = 'name_en'
    display_name.short_description = 'Display Name'


class ListSpeciesInline(admin.TabularInline):
    model = ListSpecies
    autocomplete_fields = ["species"]
    extra = 1


class RegionFilter(admin.SimpleListFilter):
    title = "Region"
    parameter_name = "region"

    def lookups(self, request, model_admin):
        return [(r.id, r.name) for r in Region.objects.all()]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(regions__id=self.value())
        return queryset


@admin.register(SpeciesList)
class SpeciesListAdmin(admin.ModelAdmin):
    list_display = ("name", "is_official", "created_by", "created_at", "regions_list", "type", "species_count")
    list_filter = ("is_official", "type", RegionFilter)
    search_fields = ("name", "name_sci", "code", "created_by__username")
    autocomplete_fields = ("regions",)
    inlines = [ListSpeciesInline]
    save_as = True

    def species_count(self, obj):
            return obj.species_entries.count()
    species_count.short_description = "Species count"

    def regions_list(self, obj):
        return ", ".join([r.name for r in obj.regions.all()])
    regions_list.short_description = "Regions"


@admin.register(Species)
class SpeciesAdmin(admin.ModelAdmin):
    list_display = ("name", "name_sci", "order", "family", "genus", "code")
    search_fields = ("name", "name_sci", "code")
    list_filter = ("order", "family")
    ordering = ("name",)
