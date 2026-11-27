from django.test import TestCase

from apps.inventario.models import Equipo
from apps.titulares.models import Titular


class DashboardTests(TestCase):
    def setUp(self):
        for index in range(3):
            Equipo.objects.create(
                codigo=f"MON-{index}",
                nombre="MONITOR",
                estado="FUNCIONAL",
            )
        Equipo.objects.create(
            codigo="CEL-1",
            nombre="CELULAR",
            estado="MANTENIMIENTO",
        )
        Titular.objects.create(nombre="Titular de prueba")

    def test_dashboard_shows_device_totals_percentages_and_images(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Total de equipos")
        self.assertContains(response, "4")
        self.assertContains(response, "MONITOR")
        self.assertContains(response, "CELULAR")
        self.assertContains(response, "75.0%")
        self.assertContains(response, "25.0%")
        self.assertContains(response, 'device-icons.svg#monitor')
        self.assertContains(response, 'device-icons.svg#mobile')
        self.assertContains(response, 'role="progressbar"')

    def test_empty_dashboard_renders_without_division_by_zero(self):
        Equipo.objects.all().delete()

        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Aún no hay equipos registrados")
