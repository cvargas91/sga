from rest_framework import serializers

from .models import (
    Departamento, Carrera, Plan, MallaObligatoria, MallaElectiva, Ramo, ConjuntoRamos
)


class DepartamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Departamento
        fields = ['id', 'nombre']


class CarreraSerializer(serializers.ModelSerializer):
    departamento = serializers.SlugRelatedField(read_only=True, slug_field='nombre')
    departamento_id = serializers.PrimaryKeyRelatedField(
        source='departamento',
        queryset=Departamento.objects.all(),
    )
    tipo_carrera_display = serializers.CharField(
        source='get_tipo_carrera_display', read_only=True)

    class Meta:
        model = Carrera
        fields = [
            'id', 'departamento', 'departamento_id', 'nombre', 'tipo_carrera',
            'tipo_carrera_display'
        ]


class PlanSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(source='__str__', read_only=True)
    carrera = CarreraSerializer(read_only=True)
    carrera_id = serializers.PrimaryKeyRelatedField(
        source='carrera',
        queryset=Carrera.objects.all(),
    )

    class Meta:
        model = Plan
        fields = ['id', 'nombre', 'carrera', 'carrera_id', 'version']


class PlanCortoSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(source='__str__', read_only=True)

    class Meta:
        model = Plan
        fields = ['id', 'nombre']


class PlanInfoSerializer(serializers.ModelSerializer):
    carrera = serializers.SlugRelatedField(read_only=True, slug_field='nombre')
    carrera_id = serializers.PrimaryKeyRelatedField(
        source='carrera', queryset=Carrera.objects.all())
    carrera_tipo = serializers.CharField(source='carrera.get_tipo_carrera_display', read_only=True)
    depto = serializers.SlugRelatedField(
        source='carrera.departamento', read_only=True, slug_field='nombre')

    class Meta:
        model = Plan
        fields = ['id', 'version', 'carrera', 'carrera_id', 'carrera_tipo', 'depto', 'link_decreto']


class RamoCortoSerializer(serializers.ModelSerializer):
    equivalencias = serializers.SlugRelatedField(
        slug_field='codigo', many=True, read_only=True)
    equivalencias_ids = serializers.PrimaryKeyRelatedField(
        source='equivalencias', many=True, write_only=True,
        queryset=Ramo.objects.all(), required=False)

    class Meta:
        model = Ramo
        fields = ['id', 'codigo', 'nombre', 'creditos', 'equivalencias', 'equivalencias_ids']


class RamoSerializer(serializers.ModelSerializer):
    requisitos = serializers.SlugRelatedField(
        slug_field='codigo', many=True, read_only=True)
    requisitos_ids = serializers.PrimaryKeyRelatedField(
        source='requisitos', many=True, write_only=True,
        queryset=Ramo.objects.all(), required=False)

    equivalencias = serializers.SlugRelatedField(
        slug_field='codigo', many=True, read_only=True)
    equivalencias_ids = serializers.PrimaryKeyRelatedField(
        source='equivalencias', many=True, write_only=True,
        queryset=Ramo.objects.all(), required=False)

    class Meta:
        model = Ramo
        fields = [
            'id', 'departamento', 'codigo', 'nombre', 'creditos', 'requisitos', 'requisitos_ids', 'requisito_nivel',
            'equivalencias', 'requisito_creditaje', 'equivalencias_ids',
        ]


class MallaObligatoriaSerializer(serializers.ModelSerializer):
    ramo = RamoSerializer(read_only=True)
    ramo_id = serializers.PrimaryKeyRelatedField(
        source='ramo', write_only=True, queryset=Ramo.objects.all(), required=False
    )

    class Meta:
        model = MallaObligatoria
        fields = ['semestre', 'tipo_formacion', 'ramo', 'ramo_id']


class MallaElectivaSerializer(serializers.ModelSerializer):
    class Meta:
        model = MallaElectiva
        fields = ['semestre', 'tipo_formacion', 'nombre', 'conjunto_ramos', 'creditos']


class ConjuntoRamosSerializer(serializers.ModelSerializer):
    ramos = RamoCortoSerializer(many=True, required=False, read_only=True)
    ramos_ids = serializers.PrimaryKeyRelatedField(
        source='ramos', many=True, write_only=True, queryset=Ramo.objects.all())

    class Meta:
        model = ConjuntoRamos
        fields = ['id', 'nombre', 'ramos', 'ramos_ids']


class MallaPlanSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(source='__str__', read_only=True)
    malla_obligatoria = MallaObligatoriaSerializer(many=True, required=True)
    malla_electiva = MallaElectivaSerializer(many=True, required=True)

    class Meta:
        model = Plan
        fields = ['id', 'nombre', 'malla_obligatoria', 'malla_electiva']

    def update(self, instance, validated_data):
        malla_obligatoria = validated_data.pop('malla_obligatoria')

        # eliminar obsoletas
        ids_obligatorios = [malla.get('ramo').id for malla in malla_obligatoria]
        MallaObligatoria.objects.filter(plan=instance).exclude(ramo__in=ids_obligatorios).delete()

        # crear nuevas o actualizar antiguas
        for malla in malla_obligatoria:
            MallaObligatoria.objects.update_or_create(
                plan=instance,
                ramo=malla.get('ramo'),
                defaults={**malla},
            )

        # no hay llave primaria para actualizar malla electiva, por lo que solo se eliminan todas
        # las anteriores y se crean las enviadas
        malla_electiva = validated_data.pop('malla_electiva')
        MallaElectiva.objects.filter(plan=instance).delete()
        for malla in malla_electiva:
            MallaElectiva.objects.create(plan=instance, **malla)

        return instance
