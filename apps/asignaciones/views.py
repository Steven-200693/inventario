from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AsignacionForm
from .models import Asignacion


def lista_asignaciones(request):
    asignaciones = Asignacion.objects.select_related(
        "equipo",
        "titular",
    ).order_by("-fecha_asignacion", "-pk")
    return render(
        request,
        "asignaciones/lista.html",
        {"asignaciones": asignaciones},
    )


def crear_asignacion(request):
    form = AsignacionForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "La asignación se creó correctamente.")
        return redirect("asignaciones")
    return render(request, "asignaciones/formulario.html", {"form": form})


def editar_asignacion(request, pk):
    asignacion = get_object_or_404(Asignacion, pk=pk)
    form = AsignacionForm(
        request.POST if request.method == "POST" else None,
        instance=asignacion,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "La asignación se actualizó correctamente.")
        return redirect("asignaciones")
    return render(
        request,
        "asignaciones/formulario.html",
        {"form": form, "asignacion": asignacion},
    )


def eliminar_asignacion(request, pk):
    asignacion = get_object_or_404(Asignacion, pk=pk)
    if request.method == "POST":
        asignacion.delete()
        messages.success(request, "La asignación se eliminó correctamente.")
        return redirect("asignaciones")
    return render(
        request,
        "asignaciones/confirmar_eliminacion.html",
        {"objeto": asignacion},
    )
