from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.inventario.services import importar_libro_excel


class Command(BaseCommand):
    help = "Importa equipos desde un archivo Excel (.xlsx)."

    def add_arguments(self, parser):
        parser.add_argument("archivo", type=Path)
        parser.add_argument("--hoja", default="Inventario")

    def handle(self, *args, **options):
        archivo = options["archivo"]
        if not archivo.is_file():
            raise CommandError(f"No se encontró el archivo: {archivo}")

        with archivo.open("rb") as contenido:
            resumen = importar_libro_excel(contenido, options["hoja"])

        self.stdout.write(
            self.style.SUCCESS(
                "Importación completada: "
                f"{resumen['creados']} equipos nuevos, "
                f"{resumen['existentes']} actualizados y "
                f"{resumen['asignaciones_creadas']} asignaciones nuevas. "
                f"Códigos provisionales generados: "
                f"{resumen['codigos_generados']}."
            )
        )
