from django.urls import path

from . import views

urlpatterns = [
    path("", views.lista_asignaciones, name="asignaciones"),
    path("nueva/", views.crear_asignacion, name="crear_asignacion"),
    path("editar/<int:pk>/", views.editar_asignacion, name="editar_asignacion"),
    path(
        "eliminar/<int:pk>/",
        views.eliminar_asignacion,
        name="eliminar_asignacion",
    ),
]
