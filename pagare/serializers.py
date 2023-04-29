from rest_framework import serializers

from .models import (
    ModalidadCuotaPagare, Pagare, HistorialEstadoPagare, PagarePersona, TipoExtraPagare,
    PagoExtraPagare, FechaCuotaPagare, CuotaPagare,
)


class ModalidadCuotaPagareSerializer(serializers.ModelSerializer):
    curso_asociado_display = serializers.CharField(
        source='get_curso_asociado_display', read_only=True)

    class Meta:
        model = ModalidadCuotaPagare
        fields = [
            'id', 'proceso_matricula', 'plan', 'cantidad_cuotas',
            'curso_asociado_display', 'link_pagare', 'fecha_primera_cuota',
        ]


class PagareSerializer(serializers.ModelSerializer):
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = Pagare
        fields = [
            'id', 'arancel_estudiante', 'fecha', 'modalidad_cuota', 'monto_arancel', 'validado',
            'estado', 'estado_display', 'cantidad_cuotas'
        ]


class HistorialEstadoPagareSerializer(serializers.ModelSerializer):
    estado_anterior_display = serializers.CharField(
        source='get_estado_anterior_display', read_only=True)
    estado_actual_display = serializers.CharField(
        source='get_estado_actual_display', read_only=True)

    class Meta:
        model = HistorialEstadoPagare
        fields = [
            'id', 'pagare', 'estado_anterior_display', 'estado_actual_display', 'autor_cambio',
        ]


class PagarePersonaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PagarePersona
        fields = [
            'id', 'pagare', 'tipo_persona_display', 'rut', 'nombres', 'primer_apellido',
            'segundo_apellido', 'carnet', 'direccion', 'comuna', 'telefono',
        ]


class TipoExtraPagareSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoExtraPagare
        fields = ['id', 'nombre']


class PagoExtraPagareSerializer(serializers.ModelSerializer):
    tipo_extra = TipoExtraPagareSerializer()

    class Meta:
        model = PagoExtraPagare
        fields = ['id', 'pagare', 'tipo_extra', 'monto', 'justificacion']


class FechaCuotaPagareSerializer(serializers.ModelSerializer):
    class Meta:
        model = FechaCuotaPagare
        fields = ['id', 'modalidad_cuota', 'numero_cuota', 'fecha_pago']


class CuotaPagareSerializer(serializers.ModelSerializer):
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = CuotaPagare
        fields = [
            'id', 'pagare', 'numero_cuota', 'monto_a_pagar', 'fecha_cuota_pagare', 'fecha_cuota',
            'monto_pagado', 'orden_compra', 'fecha_pago', 'estado_display'
        ]
