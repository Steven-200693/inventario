from django.db import models


class Titular(models.Model):
    nombre = models.CharField(max_length=200)
    cargo = models.CharField(max_length=200, blank=True)
    correo = models.EmailField(blank=True)
    foto = models.ImageField(
        upload_to="titulares/",
        null=True,
        blank=True,
    )
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Titulares"
        verbose_name_plural = "Titulares"

    def __str__(self):
        return self.nombre
