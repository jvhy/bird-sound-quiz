from django.contrib import admin

from quiz.models import Region


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
