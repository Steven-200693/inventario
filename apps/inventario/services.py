import unicodedata
from datetime import date, datetime
from zipfile import BadZipFile

from django.core.management.base import CommandError
from django.db import transaction
from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException

from apps.asignaciones.models import Asignacion
from apps.titulares.models import Titular
from .models import Equipo


def normalizar(valor):
    texto = str(valor or "").strip().casefold()
    return "".join(
        caracter
        for caracter in unicodedata.normalize("NFKD", texto)
        if not unicodedata.combining(caracter)
    )


def importar_libro_excel(archivo, nombre_hoja="Inventario"):
    try:
        archivo.seek(0)
        libro = load_workbook(archivo, read_only=True, data_only=True)
    except (OSError, BadZipFile, InvalidFileException) as exc:
        raise CommandError(f"No se pudo abrir el archivo Excel: {exc}") from exc

    try:
        if nombre_hoja not in libro.sheetnames:
            raise CommandError(
                f"No existe la hoja '{nombre_hoja}'. "
                f"Hojas disponibles: {', '.join(libro.sheetnames)}"
            )

        filas = libro[nombre_hoja].iter_rows(values_only=True)
        encabezados = next(filas, None)
        if not encabezados:
            raise CommandError("La hoja está vacía o no contiene encabezados.")

        columnas = {
            normalizar(encabezado): indice
            for indice, encabezado in enumerate(encabezados)
            if encabezado is not None
        }
        if "estado" not in columnas and "situacion patrimonial" in columnas:
            columnas["estado"] = columnas["situacion patrimonial"]
        faltantes = [
            campo for campo in ("codigo", "nombre") if campo not in columnas
        ]
        if faltantes:
            raise CommandError(
                "Faltan columnas requeridas: " + ", ".join(faltantes)
            )

        campos_excel = {
            "d.ampli.": "ampliacion",
            "descripcion ampliada": "ampliacion",
            "serie": "serie",
            "numero de telefono": "numero_telefono",
            "extension": "extension",
            "marca": "marca",
            "modelo": "modelo",
            "gfh (cod.)": "gfh_codigo",
            "gfh (descripcion)": "gfh_descripcion",
            "area (cod.)": "area_codigo",
            "area (descripcion)": "area_descripcion",
            "modo de incorporacion": "modo_incorporacion",
            "naturaleza patrimonial": "naturaleza_patrimonial",
            "servicio": "servicio",
        }
        estados = {
            "funcional": "FUNCIONAL",
            "mantenimiento": "MANTENIMIENTO",
            "danado": "DAÑADO",
            "baja": "BAJA",
        }

        def valor(fila, campo):
            indice = columnas.get(campo)
            if indice is None or indice >= len(fila) or fila[indice] is None:
                return ""
            return str(fila[indice]).strip()

        def fecha_servicio(fila, numero_fila):
            indice = columnas.get("fecha puesta en servicio")
            if indice is None or indice >= len(fila) or fila[indice] is None:
                return None
            valor_fecha = fila[indice]
            if isinstance(valor_fecha, datetime):
                return valor_fecha.date()
            if isinstance(valor_fecha, date):
                return valor_fecha
            try:
                return date.fromisoformat(str(valor_fecha).strip())
            except ValueError as exc:
                raise CommandError(
                    f"Fecha puesta en servicio no válida en la fila {numero_fila}: "
                    f"{valor_fecha}"
                ) from exc

        creados = 0
        existentes = 0
        asignaciones_creadas = 0
        codigos_generados = 0

        with transaction.atomic():
            for numero_fila, fila in enumerate(filas, start=2):
                if not fila or all(celda is None for celda in fila):
                    continue

                codigo = valor(fila, "codigo")
                nombre = valor(fila, "nombre")
                if not nombre:
                    raise CommandError(
                        f"La fila {numero_fila} debe incluir Nombre."
                    )
                if not codigo:
                    codigo = f"SIN-CODIGO-FILA-{numero_fila}"
                    codigos_generados += 1

                estado = normalizar(valor(fila, "estado")) or "funcional"
                if estado not in estados:
                    raise CommandError(
                        f"Estado no válido en la fila {numero_fila}: "
                        f"{valor(fila, 'estado')}"
                    )

                defaults = {
                    campo_modelo: valor(fila, campo_excel)
                    for campo_excel, campo_modelo in campos_excel.items()
                    if campo_excel in columnas
                }
                defaults.update({"nombre": nombre, "estado": estados[estado]})
                if "fecha puesta en servicio" in columnas:
                    defaults["fecha_puesta_en_servicio"] = fecha_servicio(
                        fila,
                        numero_fila,
                    )

                equipo, creado = Equipo.objects.update_or_create(
                    codigo=codigo,
                    defaults=defaults,
                )
                creados += int(creado)
                existentes += int(not creado)

                nombre_titular = valor(fila, "titular")
                if nombre_titular:
                    titular, _ = Titular.objects.get_or_create(
                        nombre=nombre_titular,
                    )
                    _, asignacion_creada = Asignacion.objects.get_or_create(
                        equipo=equipo,
                        titular=titular,
                        activa=True,
                    )
                    asignaciones_creadas += int(asignacion_creada)

        return {
            "creados": creados,
            "existentes": existentes,
            "asignaciones_creadas": asignaciones_creadas,
            "codigos_generados": codigos_generados,
        }
    finally:
        libro.close()
