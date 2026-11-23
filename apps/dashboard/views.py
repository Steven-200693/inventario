import unicodedata

from django.db.models import Count
from django.shortcuts import render

from apps.asignaciones.models import Asignacion
from apps.inventario.models import Equipo
from apps.titulares.models import Titular


ICONOS_EQUIPO = {
    "monitor": "monitor",
    "equipo de computo": "desktop",
    "celular": "mobile",
    "telefono basico": "phone",
    "tablet": "tablet",
    "portatil especial": "laptop",
    "televisor": "tv",
    "telefono ejecutivo": "phone",
    "equipo de proyeccion multimedia con soporte": "projector",
    "impresora zebra": "printer",
    "telon": "screen",
}


def normalizar_nombre(nombre):
    return "".join(
        caracter
        for caracter in unicodedata.normalize("NFKD", nombre.casefold())
        if not unicodedata.combining(caracter)
    )


def dashboard(request):
    total_equipos = Equipo.objects.count()
    equipos_por_tipo = Equipo.objects.values("nombre").annotate(
        total=Count("id"),
    ).order_by("-total", "nombre")
    tipos_equipo = [
        {
            **item,
            "porcentaje": (
                round(item["total"] * 100 / total_equipos, 1)
                if total_equipos
                else 0
            ),
            "icono": ICONOS_EQUIPO.get(
                normalizar_nombre(item["nombre"]),
                "device",
            ),
        }
        for item in equipos_por_tipo
    ]
    total_activos = Equipo.objects.filter(estado="FUNCIONAL").count()

    return render(
        request,
        "dashboard/inicio.html",
        {
            "total_equipos": total_equipos,
            "total_titulares": Titular.objects.count(),
            "total_asignaciones": Asignacion.objects.filter(activa=True).count(),
            "total_activos": total_activos,
            "porcentaje_activos": (
                round(total_activos * 100 / total_equipos, 1)
                if total_equipos
                else 0
            ),
            "tipos_equipo": tipos_equipo,
        },
    )
