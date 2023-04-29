from rest_framework import serializers

from persona.models import Persona
from matricula.models import MatriculaEstudiante


class PersonaUcampusSerializer(serializers.ModelSerializer):
    direccion_comuna = serializers.StringRelatedField(read_only=True)
    rut = serializers.CharField(source='numero_documento')
    sexo = serializers.SerializerMethodField()

    class Meta:
        model = Persona
        fields = [
            'rut', 'nombres', 'apellido1', 'apellido2', 'mail_institucional',
            'mail_secundario', 'fecha_nacimiento', 'sexo', 'direccion_calle', 'direccion_numero',
            'direccion_block', 'direccion_depto', 'direccion_villa', 'direccion_comuna',
        ]

    sexos = {
        0: 'F',
        1: 'M',
        2: '-',
    }

    def get_sexo(self, obj):
        return self.sexos[obj.sexo]


class MatriculaUcampusSerializer(serializers.ModelSerializer):
    rut = serializers.CharField(source='estudiante.persona.numero_documento', read_only=True)
    id_carrera = serializers.IntegerField(source='estudiante.plan.carrera.id', read_only=True)
    carrera = serializers.StringRelatedField(source='estudiante.plan.carrera', read_only=True)

    año = serializers.IntegerField(source='proceso_matricula.ano', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    via_ingreso = serializers.CharField(source='estudiante.via_ingreso.nombre', read_only=True)
    año_ingreso = serializers.CharField(source='estudiante.periodo_ingreso.ano', read_only=True)

    class Meta:
        model = MatriculaEstudiante
        fields = [
            'rut', 'id_carrera', 'carrera', 'año', 'estado', 'estado_display', 'via_ingreso',
            'año_ingreso',
        ]
