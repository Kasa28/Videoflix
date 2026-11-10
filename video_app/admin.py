from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import Video


@admin.register(Video)
class VideoAdmin(ImportExportModelAdmin):
    list_display = ("id", "title", "created_at")
    search_fields = ("title",)
