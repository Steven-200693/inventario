import unicodedata
from datetime import date, datetime
from zipfile import BadZipFile

from django.core.management.base import CommandError
from django.db import transaction
from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException

from .models import SubredEquipo


def normalizar(valor):
    texto = str(valor or "").strip().casefold()
    return "".join(
        caracter
        for caracter in unicodedata.normalize("NFKD", texto)
        if not unicodedata.combining(caracter)
    )


def importar_libro_excel(archivo):
    try:
        archivo.seek(0)
        libro = load_workbook(archivo, read_only=True, data_only=True)
    except (OSError, BadZipFile, InvalidFileException) as exc:
        raise CommandError(f"No se pudo abrir el archivo Excel: {exc}") from exc

    try:
        if "Inventario" not in libro.sheetnames:
            raise CommandError(
                "No existe la hoja 'Inventario'. "
                f"Hojas disponibles: {', '.join(libro.sheetnames)}"
            )

        filas = libro["Inventario"].iter_rows(values_only=True)
        encabezados = next(filas, None)
        if not encabezados:
            raise CommandError("La hoja está vacía.")

        columnas = {
            normalizar(encabezado): indice
            for indice, encabezado in enumerate(encabezados)
            if encabezado is not None
        }
        if "estado" not in columnas and "situacion patrimonial" in columnas:
            columnas["estado"] = columnas["situacion patrimonial"]
        if "codigo" not in columnas or "nombre" not in columnas:
            raise CommandError("Faltan las columnas requeridas: Código y Nombre.")

        campos = {
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

        creados = existentes = 0
        with transaction.atomic():
            for numero_fila, fila in enumerate(filas, start=2):
                if not fila or all(celda is None for celda in fila):
                    continue
                codigo = valor(fila, "codigo")
                nombre = valor(fila, "nombre")
                if not codigo or not nombre:
                    raise CommandError(
                        f"La fila {numero_fila} debe incluir Código y Nombre."
                    )

                estado = normalizar(valor(fila, "estado")) or "funcional"
                if estado not in estados:
                    raise CommandError(
                        f"Estado no válido en la fila {numero_fila}: "
                        f"{valor(fila, 'estado')}"
                    )

                defaults = {
                    campo_modelo: valor(fila, campo_excel)
                    for campo_excel, campo_modelo in campos.items()
                    if campo_excel in columnas
                }
                defaults.update({"nombre": nombre, "estado": estados[estado]})

                indice_fecha = columnas.get("fecha puesta en servicio")
                if indice_fecha is not None and indice_fecha < len(fila):
                    fecha_valor = fila[indice_fecha]
                    if isinstance(fecha_valor, datetime):
                        defaults["fecha_puesta_en_servicio"] = fecha_valor.date()
                    elif isinstance(fecha_valor, date):
                        defaults["fecha_puesta_en_servicio"] = fecha_valor

                _, creado = SubredEquipo.objects.update_or_create(
                    codigo=codigo,
                    defaults=defaults,
                )
                creados += int(creado)
                existentes += int(not creado)

        return {"creados": creados, "existentes": existentes}
    finally:
        libro.close()
