from rest_framework import serializers

from academica.serializers import PlanInfoSerializer
from pagare.serializers import PagareSerializer
from pagos.serializers import OrdenCompraSerializer

from persona.models import Persona, Estudiante
from persona.serializers import PersonaSerializer

from .models import (
    PeriodoProcesoMatricula, PostulanteDefinitivo,
    ArancelEstudiante, InhabilitantesMatricula, MatriculaEstudiante, PostulanteEducacionContinua,
)


class DatosContactoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Persona
        fields = [
            'id', 'nombre_social', 'genero', 'mail_secundario', 'telefono_fijo',
            'telefono_celular', 'nacionalidad', 'ciudad_origen',
            'direccion_calle', 'direccion_numero', 'direccion_block', 'direccion_depto',
            'direccion_villa', 'direccion_comuna', 'direccion_coyhaique',
            'emergencia_nombre', 'emergencia_parentezco', 'emergencia_telefono_fijo',
            'emergencia_telefono_laboral', 'emergencia_telefono_celular', 'emergencia_mail',
            'educontinua_cargo', 'educontinua_empresa', 'educontinua_mail_laboral',
            'autoriza_uso_imagen',
        ]


class PeriodoProcesoMatriculaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeriodoProcesoMatricula
        fields = [
            'id', 'proceso_matricula', 'descripcion', 'fecha_inicio', 'fecha_fin', 'publico',
        ]


class DetallesPeriodoProcesoMatriculaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeriodoProcesoMatricula
        fields = [
            'dcto_oportuno', 'fecha_entrega_pagare', 'fecha_pago_matricula', 'fecha_pago_arancel',
        ]


class PostulanteDefinitivoSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(source='persona.nombre', read_only=True)
    plan = PlanInfoSerializer()
    via_ingreso = serializers.CharField(source='via_ingreso.nombre', read_only=True)
    resultado_postulacion_display = serializers.CharField(
        source='get_resultado_postulacion_display', read_only=True)
    etapa_estudiante = serializers.IntegerField(source='etapa_actual', read_only=True)

    class Meta:
        model = PostulanteDefinitivo
        fields = [
            'id', 'persona', 'nombre', 'plan', 'via_ingreso', 'resultado_postulacion',
            'resultado_postulacion_display', 'posicion_lista', 'preseleccionado_gratuidad',
            'habilitado', 'acepta_vacante', 'estudiante', 'etapa_estudiante',
        ]


class ArancelEstudianteSerializer(serializers.ModelSerializer):
    orden_compra = OrdenCompraSerializer()
    pagare = PagareSerializer()
    periodo_matricula = DetallesPeriodoProcesoMatriculaSerializer()

    class Meta:
        model = ArancelEstudiante
        fields = [
            'id', 'proceso_matricula', 'estudiante', 'monto', 'tiene_beneficios',
            'beneficios_monto_total', 'descripcion_beneficios',
            'pago_cuotas', 'orden_compra', 'pagare', 'periodo_matricula',
        ]


class MatriculaEstudianteSerializer(serializers.ModelSerializer):
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    orden_compra = OrdenCompraSerializer()
    periodo_matricula = DetallesPeriodoProcesoMatriculaSerializer()

    class Meta:
        model = MatriculaEstudiante
        fields = [
            'id', 'proceso_matricula', 'estudiante', 'monto_final', 'tiene_beneficios',
            'beneficios_monto_total', 'descripcion_beneficios', 'estado', 'estado_display',
            'orden_compra', 'periodo_matricula',
        ]


class InhabilitantesMatriculaSerializer(serializers.ModelSerializer):
    class Meta:
        model = InhabilitantesMatricula
        fields = [
            'id', 'proceso_matricula', 'estudiante', 'tiene_deuda_finanzas',
            'tiene_deuda_biblioteca', 'comentario_finanzas', 'comentario_biblioteca',
        ]


class HistorialMatriculaEstudianteSerializer(serializers.ModelSerializer):
    periodo = serializers.PrimaryKeyRelatedField(
        source='proceso_matricula.periodo_ingreso', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = MatriculaEstudiante
        fields = [
            'id', 'periodo', 'estudiante', 'estado', 'estado_display',
        ]


class EstudianteAntiguoSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(source='persona.nombre', read_only=True)
    acepta_contrato = serializers.BooleanField(source='persona.acepta_contrato', read_only=True)

    plan = PlanInfoSerializer()
    persona = PersonaSerializer()
    class Meta:
        model = Estudiante
        fields = [
            'id', 'persona', 'nombre', 'plan', 'etapa_estudiante','acepta_contrato',
        ]


class PostulanteEducacionContinuaSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(source='persona.nombre', read_only=True)
    plan = PlanInfoSerializer()
    etapa_estudiante = serializers.IntegerField(source='etapa_actual', read_only=True)

    class Meta:
        model = PostulanteEducacionContinua
        fields = [
            'id', 'persona', 'nombre', 'plan', 'estudiante', 'etapa_estudiante',
        ]
