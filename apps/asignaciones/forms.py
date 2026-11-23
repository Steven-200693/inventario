from django import forms

from .models import Asignacion


class AsignacionForm(forms.ModelForm):
    class Meta:
        model = Asignacion
        fields = ("equipo", "titular", "activa")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = (
                "mt-1 block w-full rounded-lg border border-slate-300 "
                "bg-white px-3 py-2 shadow-sm focus:border-blue-500 "
                "focus:outline-none focus:ring-2 focus:ring-blue-200"
            )
