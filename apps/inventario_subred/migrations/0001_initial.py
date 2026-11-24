from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="SubredEquipo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("codigo", models.CharField(max_length=50, unique=True)),
                ("nombre", models.CharField(max_length=150)),
                ("ampliacion", models.CharField(blank=True, max_length=150, verbose_name="Descripción ampliada")),
                ("serie", models.CharField(blank=True, max_length=150)),
                ("numero_telefono", models.CharField(blank=True, max_length=50)),
                ("extension", models.CharField(blank=True, max_length=30)),
                ("marca", models.CharField(blank=True, max_length=100)),
                ("modelo", models.CharField(blank=True, max_length=100)),
                ("gfh_codigo", models.CharField(blank=True, max_length=50)),
                ("gfh_descripcion", models.CharField(blank=True, max_length=255)),
                ("area_codigo", models.CharField(blank=True, max_length=50)),
                ("area_descripcion", models.CharField(blank=True, max_length=255)),
                ("fecha_puesta_en_servicio", models.DateField(blank=True, null=True)),
                ("modo_incorporacion", models.CharField(blank=True, max_length=100)),
                ("servicio", models.CharField(blank=True, max_length=150)),
                ("naturaleza_patrimonial", models.CharField(blank=True, max_length=100)),
                ("estado", models.CharField(choices=[("FUNCIONAL", "Funcional"), ("MANTENIMIENTO", "Mantenimiento"), ("DAÑADO", "Dañado"), ("BAJA", "Baja")], default="FUNCIONAL", max_length=20)),
                ("observaciones", models.TextField(blank=True)),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="FotoSubredEquipo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("foto", models.ImageField(upload_to="subred/")),
                ("fecha_carga", models.DateTimeField(auto_now_add=True)),
                ("equipo", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="fotos", to="inventario_subred.subredequipo")),
            ],
        ),
    ]
