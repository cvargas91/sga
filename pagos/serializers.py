from rest_framework import serializers

from .models import OrdenCompra, FormaPago


class FormaPagoSerializer(serializers.ModelSerializer):
    modalidad_nombre = serializers.CharField(source='modalidad_pago.nombre', read_only=True)

    class Meta:
        model = FormaPago
        fields = [
            'id', 'nombre', 'modalidad_pago', 'modalidad_nombre',
        ]


class OrdenCompraSerializer(serializers.ModelSerializer):
    estado_pago_display = serializers.CharField(source='get_estado_pago_display', read_only=True)
    forma_pago = FormaPagoSerializer()

    class Meta:
        model = OrdenCompra
        fields = [
            'id', 'persona', 'forma_pago', 'monto_total', 'total_descuento_beneficios',
            'estado_pago', 'estado_pago_display'
        ]
