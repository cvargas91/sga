# Generated by Django 4.0.3 on 2022-09-08 04:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('academica', '0013_alter_mallaelectiva_semestre_and_more'),
        ('curso', '0010_alter_curso_creditos_alter_curso_estado_curso_and_more'),
        ('matricula', '0031_alter_gratuidadestudiante_tiene_gratuidad'),
    ]

    operations = [
        migrations.AlterField(
            model_name='arancelestudiante',
            name='monto',
            field=models.IntegerField(help_text='corresponde al monto final que debe pagar el estudiante, considerando beneficios'),
        ),
        migrations.AlterField(
            model_name='arancelestudiante',
            name='pago_cuotas',
            field=models.BooleanField(default=False, help_text='define si este arancel se está pagando con pagaré (true) o al contado (false)'),
        ),
        migrations.AlterField(
            model_name='arancelestudiante',
            name='periodo_matricula',
            field=models.ForeignKey(blank=True, help_text='se debe guardar el periodo para conocer las fechas límites asociadas', null=True, on_delete=django.db.models.deletion.PROTECT, to='matricula.periodoprocesomatricula'),
        ),
        migrations.AlterField(
            model_name='matriculaestudiante',
            name='monto_final',
            field=models.IntegerField(help_text='corresponde al monto final que debe pagar el estudiante, considerando beneficios'),
        ),
        migrations.AlterField(
            model_name='matriculaestudiante',
            name='periodo_matricula',
            field=models.ForeignKey(blank=True, help_text='se debe guardar el periodo para conocer las fechas límites asociadas', null=True, on_delete=django.db.models.deletion.PROTECT, to='matricula.periodoprocesomatricula'),
        ),
        migrations.AlterField(
            model_name='periodoprocesomatricula',
            name='planes',
            field=models.ManyToManyField(blank=True, help_text='si no se deja en blanco, solo los planes asociados se pueden matricular\n                    en este periodo', to='academica.plan'),
        ),
        migrations.AlterField(
            model_name='postulantedefinitivo',
            name='PACE',
            field=models.BooleanField(default=False, help_text='define si es que el estudiante proviene de un programa PACE,\n                    independiente de su vía de ingreso'),
        ),
        migrations.AlterField(
            model_name='postulantedefinitivo',
            name='numero_demre',
            field=models.CharField(help_text='Este número se utiliza como la contraseña del estudiante para\n                    ingresar al portal de matrícula', max_length=50),
        ),
        migrations.AlterField(
            model_name='postulantedefinitivo',
            name='preseleccionado_gratuidad',
            field=models.BooleanField(default=False, help_text='Atención: marcar esta opción resultará en un costo de matrícula y\n                    arancel de $0 para el estudiante'),
        ),
        migrations.AlterField(
            model_name='procesomatricula',
            name='activo',
            field=models.BooleanField(help_text='define qué proceso está en progreso, independiente del periodo activo'),
        ),
        migrations.AlterField(
            model_name='procesomatricula',
            name='fecha_vigencia',
            field=models.DateField(help_text='fecha hasta la cuál es válida una matrícula de este proceso, para validar\n        que solo estudiantes matriculados puedan realizar inscripción académica y otras acciones\n        similares que puedan ocurrir el año siguiente de la matrícula'),
        ),
        migrations.AlterField(
            model_name='procesomatricula',
            name='periodo_ingreso',
            field=models.ForeignKey(help_text='periodo de ingreso para los estudiantes nuevos de este proceso de matrícula', on_delete=django.db.models.deletion.PROTECT, to='curso.periodo'),
        ),
    ]
