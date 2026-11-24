from django.urls import path

from . import views

urlpatterns = [
    path("", views.lista_equipos, name="subred_equipos"),
    path("exportar/", views.exportar_excel, name="subred_exportar_excel"),
    path("importar/", views.importar_excel, name="subred_importar_excel"),
    path("nuevo/", views.crear_equipo, name="subred_crear_equipo"),
    path("editar/<int:pk>/", views.editar_equipo, name="subred_editar_equipo"),
    path("eliminar/<int:pk>/", views.eliminar_equipo, name="subred_eliminar_equipo"),
]
