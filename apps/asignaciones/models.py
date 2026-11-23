from django.db import models
from apps.inventario.models import Equipo
from apps.titulares.models import Titular


class Asignacion(models.Model):
    equipo = models.ForeignKey(
        Equipo,
        on_delete=models.CASCADE,
        related_name="asignaciones",
    )
    titular = models.ForeignKey(
        Titular,
        on_delete=models.CASCADE,
        related_name="asignaciones",
    )
    fecha_asignacion = models.DateField(auto_now_add=True)
    activa = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.equipo} - {self.titular}"
