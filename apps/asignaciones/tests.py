from django.test import TestCase

from apps.inventario.models import Equipo
from apps.titulares.models import Titular
from .models import Asignacion


class AsignacionCrudTests(TestCase):
    def setUp(self):
        self.equipo = Equipo.objects.create(
            codigo="EQ-A",
            nombre="Equipo de prueba",
        )
        self.titular = Titular.objects.create(nombre="Titular Uno")

    def test_create_edit_and_delete_assignment(self):
        response = self.client.post(
            "/asignaciones/nueva/",
            {
                "equipo": self.equipo.pk,
                "titular": self.titular.pk,
                "activa": "on",
            },
        )
        self.assertRedirects(response, "/asignaciones/")
        asignacion = Asignacion.objects.get()
        self.assertTrue(asignacion.activa)

        response = self.client.post(
            f"/asignaciones/editar/{asignacion.pk}/",
            {
                "equipo": self.equipo.pk,
                "titular": self.titular.pk,
            },
        )
        self.assertRedirects(response, "/asignaciones/")
        asignacion.refresh_from_db()
        self.assertFalse(asignacion.activa)

        self.client.get(f"/asignaciones/eliminar/{asignacion.pk}/")
        self.assertTrue(Asignacion.objects.filter(pk=asignacion.pk).exists())
        response = self.client.post(f"/asignaciones/eliminar/{asignacion.pk}/")
        self.assertRedirects(response, "/asignaciones/")
        self.assertFalse(Asignacion.objects.filter(pk=asignacion.pk).exists())

    def test_multiple_holders_can_be_assigned_to_same_equipment(self):
        otro_titular = Titular.objects.create(nombre="Titular Dos")
        Asignacion.objects.create(equipo=self.equipo, titular=self.titular)
        Asignacion.objects.create(equipo=self.equipo, titular=otro_titular)

        self.assertEqual(
            Asignacion.objects.filter(equipo=self.equipo, activa=True).count(),
            2,
        )

    def test_assignment_pages_render(self):
        self.assertEqual(self.client.get("/asignaciones/").status_code, 200)
        self.assertEqual(self.client.get("/asignaciones/nueva/").status_code, 200)

# Create your tests here.
