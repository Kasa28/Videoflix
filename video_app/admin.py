from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Video

@admin.register(Video)
class VideoManagementAdmin(ImportExportModelAdmin):
    list_display = ("id", "title", "category", "created_at")
    list_filter = ("category",)
    search_fields = ("title", "description")
    exclude = ("thumbnail",)
