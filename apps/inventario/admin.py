from django.contrib import admin
from apps.asignaciones.models import Asignacion
from .models import Equipo, FotoEquipo


class FotoEquipoInline(admin.TabularInline):
    model = FotoEquipo
    extra = 1


class AsignacionInline(admin.TabularInline):
    model = Asignacion
    extra = 1
    autocomplete_fields = ("titular",)


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "marca", "modelo", "estado")
    list_filter = ("estado", "marca")
    search_fields = ("codigo", "nombre", "serie", "marca", "modelo")
    inlines = (AsignacionInline, FotoEquipoInline)
    readonly_fields = ("fecha_creacion",)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        etiquetas = {
            "codigo": "Código",
            "nombre": "Nombre",
            "ampliacion": "Descripción ampliada",
            "serie": "Serie",
            "numero_telefono": "Número de teléfono",
            "extension": "Extensión",
            "marca": "Marca",
            "modelo": "Modelo",
            "gfh_codigo": "GFH (Cód.)",
            "gfh_descripcion": "GFH (Descripción)",
            "area_codigo": "Área (Cód.)",
            "area_descripcion": "Área (Descripción)",
            "fecha_puesta_en_servicio": "Fecha puesta en servicio",
            "modo_incorporacion": "Modo de incorporación",
            "naturaleza_patrimonial": "Naturaleza patrimonial",
            "servicio": "Servicio",
            "estado": "Situación patrimonial",
            "observaciones": "Observaciones",
        }
        for campo, etiqueta in etiquetas.items():
            form.base_fields[campo].label = etiqueta
        return form
