from django.utils.timezone import localdate
from .models import PeriodoTipoSolicitud, Solicitud, SolicitudRenuncia
from .permisos import SolicitudPermisos
from .resoluciones import APROBAR_SOLICITUD_TIPO
from rest_framework import serializers
from rest_access_policy import FieldAccessMixin
from curso.models import Periodo
from solicitudes.models import (
    SolicitudPostergacion, SolicitudCambioCarrera, SolicitudReintegracion, TipoSolicitud,
    CausaSolicitud,
)


class TipoSolicitudSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoSolicitud
        fields = ('id', 'nombre', 'instrucciones')


class CausaSolicitudSerializer(serializers.ModelSerializer):
    class Meta:
        model = CausaSolicitud
        fields = ('id', 'nombre')


class PeriodoTipoSolicitudSerializer(serializers.ModelSerializer):
    tipo_solicitud_nombre = serializers.CharField(source='tipo_solicitud.nombre', read_only=True)

    class Meta:
        model = PeriodoTipoSolicitud
        fields = ('id', 'tipo_solicitud', 'tipo_solicitud_nombre', 'fecha_inicio', 'fecha_fin')


# Serializadores base
class SolicitudSerializer(serializers.ModelSerializer):
    persona = serializers.PrimaryKeyRelatedField(source='estudiante.persona', read_only=True)
    persona_nombre = serializers.CharField(
        source='estudiante.persona.nombre_completo', read_only=True)
    persona_rut = serializers.CharField(source='estudiante.persona.documento', read_only=True)
    carrera = serializers.PrimaryKeyRelatedField(
        source='estudiante.plan.carrera', read_only=True)
    carrera_nombre = serializers.StringRelatedField(
        source='estudiante.plan.carrera', read_only=True)
    tipo_nombre = serializers.CharField(source='tipo.nombre', read_only=True)
    estado_nombre = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = Solicitud
        fields = (
            'id', 'persona', 'estudiante', 'persona_nombre', 'persona_rut', 'carrera',
            'carrera_nombre', 'tipo', 'tipo_nombre', 'fecha_creacion', 'periodo',
            'fecha_actualizacion', 'fecha_resolucion', 'estado', 'estado_nombre',
        )


class SolicitudPostergacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SolicitudPostergacion
        fields = ('id', 'duracion_semestres')


class SolicitudCambioCarreraSerializer(serializers.ModelSerializer):
    carrera_nombre = serializers.StringRelatedField(source='carrera')

    class Meta:
        model = SolicitudCambioCarrera
        fields = ('id', 'carrera', 'carrera_nombre')


class SolicitudReintegracionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SolicitudReintegracion
        fields = ('id',)


class SolicitudRenunciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = SolicitudRenuncia
        fields = ('id',)


# Serializadores anidados
class SolicitudDetalleSerializer(FieldAccessMixin, SolicitudSerializer):
    tipo_instrucciones = serializers.CharField(source='tipo.instrucciones', read_only=True)
    # causa_nombre = serializers.CharField(source='causa_principal.nombre', read_only=True)
    periodo_nombre = serializers.StringRelatedField(source='periodo', read_only=True)
    detalle = serializers.SerializerMethodField()
    causas_estudiante_detalle = CausaSolicitudSerializer(source='causas_estudiante',
                                                         read_only=True, many=True)
    causas_revisor_detalle = CausaSolicitudSerializer(source='causas_revisor',
                                                      read_only=True, many=True)

    class Meta:
        model = Solicitud
        fields = (
            *SolicitudSerializer.Meta.fields,
            'periodo_nombre', 'tipo_instrucciones', 'detalle', 'justificacion_estudiante',
            'resolucion', 'comentario_revisor', 'justificacion_revisor', 'valida_causas',
            'causas_estudiante_detalle', 'causas_revisor_detalle',
        )
        access_policy = SolicitudPermisos

    def get_detalle(self, obj):
        if obj.tipo_id == 1:
            sp = SolicitudPostergacion.objects.get(solicitud_id=obj.id)
            return SolicitudPostergacionSerializer(sp).data

        if obj.tipo_id == 2:
            scc = SolicitudCambioCarrera.objects.get(solicitud_id=obj.id)
            return SolicitudCambioCarreraSerializer(scc).data

        if obj.tipo_id == 3:
            sr = SolicitudReintegracion.objects.get(solicitud_id=obj.id)
            return SolicitudReintegracionSerializer(sr).data

        if obj.tipo_id == 4:
            sre = SolicitudRenuncia.objects.get(solicitud_id=obj.id)
            return SolicitudRenunciaSerializer(sre).data


