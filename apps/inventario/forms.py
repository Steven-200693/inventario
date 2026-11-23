from django import forms

from .models import Equipo


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.ImageField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        if not data:
            return []
        files = data if isinstance(data, (list, tuple)) else [data]
        return [
            super(MultipleImageField, self).clean(file, initial)
            for file in files
        ]


class ImportarExcelForm(forms.Form):
    archivo = forms.FileField(
        label="Archivo Excel",
        help_text="Selecciona un archivo .xlsx con una hoja llamada Inventario.",
    )

    def clean_archivo(self):
        archivo = self.cleaned_data["archivo"]
        if not archivo.name.lower().endswith(".xlsx"):
            raise forms.ValidationError("El archivo debe tener formato .xlsx.")
        return archivo


class EquipoForm(forms.ModelForm):
    titular = forms.CharField(
        label="Titular",
        required=False,
        help_text="Escribe el nombre del titular como aparece en el libro de inventario.",
    )
    fotos = MultipleImageField(
        required=False,
        label="Fotografías del equipo",
        help_text="Puedes seleccionar varias imágenes.",
    )

    class Meta:
        model = Equipo
        fields = (
            "codigo",
            "nombre",
            "ampliacion",
            "serie",
            "numero_telefono",
            "extension",
            "marca",
            "modelo",
            "gfh_codigo",
            "gfh_descripcion",
            "area_codigo",
            "area_descripcion",
            "fecha_puesta_en_servicio",
            "modo_incorporacion",
            "naturaleza_patrimonial",
            "servicio",
            "estado",
            "observaciones",
        )
        widgets = {
            "observaciones": forms.Textarea(attrs={"rows": 4}),
            "fecha_puesta_en_servicio": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            titular_actual = self.instance.asignaciones.filter(
                activa=True,
            ).select_related("titular").first()
            if titular_actual:
                self.fields["titular"].initial = titular_actual.titular.nombre

        self.fields["codigo"].label = "Código"
        self.fields["nombre"].label = "Nombre"
        self.fields["ampliacion"].label = "Descripción ampliada"
        self.fields["serie"].label = "Serie"
        self.fields["numero_telefono"].label = "Número de teléfono"
        self.fields["extension"].label = "Extensión"
        self.fields["marca"].label = "Marca"
        self.fields["modelo"].label = "Modelo"
        self.fields["gfh_codigo"].label = "GFH (Cód.)"
        self.fields["gfh_descripcion"].label = "GFH (Descripción)"
        self.fields["area_codigo"].label = "Área (Cód.)"
        self.fields["area_descripcion"].label = "Área (Descripción)"
        self.fields["fecha_puesta_en_servicio"].label = "Fecha puesta en servicio"
        self.fields["modo_incorporacion"].label = "Modo de incorporación"
        self.fields["naturaleza_patrimonial"].label = "Naturaleza patrimonial"
        self.fields["servicio"].label = "Servicio"
        self.fields["estado"].label = "Situación patrimonial"

        for field in self.fields.values():
            field.widget.attrs["class"] = (
                "mt-1 block w-full rounded-lg border border-slate-300 "
                "bg-white px-3 py-2 shadow-sm focus:border-blue-500 "
                "focus:outline-none focus:ring-2 focus:ring-blue-200"
            )
        self.fields["fotos"].widget.attrs.update(
            {"accept": "image/*", "multiple": True}
        )
