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

from .forms import ImportarExcelForm, SubredEquipoForm
from .models import FotoSubredEquipo, SubredEquipo
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


def _equipos_filtrados(busqueda, estado=""):
    equipos = SubredEquipo.objects.all()
    if estado:
        equipos = equipos.filter(estado=estado)
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
        ).distinct()
    return equipos.order_by("codigo")


def lista_equipos(request):
    busqueda = request.GET.get("q", "").strip()
    estado = request.GET.get("estado", "").strip().upper()
    equipos = _equipos_filtrados(busqueda, estado).prefetch_related("fotos")
    return render(
        request,
        "inventario_subred/lista.html",
        {"equipos": equipos, "busqueda": busqueda, "estado": estado},
    )


def exportar_excel(request):
    libro = Workbook()
    hoja = libro.active
    hoja.title = "Inventario Subred"
    hoja.append(ENCABEZADOS_EXCEL)
    hoja.freeze_panes = "A2"

    for celda in hoja[1]:
        celda.fill = PatternFill(fill_type="solid", fgColor="1F4E78")
        celda.font = Font(bold=True, color="FFFFFF")
        celda.alignment = Alignment(horizontal="center", vertical="center")

    busqueda = request.GET.get("q", "").strip()
    estado = request.GET.get("estado", "").strip().upper()
    ids_visibles = [
        int(valor)
        for valor in request.GET.get("ids", "").split(",")
        if valor.strip().isdigit()
    ]
    equipos = (
        SubredEquipo.objects.filter(pk__in=ids_visibles)
        if ids_visibles
        else _equipos_filtrados(busqueda, estado)
    )

    for equipo in equipos:
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
            "",
            equipo.naturaleza_patrimonial,
            equipo.servicio,
        )
        valores = tuple(
            ILLEGAL_CHARACTERS_RE.sub("", valor)
            if isinstance(valor, str)
            else valor
            for valor in valores
        )
        hoja.append(valores)
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
        hoja.column_dimensions[columna[0].column_letter].width = min(ancho + 2, 255)

    salida = BytesIO()
    libro.save(salida)
    salida.seek(0)
    respuesta = HttpResponse(
        salida.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    sufijo = slugify(re.sub(r"[\W_]+", " ", busqueda))
    nombre = f"inventario-subred-{sufijo}.xlsx" if sufijo else "inventario-subred.xlsx"
    respuesta["Content-Disposition"] = f'attachment; filename="{nombre}"'
    return respuesta


def crear_equipo(request):
    form = SubredEquipoForm(
        request.POST if request.method == "POST" else None,
        request.FILES if request.method == "POST" else None,
    )
    if request.method == "POST" and form.is_valid():
        equipo = form.save()
        for archivo in form.cleaned_data["fotos"]:
            FotoSubredEquipo.objects.create(equipo=equipo, foto=archivo)
        messages.success(request, "El equipo se creó correctamente en Inventario Subred.")
        return redirect("subred_equipos")
    return render(request, "inventario_subred/formulario.html", {"form": form})


def editar_equipo(request, pk):
    equipo = get_object_or_404(SubredEquipo, pk=pk)
    form = SubredEquipoForm(
        request.POST if request.method == "POST" else None,
        request.FILES if request.method == "POST" else None,
        instance=equipo,
    )
    if request.method == "POST" and form.is_valid():
        equipo = form.save()
        for archivo in form.cleaned_data["fotos"]:
            FotoSubredEquipo.objects.create(equipo=equipo, foto=archivo)
        messages.success(request, "El equipo se actualizó correctamente.")
        return redirect("subred_equipos")
    return render(
        request,
        "inventario_subred/formulario.html",
        {"form": form, "equipo": equipo},
    )


def eliminar_equipo(request, pk):
    equipo = get_object_or_404(SubredEquipo, pk=pk)
    if request.method == "POST":
        equipo.delete()
        messages.success(request, "El equipo se eliminó correctamente.")
        return redirect("subred_equipos")
    return render(
        request,
        "inventario_subred/confirmar_eliminacion.html",
        {"objeto": equipo},
    )


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
                f"{resumen['creados']} equipos nuevos y "
                f"{resumen['existentes']} actualizados.",
            )
            return redirect("subred_equipos")
    return render(request, "inventario_subred/importar.html", {"form": form})
