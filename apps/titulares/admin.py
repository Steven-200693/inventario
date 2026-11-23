from django.contrib import admin
from .models import Titular


@admin.register(Titular)
class TitularAdmin(admin.ModelAdmin):
    search_fields = ("nombre", "cargo", "correo")