class EnvioSolicitudSerializer(serializers.ModelSerializer):
    class Meta:
        model = Solicitud
        fields = ('tipo', 'causas_estudiante', 'justificacion_estudiante')


class EnvioSolicitudEspecificaSerializer(serializers.ModelSerializer):
    solicitud = EnvioSolicitudSerializer()

    def validate(self, data):
        user = self.context['request'].user
        estudiante = user.get_persona().estudiante_activo()

        tipo = data['solicitud']['tipo']
        if not tipo.estados_validos.filter(pk=estudiante.estado_estudiante_id).exists():
            raise serializers.ValidationError(
                'El estudiante no puede realizar esta solicitud en el estado academico actual')

        return data

    def create(self, validated_data):
        solicitud_base_data = validated_data.pop('solicitud')
        causas_estudiante = solicitud_base_data.pop('causas_estudiante')
        # obtener estudiante
        estudiante = self.context.get('request').user.get_persona().estudiante_activo()

        solicitud_base = Solicitud.objects.create(
            estudiante=estudiante,
            periodo=Periodo.get_activo(),
            **solicitud_base_data,
        )
        solicitud_base.causas_estudiante.set(causas_estudiante)

        solicitud_postergacion = self.Meta.model.objects.create(
            solicitud=solicitud_base, **validated_data,
        )
        return solicitud_postergacion


class EnvioSolicitudPostergacionSerializer(EnvioSolicitudEspecificaSerializer):
    class Meta:
        model = SolicitudPostergacion
        fields = ('solicitud', 'duracion_semestres')


class EnvioSolicitudCambioCarreraSerializer(EnvioSolicitudEspecificaSerializer):
    class Meta:
        model = SolicitudCambioCarrera
        fields = ('solicitud', 'carrera')


class EnvioSolicitudReintegracionSerializer(EnvioSolicitudEspecificaSerializer):
    class Meta:
        model = SolicitudReintegracion
        fields = ('solicitud',)


class EnvioSolicitudRenunciaSerializer(EnvioSolicitudEspecificaSerializer):
    class Meta:
        model = SolicitudRenuncia
        fields = ('solicitud',)


SERIALIZADOR_TIPO = {
    1: EnvioSolicitudPostergacionSerializer,
    2: EnvioSolicitudCambioCarreraSerializer,
    3: EnvioSolicitudReintegracionSerializer,
    4: EnvioSolicitudRenunciaSerializer,
}


class ResolucionSolicitudSerializer(serializers.ModelSerializer):

    class Meta:
        model = Solicitud
        fields = ('id', 'estado', 'resolucion', 'comentario_revisor', 'justificacion_revisor',
                  'valida_causas', 'causas_revisor')

    def update(self, instance, validated_data):
        if instance.estado not in [0, 5]:
            raise serializers.ValidationError({'detail': 'La solicitud ya fue resuelta'})

        estado_anterior = instance.estado
        instance.estado = validated_data.get('estado')
        instance.resolucion = validated_data.get('resolucion')
        instance.comentario_revisor = validated_data.get('comentario_revisor')
        instance.justificacion_revisor = validated_data.get('justificacion_revisor')
        instance.valida_causas = validated_data.get('valida_causas')
        instance.fecha_resolucion = localdate()
        instance.causas_revisor.set(validated_data["causas_revisor"])

        instance.save()

        if instance.estado == 1:
            tipo = instance.tipo_id
            funcion_aprobacion = APROBAR_SOLICITUD_TIPO.get(tipo, None)
            funcion_aprobacion(instance, estado_anterior)

        return instance


class DecretoResolucionSolicitudSerializer(serializers.ModelSerializer):
    class Meta:
        model = Solicitud
        fields = (
            'resolucion', 'comentario_revisor', 'justificacion_revisor', 'valida_causas',
            'causas_revisor'
        )
