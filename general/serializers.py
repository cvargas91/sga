from rest_framework import serializers

from .models import (
    Region, Comuna, Pais,
)


class ComunaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comuna
        fields = [
            'id', 'nombre', 'region',
        ]


class RegionSerializer(serializers.ModelSerializer):
    comunas = ComunaSerializer(many=True, read_only=True)

    class Meta:
        model = Region
        fields = [
            'id', 'nombre', 'comunas',
        ]


class PaisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pais
        fields = [
            'id', 'nombre',
        ]
