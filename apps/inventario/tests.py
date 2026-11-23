from io import BytesIO
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.core.management.base import CommandError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from openpyxl import Workbook
from PIL import Image

from apps.asignaciones.models import Asignacion
from apps.titulares.models import Titular
from .models import Equipo, FotoEquipo


class InventarioCrudTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.media_dir = TemporaryDirectory()
        cls.media_override = override_settings(MEDIA_ROOT=cls.media_dir.name)
        cls.media_override.enable()

    @classmethod
    def tearDownClass(cls):
        cls.media_override.disable()
        cls.media_dir.cleanup()
        super().tearDownClass()

    def test_create_search_and_delete_equipment(self):
        response = self.client.post(
            "/inventario/nuevo/",
            {
                "codigo": "EQ-001",
                "nombre": "Laptop",
                "serie": "SER-1",
                "marca": "Marca",
                "modelo": "Modelo",
                "servicio": "TI",
                "estado": "FUNCIONAL",
                "observaciones": "",
            },
        )
        self.assertRedirects(response, "/inventario/")
        equipo = Equipo.objects.get(codigo="EQ-001")

        response = self.client.get("/inventario/?q=Laptop")
        self.assertContains(response, "EQ-001")
        self.assertContains(response, "Laptop")
        self.assertNotContains(
            self.client.get("/inventario/?q=no-existe"),
            "EQ-001",
        )

        self.client.get(f"/inventario/eliminar/{equipo.pk}/")
        self.assertTrue(Equipo.objects.filter(pk=equipo.pk).exists())
        response = self.client.post(f"/inventario/eliminar/{equipo.pk}/")
        self.assertRedirects(response, "/inventario/")
        self.assertFalse(Equipo.objects.filter(pk=equipo.pk).exists())

    def test_create_equipment_captures_excel_fields_and_titular(self):
        response = self.client.post(
            "/inventario/nuevo/",
            {
                "codigo": "EQ-EXCEL",
                "nombre": "MONITOR",
                "ampliacion": "MONITOR DESKTOP",
                "serie": "SER-987",
                "numero_telefono": "300123456",
                "extension": "123",
                "marca": "HPE",
                "modelo": "E24",
                "gfh_codigo": "17",
                "gfh_descripcion": "SERVICIOS GENERALES",
                "area_codigo": "A-10",
                "area_descripcion": "ALMACEN",
                "fecha_puesta_en_servicio": "2024-01-15",
                "modo_incorporacion": "COMPRA",
                "estado": "FUNCIONAL",
                "titular": "Ana Perez - Coordinadora",
                "naturaleza_patrimonial": "GUIA DE DOTACION",
                "servicio": "Almacen",
                "observaciones": "",
            },
        )

        self.assertRedirects(response, "/inventario/")
        equipo = Equipo.objects.get(codigo="EQ-EXCEL")
        self.assertEqual(equipo.ampliacion, "MONITOR DESKTOP")
        self.assertEqual(equipo.gfh_codigo, "17")
        self.assertEqual(equipo.area_descripcion, "ALMACEN")
        self.assertEqual(equipo.fecha_puesta_en_servicio.isoformat(), "2024-01-15")
        self.assertTrue(
            Asignacion.objects.filter(
                equipo=equipo,
                titular__nombre="Ana Perez - Coordinadora",
                activa=True,
            ).exists()
        )

    def test_new_equipment_form_has_excel_field_labels(self):
        response = self.client.get("/inventario/nuevo/")

        for label in (
            "Código",
            "Nombre",
            "Descripción ampliada",
            "Número de teléfono",
            "GFH (Cód.)",
            "GFH (Descripción)",
            "Área (Cód.)",
            "Área (Descripción)",
            "Fecha puesta en servicio",
            "Modo de incorporación",
            "Situación patrimonial",
            "Titular",
            "Naturaleza patrimonial",
            "Servicio",
        ):
            self.assertContains(response, label)

    def test_equipment_list_shows_all_fields_without_horizontal_table(self):
        Equipo.objects.create(
            codigo="EQ-BUSCAR",
            nombre="Equipo localizable",
            estado="FUNCIONAL",
        )

        response = self.client.get("/inventario/")

        self.assertContains(response, 'id="buscador"')
        self.assertContains(response, 'src="/static/js/busqueda.js?v=3"')
        self.assertContains(response, "data-search-primary")
        self.assertNotContains(response, "overflow-x-auto")
        self.assertNotContains(response, "min-w-[2400px]")
        self.assertContains(response, "Equipo localizable")
        for encabezado in (
            "D.Ampli.",
            "Número de teléfono",
            "GFH (Cód.)",
            "GFH (Descripción)",
            "Área (Cód.)",
            "Área (Descripción)",
            "Fecha puesta en servicio",
            "Modo de incorporación",
            "Situación patrimonial",
            "Naturaleza patrimonial",
            "Titular(es)",
            "Servicio",
            "Observaciones",
        ):
            self.assertContains(response, encabezado)

    def test_inventory_page_links_to_import_and_export(self):
        response = self.client.get("/inventario/")
        self.assertContains(response, 'href="/inventario/importar/"')
        self.assertContains(response, 'href="/inventario/exportar/"')
        self.assertContains(response, "data-export-link")
        self.assertContains(response, 'src="/static/js/busqueda.js?v=3"')

    def test_export_download_contains_inventory_headers_and_values(self):
        Equipo.objects.create(
            codigo="EQ-EXPORT",
            nombre="Equipo exportado",
            ampliacion="Descripción de prueba",
            gfh_codigo="17",
            servicio="Servicio TI",
        )

        response = self.client.get("/inventario/exportar/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            response["Content-Type"],
        )
        self.assertIn('filename="inventario.xlsx"', response["Content-Disposition"])
        from openpyxl import load_workbook

        workbook = load_workbook(BytesIO(response.content))
        sheet = workbook["Inventario"]
        self.assertEqual(sheet.cell(1, 1).value, "Código")
        self.assertEqual(sheet.cell(1, 3).value, "D.Ampli.")
        self.assertEqual(sheet["A1"].fill.fgColor.rgb, "001F4E78")
        self.assertTrue(sheet["A1"].font.bold)
        self.assertEqual(sheet["A1"].font.color.rgb, "00FFFFFF")
        self.assertEqual(sheet.cell(2, 1).value, "EQ-EXPORT")
        self.assertEqual(sheet.cell(2, 3).value, "Descripción de prueba")
        self.assertEqual(
            sheet.column_dimensions["C"].width,
            len("Descripción de prueba") + 2,
        )
        self.assertEqual(sheet.cell(2, 18).value, "Servicio TI")
        workbook.close()

    def test_export_keeps_cell_values_safe_and_formats_dates(self):
        Equipo.objects.create(
            codigo="0007",
            nombre="MONITOR\x01",
            fecha_puesta_en_servicio=datetime(2024, 5, 6).date(),
        )

        response = self.client.get("/inventario/exportar/")

        from openpyxl import load_workbook

        workbook = load_workbook(BytesIO(response.content))
        sheet = workbook["Inventario"]
        self.assertEqual(sheet["A2"].value, "0007")
        self.assertEqual(sheet["A2"].data_type, "s")
        self.assertEqual(sheet["B2"].value, "MONITOR")
        self.assertEqual(sheet["M2"].value.date(), datetime(2024, 5, 6).date())
        self.assertEqual(sheet["M2"].number_format, "dd/mm/yyyy")
        workbook.close()

    def test_dashboard_type_filter_is_preserved_in_export(self):
        Equipo.objects.create(
            codigo="EQ-MON-1",
            nombre="MONITOR",
            estado="FUNCIONAL",
        )
        Equipo.objects.create(
            codigo="EQ-LAP-1",
            nombre="LAPTOP",
            estado="FUNCIONAL",
        )

        response = self.client.get("/inventario/?q=MONITOR")

        self.assertContains(
            response,
            'href="/inventario/exportar/?q=MONITOR"',
        )
        exportacion = self.client.get("/inventario/exportar/?q=MONITOR")
        self.assertIn(
            'filename="inventario-monitor.xlsx"',
            exportacion["Content-Disposition"],
        )
        from openpyxl import load_workbook

        workbook = load_workbook(BytesIO(exportacion.content), read_only=True)
        sheet = workbook["Inventario"]
        rows = list(sheet.iter_rows(min_row=2, values_only=True))
        workbook.close()

        self.assertEqual([row[0] for row in rows], ["EQ-MON-1"])
        self.assertEqual(rows[0][1], "MONITOR")

    def test_export_filename_uses_a_safe_filter_slug(self):
        response = self.client.get(
            "/inventario/exportar/?q=Calidad%20M%C3%A9dica%2FEquipo"
        )

        self.assertIn(
            'filename="inventario-calidad-medica-equipo.xlsx"',
            response["Content-Disposition"],
        )

    def test_importing_filtered_export_only_updates_included_equipment(self):
        equipo_filtrado = Equipo.objects.create(
            codigo="EQ-MON-EDIT",
            nombre="MONITOR",
            marca="Marca anterior",
            estado="FUNCIONAL",
        )
        equipo_no_filtrado = Equipo.objects.create(
            codigo="EQ-LAP-KEEP",
            nombre="LAPTOP",
            marca="Marca intacta",
            estado="FUNCIONAL",
        )

        exportacion = self.client.get("/inventario/exportar/?q=MONITOR")
        from openpyxl import load_workbook

        libro = load_workbook(BytesIO(exportacion.content))
        hoja = libro["Inventario"]
        hoja["G2"] = "Marca actualizada"
        contenido = BytesIO()
        libro.save(contenido)
        libro.close()
        archivo = SimpleUploadedFile(
            "inventario-filtrado.xlsx",
            contenido.getvalue(),
            content_type=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
        )

        response = self.client.post(
            "/inventario/importar/",
            {"archivo": archivo},
        )

        self.assertRedirects(response, "/inventario/")
        equipo_filtrado.refresh_from_db()
        equipo_no_filtrado.refresh_from_db()
        self.assertEqual(equipo_filtrado.marca, "Marca actualizada")
        self.assertEqual(equipo_no_filtrado.marca, "Marca intacta")

    def test_import_upload_updates_inventory(self):
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Inventario"
        sheet.append(["Código", "Nombre", "D.Ampli.", "Situación patrimonial"])
        sheet.append(["EQ-UPLOAD", "Equipo desde Excel", "Detalle", "FUNCIONAL"])
        contenido = BytesIO()
        workbook.save(contenido)
        archivo = SimpleUploadedFile(
            "inventario.xlsx",
            contenido.getvalue(),
            content_type=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
        )

        response = self.client.post(
            "/inventario/importar/",
            {"archivo": archivo},
        )

        self.assertRedirects(response, "/inventario/")
        equipo = Equipo.objects.get(codigo="EQ-UPLOAD")
        self.assertEqual(equipo.ampliacion, "Detalle")

    def test_admin_labels_ampliacion_as_descripcion_ampliada(self):
        usuario = get_user_model().objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="test-password",
        )
        self.client.force_login(usuario)

        response = self.client.get("/admin/inventario/equipo/add/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Descripción ampliada")
        self.assertContains(response, "GFH (Descripción)")
        self.assertContains(response, "Situación patrimonial")
        self.assertContains(response, "Titular")

    def test_upload_equipment_photo(self):
        image_buffer = BytesIO()
        Image.new("RGB", (2, 2), color="blue").save(image_buffer, format="PNG")
        foto = SimpleUploadedFile(
            "equipo.png",
            image_buffer.getvalue(),
            content_type="image/png",
        )

        response = self.client.post(
            "/inventario/nuevo/",
            {
                "codigo": "EQ-FOTO",
                "nombre": "Equipo con foto",
                "estado": "FUNCIONAL",
                "fotos": [foto],
            },
        )

        self.assertRedirects(response, "/inventario/")
        foto = FotoEquipo.objects.get()
        ruta_foto = Path(foto.foto.path)
        self.assertTrue(ruta_foto.exists())
        foto.equipo.delete()
        self.assertFalse(ruta_foto.exists())

    def test_import_excel_includes_equipment_and_assignment(self):
        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "inventario.xlsx"
            workbook = Workbook()
            sheet = workbook.active
            sheet.title = "Inventario"
            sheet.append(
                ["Código", "Nombre", "Serie", "Marca", "Modelo", "Titular", "Servicio", "Estado"]
            )
            sheet.append(
                ["EQ-XLS", "Monitor", "S-2", "Marca", "M1", "Ana Pérez", "TI", "Funcional"]
            )
            workbook.save(file_path)

            call_command("importar_excel", str(file_path))

        equipo = Equipo.objects.get(codigo="EQ-XLS")
        titular = Titular.objects.get(nombre="Ana Pérez")
        self.assertEqual(equipo.servicio, "TI")
        self.assertTrue(
            Asignacion.objects.filter(
                equipo=equipo,
                titular=titular,
                activa=True,
            ).exists()
        )

    def test_import_excel_populates_full_inventory_columns(self):
        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "inventario.xlsx"
            workbook = Workbook()
            sheet = workbook.active
            sheet.title = "Inventario"
            sheet.append(
                [
                    "Código",
                    "Nombre",
                    "D.Ampli.",
                    "Serie",
                    "Número de teléfono",
                    "Extensión",
                    "Marca",
                    "Modelo",
                    "GFH (Cód.)",
                    "GFH (Descripción)",
                    "Área (Cód.)",
                    "Área (Descripción)",
                    "Fecha puesta en servicio",
                    "Modo de incorporación",
                    "Situación patrimonial",
                    "Titular",
                    "Naturaleza patrimonial",
                    "Servicio",
                ]
            )
            sheet.append(
                [
                    "EQ-COMPLETO",
                    "Equipo de prueba",
                    "PORTÁTIL",
                    "SER-123",
                    "3001234567",
                    "101",
                    "Marca",
                    "Modelo",
                    "17",
                    "SERVICIOS GENERALES",
                    "A-10",
                    "ALMACÉN",
                    datetime(2023, 12, 4),
                    "COMPRA",
                    "FUNCIONAL",
                    "Ana Pérez",
                    "GUÍA DE DOTACIÓN",
                    "Almacén piso 2",
                ]
            )
            workbook.save(file_path)

            call_command("importar_excel", str(file_path))

        equipo = Equipo.objects.get(codigo="EQ-COMPLETO")
        self.assertEqual(equipo.ampliacion, "PORTÁTIL")
        self.assertEqual(equipo.numero_telefono, "3001234567")
        self.assertEqual(equipo.extension, "101")
        self.assertEqual(equipo.gfh_codigo, "17")
        self.assertEqual(equipo.area_codigo, "A-10")
        self.assertEqual(
            equipo.fecha_puesta_en_servicio.isoformat(),
            "2023-12-04",
        )
        self.assertEqual(equipo.modo_incorporacion, "COMPRA")
        self.assertEqual(equipo.naturaleza_patrimonial, "GUÍA DE DOTACIÓN")
        self.assertTrue(
            Asignacion.objects.filter(
                equipo=equipo,
                titular__nombre="Ana Pérez",
                activa=True,
            ).exists()
        )

    def test_import_excel_maps_situation_and_generates_missing_code(self):
        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "inventario.xlsx"
            workbook = Workbook()
            sheet = workbook.active
            sheet.title = "Inventario"
            sheet.append(["Código", "Nombre", "Situación patrimonial"])
            sheet.append([None, "Monitor", "FUNCIONAL"])
            workbook.save(file_path)

            call_command("importar_excel", str(file_path))

        equipo = Equipo.objects.get()
        self.assertEqual(equipo.codigo, "SIN-CODIGO-FILA-2")
        self.assertEqual(equipo.estado, "FUNCIONAL")

    def test_import_excel_reports_missing_file(self):
        with self.assertRaisesMessage(CommandError, "No se encontró el archivo"):
            call_command("importar_excel", "archivo-inexistente.xlsx")

    def test_dashboard_and_equipment_form_render(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/inventario/nuevo/").status_code, 200)

# Create your tests here.
