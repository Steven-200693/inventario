from django.db import models
class SubredEquipo(models.Model):
    ESTADOS = [
        ("FUNCIONAL", "Funcional"),
        ("MANTENIMIENTO", "Mantenimiento"),
        ("DAÑADO", "Dañado"),
        ("BAJA", "Baja"),
    ]

    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=150)
    ampliacion = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Descripción ampliada",
    )
    serie = models.CharField(max_length=150, blank=True)
    numero_telefono = models.CharField(max_length=50, blank=True)
    extension = models.CharField(max_length=30, blank=True)
    marca = models.CharField(max_length=100, blank=True)
    modelo = models.CharField(max_length=100, blank=True)
    gfh_codigo = models.CharField(max_length=50, blank=True)
    gfh_descripcion = models.CharField(max_length=255, blank=True)
    area_codigo = models.CharField(max_length=50, blank=True)
    area_descripcion = models.CharField(max_length=255, blank=True)
    fecha_puesta_en_servicio = models.DateField(null=True, blank=True)
    modo_incorporacion = models.CharField(max_length=100, blank=True)
    servicio = models.CharField(max_length=150, blank=True)
    naturaleza_patrimonial = models.CharField(max_length=100, blank=True)
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default="FUNCIONAL",
    )
    observaciones = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class FotoSubredEquipo(models.Model):
    equipo = models.ForeignKey(
        SubredEquipo,
        on_delete=models.CASCADE,
        related_name="fotos",
    )
    foto = models.ImageField(upload_to="subred/")
    fecha_carga = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Foto de {self.equipo.codigo}"


from django.db.models.signals import post_delete
from django.dispatch import receiver


@receiver(post_delete, sender=FotoSubredEquipo)
def eliminar_archivo_de_foto_subred(sender, instance, **kwargs):
    if instance.foto:
        instance.foto.delete(save=False)
