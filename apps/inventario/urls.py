from django.urls import path

from . import views

urlpatterns = [
    path("", views.lista_equipos, name="equipos"),
    path("exportar/", views.exportar_excel, name="exportar_excel"),
    path("importar/", views.importar_excel, name="importar_excel"),
    path("nuevo/", views.crear_equipo, name="crear_equipo"),
    path("editar/<int:pk>/", views.editar_equipo, name="editar_equipo"),
    path("eliminar/<int:pk>/", views.eliminar_equipo, name="eliminar_equipo"),
]
