from rest_framework import serializers
from certificados.generador import crear_certificado_personalizado

from certificados.models import Certificado, SolicitudCertificado


class CertificadoSerializer(serializers.ModelSerializer):
    persona_nombre = serializers.CharField(source='estudiante.persona.nombre_completo')
    persona_rut = serializers.CharField(source='estudiante.persona.documento')
    carrera = serializers.PrimaryKeyRelatedField(source='estudiante.plan.carrera', read_only=True)
    carrera_nombre = serializers.StringRelatedField(
        source='estudiante.plan.carrera', read_only=True)
    tipo_nombre = serializers.StringRelatedField(
        source='get_tipo_certificado_display', read_only=True)

    class Meta:
        model = Certificado
        fields = [
            'id', 'persona_nombre', 'persona_rut', 'carrera', 'carrera_nombre',
            'fecha_emision', 'tipo_certificado', 'tipo_nombre', 'valido',
            'url_archivo', 'nombre_archivo',
        ]


class SolicitudCertificadoSerializer(serializers.ModelSerializer):
    persona_nombre = serializers.CharField(source='estudiante.persona.nombre_completo')
    persona_rut = serializers.CharField(source='estudiante.persona.documento')
    carrera = serializers.PrimaryKeyRelatedField(source='estudiante.plan.carrera', read_only=True)
    carrera_nombre = serializers.StringRelatedField(
        source='estudiante.plan.carrera', read_only=True)

    estado_nombre = serializers.StringRelatedField(source='get_estado_display', read_only=True)
    certificado = CertificadoSerializer(read_only=True)

    class Meta:
        model = SolicitudCertificado
        fields = [
            'id', 'persona_nombre', 'persona_rut', 'carrera', 'carrera_nombre',
            'titulo', 'descripcion', 'justificacion', 'estado', 'estado_nombre', 'fecha_solicitud',
            'certificado',
        ]


class PostSolicitudCertificadoSerializer(serializers.ModelSerializer):

    class Meta:
        model = SolicitudCertificado
        fields = ['titulo', 'descripcion', 'justificacion']

    def create(self, validated_data):
        estudiante = self.context.get('request').user.get_persona().estudiante_activo()
        solicitud = SolicitudCertificado.objects.create(estudiante=estudiante, **validated_data)
        return solicitud


class ResolucionSolicitudCertificadoSerializer(serializers.ModelSerializer):
    certificado_file = serializers.CharField(source='certificado.url_archivo', read_only=True)

    class Meta:
        model = SolicitudCertificado
        fields = ('id', 'estado', 'titulo_revisor', 'contenido_revisor', 'estudiante',
                  'certificado', 'certificado_file')
        read_only_fields = ['estudiante', 'certificado']

    def update(self, instance, validated_data):
        if instance.estado != 0:
            raise serializers.ValidationError({
                'detail': 'Esta solicitud ya fue resuelta'
            })

        instance.estado = validated_data.get('estado')

        if instance.estado == 1:  # aprobar solicitud
            instance.titulo_revisor = validated_data.get('titulo_revisor')
            instance.contenido_revisor = validated_data.get('contenido_revisor')
            instance.certificado = crear_certificado_personalizado(
                instance.estudiante, instance.titulo_revisor, instance.contenido_revisor)

        instance.save()
        return instance
