from django.contrib import admin
from .models import Asignacion


@admin.register(Asignacion)
class AsignacionAdmin(admin.ModelAdmin):
    list_display = ("equipo", "titular", "fecha_asignacion", "activa")
    list_filter = ("activa", "fecha_asignacion")
    search_fields = ("equipo__codigo", "equipo__nombre", "titular__nombre")
