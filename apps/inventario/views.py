import re
from datetime import date
from io import BytesIO

from django.contrib import messages
from django.core.management.base import CommandError
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from openpyxl import Workbook
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from openpyxl.styles import Alignment, Font, PatternFill

from apps.asignaciones.models import Asignacion
from apps.titulares.models import Titular
from .forms import EquipoForm, ImportarExcelForm
from .models import Equipo, FotoEquipo
from .services import importar_libro_excel


ENCABEZADOS_EXCEL = (
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
)


def _equipos_filtrados(busqueda):
    equipos = Equipo.objects.all()
    if busqueda:
        equipos = equipos.filter(
            Q(codigo__icontains=busqueda)
            | Q(nombre__icontains=busqueda)
            | Q(marca__icontains=busqueda)
            | Q(modelo__icontains=busqueda)
            | Q(serie__icontains=busqueda)
            | Q(servicio__icontains=busqueda)
            | Q(ampliacion__icontains=busqueda)
            | Q(numero_telefono__icontains=busqueda)
            | Q(extension__icontains=busqueda)
            | Q(gfh_codigo__icontains=busqueda)
            | Q(gfh_descripcion__icontains=busqueda)
            | Q(area_codigo__icontains=busqueda)
            | Q(area_descripcion__icontains=busqueda)
            | Q(modo_incorporacion__icontains=busqueda)
            | Q(naturaleza_patrimonial__icontains=busqueda)
            | Q(estado__icontains=busqueda)
            | Q(observaciones__icontains=busqueda)
            | Q(asignaciones__titular__nombre__icontains=busqueda)
        ).distinct()
    return equipos.order_by("codigo")


def exportar_excel(request):
    libro = Workbook()
    hoja = libro.active
    hoja.title = "Inventario"
    hoja.append(ENCABEZADOS_EXCEL)
    hoja.freeze_panes = "A2"

    for celda in hoja[1]:
        celda.fill = PatternFill(
            fill_type="solid",
            fgColor="1F4E78",
        )
        celda.font = Font(bold=True, color="FFFFFF")
        celda.alignment = Alignment(horizontal="center", vertical="center")

    busqueda = request.GET.get("q", "").strip()
    equipos = _equipos_filtrados(busqueda).prefetch_related(
        "asignaciones__titular",
    )
    for equipo in equipos:
        titulares = [
            asignacion.titular.nombre
            for asignacion in equipo.asignaciones.all()
            if asignacion.activa
        ] or [""]
        for titular in titulares:
            valores = (
                equipo.codigo,
                equipo.nombre,
                equipo.ampliacion,
                equipo.serie,
                equipo.numero_telefono,
                equipo.extension,
                equipo.marca,
                equipo.modelo,
                equipo.gfh_codigo,
                equipo.gfh_descripcion,
                equipo.area_codigo,
                equipo.area_descripcion,
                equipo.fecha_puesta_en_servicio,
                equipo.modo_incorporacion,
                equipo.estado,
                titular,
                equipo.naturaleza_patrimonial,
                equipo.servicio,
            )
            valores_limpios = tuple(
                ILLEGAL_CHARACTERS_RE.sub("", valor)
                if isinstance(valor, str)
                else valor
                for valor in valores
            )
            hoja.append(valores_limpios)
            for celda in hoja[hoja.max_row]:
                if isinstance(celda.value, str):
                    celda.data_type = "s"
                    celda.number_format = "@"
                elif isinstance(celda.value, date):
                    celda.number_format = "dd/mm/yyyy"

    hoja.auto_filter.ref = hoja.dimensions
    for columna in hoja.columns:
        ancho = max(
            len(str(celda.value)) if celda.value is not None else 0
            for celda in columna
        )
        letra_columna = columna[0].column_letter
        hoja.column_dimensions[letra_columna].width = min(ancho + 2, 255)

    salida = BytesIO()
    libro.save(salida)
    salida.seek(0)
    respuesta = HttpResponse(
        salida.getvalue(),
        content_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
    )
    sufijo_filtro = slugify(re.sub(r"[\W_]+", " ", busqueda))
    nombre_archivo = (
        f"inventario-{sufijo_filtro}.xlsx"
        if sufijo_filtro
        else "inventario.xlsx"
    )
    respuesta["Content-Disposition"] = (
        f'attachment; filename="{nombre_archivo}"'
    )
    return respuesta


def importar_excel(request):
    form = ImportarExcelForm(
        request.POST if request.method == "POST" else None,
        request.FILES if request.method == "POST" else None,
    )
    if request.method == "POST" and form.is_valid():
        try:
            resumen = importar_libro_excel(form.cleaned_data["archivo"])
        except CommandError as exc:
            form.add_error("archivo", str(exc))
        else:
            messages.success(
                request,
                "Importación completada: "
                f"{resumen['creados']} equipos nuevos, "
                f"{resumen['existentes']} actualizados y "
                f"{resumen['asignaciones_creadas']} asignaciones nuevas. "
                "Los registros existentes con el mismo código se actualizaron.",
            )
            if resumen["codigos_generados"]:
                messages.warning(
                    request,
                    f"Se generaron {resumen['codigos_generados']} códigos "
                    "provisionales para filas sin código.",
                )
            return redirect("equipos")

    return render(
        request,
        "inventario/importar.html",
        {"form": form},
    )


def lista_equipos(request):
    busqueda = request.GET.get("q", "").strip()
    equipos = _equipos_filtrados(busqueda).prefetch_related(
        "asignaciones__titular",
        "fotos",
    )
    return render(
        request,
        "inventario/lista.html",
        {"equipos": equipos, "busqueda": busqueda},
    )


def _guardar_fotos(equipo, files):
    for archivo in files:
        FotoEquipo.objects.create(equipo=equipo, foto=archivo)


def _guardar_titular(equipo, nombre):
    nombre = nombre.strip()
    if not nombre:
        return
    titular, _ = Titular.objects.get_or_create(nombre=nombre)
    Asignacion.objects.get_or_create(
        equipo=equipo,
        titular=titular,
        activa=True,
    )


def crear_equipo(request):
    form = EquipoForm(
        request.POST if request.method == "POST" else None,
        request.FILES if request.method == "POST" else None,
    )
    if request.method == "POST" and form.is_valid():
        equipo = form.save()
        _guardar_titular(equipo, form.cleaned_data["titular"])
        _guardar_fotos(equipo, form.cleaned_data["fotos"])
        messages.success(request, "El equipo se creó correctamente.")
        return redirect("equipos")
    return render(request, "inventario/formulario.html", {"form": form})


def editar_equipo(request, pk):
    equipo = get_object_or_404(Equipo, pk=pk)
    form = EquipoForm(
        request.POST if request.method == "POST" else None,
        request.FILES if request.method == "POST" else None,
        instance=equipo,
    )
    if request.method == "POST" and form.is_valid():
        equipo = form.save()
        _guardar_titular(equipo, form.cleaned_data["titular"])
        _guardar_fotos(equipo, form.cleaned_data["fotos"])
        messages.success(request, "El equipo se actualizó correctamente.")
        return redirect("equipos")
    return render(
        request,
        "inventario/formulario.html",
        {"form": form, "equipo": equipo},
    )


def eliminar_equipo(request, pk):
    equipo = get_object_or_404(Equipo, pk=pk)
    if request.method == "POST":
        equipo.delete()
        messages.success(request, "El equipo se eliminó correctamente.")
        return redirect("equipos")
    return render(request, "inventario/confirmar_eliminacion.html", {"objeto": equipo})
