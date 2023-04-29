from django.contrib.auth.models import Group
from rest_framework import serializers

from .models import Persona, Estudiante, EstadoEstudiante, HistorialEstadoEstudiante


class UsuarioSerializer(serializers.ModelSerializer):
    email = serializers.CharField(source='mail_institucional', read_only=True)
    nombre = serializers.CharField(source='nombre_completo', read_only=True)
    grupos = serializers.SlugRelatedField(
        source='user.groups', slug_field='name', many=True, read_only=True)

    class Meta:
        model = Persona
        fields = [
            'id', 'email', 'nombre', 'foto', 'grupos',
        ]


class PersonaSerializer(serializers.ModelSerializer):
    grupos = serializers.StringRelatedField(source='user.groups', many=True, read_only=True)
    grupos_ids = serializers.PrimaryKeyRelatedField(
        source='user.groups', many=True, queryset=Group.objects.all())

    class Meta:
        model = Persona
        fields = [
            'id', 'tipo_identificacion', 'numero_documento', 'digito_verificador',
            'mail_institucional', 'nombre_completo', 'nombres', 'apellido1', 'apellido2',
            'fecha_nacimiento', 'grupos', 'grupos_ids', 'acepta_contrato',
        ]

    def update(self, instance, validated_data):
        grupos = validated_data.pop('user')['groups']
        instance.user.groups.set(grupos)

        return super().update(instance, validated_data)


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name']


class PerfilPrivadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Persona
        fields = [
            'id', 'tipo_identificacion', 'numero_documento', 'digito_verificador',
            'mail_institucional', 'nombre_completo', 'fecha_nacimiento',

            'foto', 'genero', 'nombre_social',
            'mail_secundario', 'telefono_fijo', 'telefono_celular', 'biografia',

            'direccion_calle', 'direccion_numero', 'direccion_block', 'direccion_depto',
            'direccion_villa', 'direccion_comuna',

            'emergencia_nombre', 'emergencia_parentezco', 'emergencia_telefono_fijo',
            'emergencia_telefono_laboral', 'emergencia_telefono_celular', 'emergencia_mail',
        ]
        extra_kwargs = {
            'tipo_identificacion': {'read_only': True},
            'numero_documento': {'read_only': True},
            'digito_verificador': {'read_only': True},
            'mail_institucional': {'read_only': True},
            'fecha_nacimiento': {'read_only': True},
            'foto': {'read_only': True},
        }


class PerfilPublicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Persona
        fields = [
            'id', 'mail_institucional', 'nombre_completo', 'fecha_nacimiento', 'foto', 'biografia',
        ]
        extra_kwargs = {
            'mail_institucional': {'read_only': True},
            'fecha_nacimiento': {'read_only': True},
            'foto': {'read_only': True},
            'biografia': {'read_only': True},
        }


class FotoPerfilSerializer(serializers.ModelSerializer):
    class Meta:
        model = Persona
        fields = ['foto']


class PersonaCortaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Persona
        fields = [
            'id', 'nombre_completo', 'foto', 'documento',
        ]


class PlanesEstudienteSerializer(serializers.ModelSerializer):
    plan_nombre = serializers.StringRelatedField(source='plan', read_only=True)
    estado_nombre = serializers.CharField(source='estado_estudiante.nombre', read_only=True)
    periodo_ingreso_nombre = serializers.StringRelatedField(
        source='periodo_ingreso', read_only=True)
    periodo_egreso_nombre = serializers.StringRelatedField(source='periodo_egreso', read_only=True)

    class Meta:
        model = Estudiante
        fields = [
            'id', 'plan', 'plan_nombre', 'estado_estudiante', 'estado_nombre', 'periodo_ingreso',
            'periodo_egreso', 'periodo_ingreso_nombre', 'periodo_egreso_nombre',
        ]


class MonitoreoEstudiantesSerializer(serializers.ModelSerializer):
    planes = PlanesEstudienteSerializer(source='estudiantes', many=True, read_only=True)

    class Meta:
        model = Persona
        fields = [
            'id', 'numero_documento', 'mail_institucional', 'nombres', 'apellido1', 'apellido2',
            'foto', 'planes',
        ]


class EstadoEstudianteSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstadoEstudiante
        fields = [
            'id', 'nombre',
        ]


class HistorialEstadoEstudianteSerializer(serializers.ModelSerializer):
    estado_nombre = serializers.CharField(source='estado_estudiante.nombre', read_only=True)

    class Meta:
        model = HistorialEstadoEstudiante
        fields = [
            'id', 'estudiante', 'estado_estudiante', 'estado_nombre', 'periodo',
        ]


class EstudianteSerializer(serializers.ModelSerializer):
    plan_nombre = serializers.StringRelatedField(source='plan', read_only=True)
    estado_nombre = serializers.CharField(source='estado_estudiante.nombre', read_only=True)
    via_ingreso = serializers.CharField(source='via_ingreso.nombre', read_only=True)

    class Meta:
        model = Estudiante
        fields = [
            'id', 'plan', 'plan_nombre', 'estado_estudiante', 'estado_nombre', 'periodo_ingreso',
            'periodo_egreso', 'periodo_ingreso_uaysen', 'via_ingreso',
        ]


class ResumenAcademicoSerializer(serializers.ModelSerializer):
    plan = serializers.StringRelatedField(read_only=True)
    estado_estudiante = serializers.StringRelatedField(read_only=True)
    periodo_ingreso = serializers.StringRelatedField(read_only=True)
    periodo_egreso = serializers.StringRelatedField(read_only=True)
    asignaturas_cursadas = serializers.SerializerMethodField()
    asignaturas_aprobadas = serializers.SerializerMethodField()
    asignaturas_actuales = serializers.SerializerMethodField()
    promedio_notas = serializers.SerializerMethodField()

    class Meta:
        model = Estudiante
        fields = [
            'id', 'plan', 'estado_estudiante', 'periodo_ingreso', 'periodo_egreso',
            'asignaturas_cursadas', 'asignaturas_aprobadas', 'asignaturas_actuales',
            'promedio_notas',
        ]

    def get_asignaturas_cursadas(self, obj):
        return obj.cursos.filter(estado__completado=True).count()

    def get_asignaturas_aprobadas(self, obj):
        return obj.cursos.filter(estado__completado=True, estado__aprobado=True).count()

    def get_asignaturas_actuales(self, obj):
        return obj.cursos.filter(estado__nombre='Inscrito').count()

    def get_promedio_notas(self, obj):
        return 7.1
