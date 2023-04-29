from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from curso.validadores import validar_suma_ponderaciones

from .models import (
    Curso, Evaluacion, Horario, DocenteCurso, AyudanteCurso, Modulo, Periodo, EstudianteCurso,
    CategoriaActividad, Actividad, Nota
)
from academica.serializers import RamoSerializer, RamoCortoSerializer
from persona.serializers import PersonaCortaSerializer


class PeriodoSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(source='__str__', read_only=True)

    class Meta:
        model = Periodo
        fields = ['id', 'ano', 'numero', 'activo', 'nombre', 'fecha_inicio', 'fecha_fin']


class DocenteCursoSerializer(serializers.ModelSerializer):
    rol_display = serializers.CharField(source='get_rol_display', read_only=True)
    detalle_persona = PersonaCortaSerializer(source='persona', read_only=True)

    class Meta:
        model = DocenteCurso
        fields = ['curso', 'persona', 'rol', 'detalle_persona', 'rol_display']
        extra_kwargs = {
            'persona': {'write_only': True},
            'curso': {'read_only': True},
        }


class AyudanteCursoSerializer(serializers.ModelSerializer):
    detalle_persona = PersonaCortaSerializer(source='persona', read_only=True)

    class Meta:
        model = AyudanteCurso
        fields = ['curso', 'persona', 'detalle_persona']
        extra_kwargs = {
            'persona': {'write_only': True},
            'curso': {'read_only': True},
        }


class ModuloSerializer(serializers.ModelSerializer):
    class Meta:
        model = Modulo
        fields = ['id', 'hora_inicio', 'hora_termino']


class HorarioSerializer(serializers.ModelSerializer):
    hora_inicio = serializers.TimeField(
        source='modulo.hora_inicio',
        format='%H:%M',
        read_only=True,
    )
    hora_termino = serializers.TimeField(
        source='modulo.hora_termino',
        format='%H:%M',
        read_only=True,
    )
    tipo_display = serializers.CharField(source='get_tipo_horario_display', read_only=True)
    dia_display = serializers.CharField(source='get_dia_display', read_only=True)

    class Meta:
        model = Horario
        fields = [
            'dia', 'modulo', 'tipo_horario', 'hora_inicio', 'hora_termino', 'tipo_display',
            'dia_display', 'sala',
        ]


class CursoSerializer(serializers.ModelSerializer):
    detalle_ramo = RamoSerializer(source='ramo', read_only=True)
    estado_display = serializers.CharField(source='get_estado_curso_display', read_only=True)
    horario = HorarioSerializer(many=True, required=False)

    docentes = DocenteCursoSerializer(many=True, required=False)
    ayudantes = AyudanteCursoSerializer(many=True, required=False)
    estudiantes = serializers.SerializerMethodField()
    solicitudes = serializers.SerializerMethodField()

    class Meta:
        model = Curso
        fields = [
            'id', 'ramo', 'detalle_ramo', 'periodo', 'seccion', 'creditos', 'cupo', 'docentes',
            'ayudantes', 'horario', 'estado_curso', 'estado_display', 'estudiantes', 'solicitudes',
        ]
        extra_kwargs = {
            'ramo': {'write_only': True},
            'estado_curso': {'write_only': True},
            'creditos': {'read_only': True},
        }

    def get_estudiantes(self, obj):
        return obj.estudiantes.count()

    def get_solicitudes(self, obj):
        return obj.solicitudes.count()

    def create(self, validated_data):
        docentes = validated_data.pop('docentes')
        ayudantes = validated_data.pop('ayudantes')
        bloques = validated_data.pop('horario')

        curso = Curso.objects.create(**validated_data)

        for docente in docentes:
            DocenteCurso.objects.create(curso=curso, **docente)
        for ayudante in ayudantes:
            AyudanteCurso.objects.create(curso=curso, **ayudante)
        for bloque in bloques:
            Horario.objects.create(curso=curso, **bloque)

        return curso

    def update(self, instance, validated_data):
        instance.cupo = validated_data.get('cupo', instance.cupo)
        instance.save()

        # actualizar docentes
        docentes = validated_data.pop('docentes')
        ids_docentes = [docente.get('persona').id for docente in docentes]

        docentes_antiguos = DocenteCurso.objects.filter(curso=instance)
        ids_docentes_antiguas = docentes_antiguos.values_list('persona__id', flat=True)

        # eliminar docentes antiguos
        for docente in docentes_antiguos:
            if docente.persona.id not in ids_docentes:
                docente.delete()

        for docente in docentes:
            persona = docente.get('persona')
            rol = docente.get('rol')

            if persona.id in ids_docentes_antiguas:
                # actualizar antiguo
                dictado = docentes_antiguos.get(persona=persona)
                dictado.rol = rol
                dictado.save()
            else:
                # crear nuevo
                DocenteCurso.objects.create(curso=instance, persona=persona, rol=rol)

        # actualizar ayudantes
        ayudantes = validated_data.pop('ayudantes')
        ids_ayudantes = [ayudante.get('persona').id for ayudante in ayudantes]

        ayudantes_antiguos = AyudanteCurso.objects.filter(curso=instance)
        ids_ayudantes_antiguas = ayudantes_antiguos.values_list('persona__id', flat=True)

        # eliminar ayudantes antiguos
        for ayudante in ayudantes_antiguos:
            if ayudante.persona.id not in ids_ayudantes:
                ayudante.delete()

        # crear nuevos
        for ayudante in ayudantes:
            persona = ayudante.get('persona')
            if persona.id not in ids_ayudantes_antiguas:
                AyudanteCurso.objects.create(curso=instance, persona=persona)

        # actualizar horario
        bloques = validated_data.pop('horario')
        ids_actuales = []

        for bloque in bloques:
            dia = bloque.get('dia')
            modulo = bloque.get('modulo')
            tipo = bloque.get('tipo_horario')
            sala = bloque.get('sala')

            if Horario.objects.filter(curso=instance, dia=dia, modulo=modulo).exists():
                # modificar bloque antiguo
                bloque_antiguo = Horario.objects.get(curso=instance, dia=dia, modulo=modulo)
                bloque_antiguo.tipo_horario = tipo
                bloque_antiguo.sala = sala
                bloque_antiguo.save()

                ids_actuales.append(bloque_antiguo.id)

            else:
                # crear nuevo bloque
                bloque_nuevo = Horario.objects.create(
                    curso=instance, dia=dia, modulo=modulo, tipo_horario=tipo, sala=sala,
                )
                ids_actuales.append(bloque_nuevo.id)

        # eliminar bloques obsoletos
        Horario.objects.filter(curso=instance).exclude(id__in=ids_actuales).delete()

        return instance


class CursoResumenSerializer(serializers.ModelSerializer):
    ramo = RamoCortoSerializer()

    class Meta:
        model = Curso
        fields = ['id', 'ramo', 'periodo', 'seccion']


class EstudianteCursoSerializer(serializers.ModelSerializer):
    detalle_persona = PersonaCortaSerializer(source='estudiante.persona', read_only=True)
    id_estudiantecurso = serializers.IntegerField(source='pk', read_only=True)

    class Meta:
        model = EstudianteCurso
        fields = ['id_estudiantecurso', 'curso', 'detalle_persona']


class CursoIntegrantesSerializer(serializers.ModelSerializer):
    docentes = DocenteCursoSerializer(many=True, required=False)
    ayudantes = AyudanteCursoSerializer(many=True, required=False)
    estudiantes = EstudianteCursoSerializer(many=True, required=False)

    class Meta:
        model = Curso
        fields = [
            'id', 'docentes', 'ayudantes', 'estudiantes',
        ]


class CursoHorarioSerializer(serializers.ModelSerializer):
    horario = HorarioSerializer(many=True, required=False)
    ramo = RamoCortoSerializer(read_only=True)

    class Meta:
        model = Curso
        fields = [
            'id', 'ramo', 'seccion', 'periodo', 'horario',
        ]


class HistorialCursosSerializer(serializers.ModelSerializer):
    ramo = RamoSerializer(source='curso.ramo', read_only=True)
    periodo = serializers.StringRelatedField(source='curso.periodo', read_only=True)
    estado_nombre = serializers.CharField(source='estado.nombre', read_only=True)

    class Meta:
        model = EstudianteCurso
        fields = ['ramo', 'periodo', 'estado', 'estado_nombre', 'nota_final']


def serializar_opciones(opciones):
    data = []
    for (id_opcion, valor) in opciones:
        data.append({'id': id_opcion, 'valor': valor})
    return data


class CategoriaActividadSerializer(serializers.ModelSerializer):
    plan_id = serializers.PrimaryKeyRelatedField(read_only=True)
    plan = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = CategoriaActividad
        fields = ['id', 'nombre', 'plan_id', 'plan']


class ActividadSerializer(serializers.ModelSerializer):

    class Meta:
        model = Actividad
        fields = ['curso', 'ponderacion', 'categoria_actividad']
        validators = []


class ActividadesCursoSerializer(serializers.Serializer):
    actividades = ActividadSerializer(many=True, required=False)
    curso = serializers.PrimaryKeyRelatedField(write_only=True, queryset=Curso.objects.all())

    def validate(self, data):
        actividades_data = data.get('actividades')
        ponderacion_total = 0

        for actividad in actividades_data:
            ponderacion_total += actividad['ponderacion']

            if actividad.get('curso') != data.get('curso'):
                raise serializers.ValidationError({
                    'detail': 'Las actividades deben corresponder al mismo curso.'})

        if ponderacion_total != 100:
            raise serializers.ValidationError({
                'detail': 'Las ponderaciones del listado de actividades deben sumar 100'})
        return data

    def create(self, validated_data):
        curso = validated_data.pop('curso')
        actividades = validated_data.pop('actividades')

        # lista de IDs de actividades para eliminar
        # inicialmente son todas las actividades creadas anteriormente
        actividades_a_eliminar = list(
            Actividad.objects.filter(curso=curso).values_list('id', flat=True))

        for actividad in actividades:
            try:
                categoria = actividad.get('categoria_actividad')
                curso = actividad.get('curso')

                # si ya existía una actividad de esa categoría en ese curso, actualizar ponderación
                # ésta linea hace necesaria la restriccion unique_together
                actividad_actualizada = Actividad.objects.get(
                    curso=curso, categoria_actividad=categoria)

                actividad_actualizada.ponderacion = actividad.get('ponderacion')
                actividad_actualizada.save()

                # si se actualiza correctamente, quitar id del listado de actividades a eliminar
                # manteniendo las evaluaciones y notas de la actividad que ya se ingresaron
                actividades_a_eliminar.remove(actividad_actualizada.pk)

            except Actividad.DoesNotExist:
                Actividad.objects.create(**actividad)

        Actividad.objects.filter(id__in=actividades_a_eliminar).delete()
        return {}

    class Meta:
        model = Curso
        fields = ['id', 'actividades', 'curso']


class EvaluacionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Evaluacion
        fields = ['actividad', 'nombre', 'fecha', 'lugar', 'ponderacion']


class EvaluacionesActividadSerializer(serializers.Serializer):
    evaluaciones = EvaluacionSerializer(many=True, required=False)
    actividad = serializers.PrimaryKeyRelatedField(
        write_only=True, queryset=Actividad.objects.all())

    def validate(self, data):
        validar_suma_ponderaciones(data, "evaluaciones")

        evaluaciones_data = data.get('evaluaciones')
        for evaluacion in evaluaciones_data:
            if evaluacion.get('actividad') != data.get('actividad'):
                raise serializers.ValidationError({
                    'detail': 'Las evaluaciones deben corresponder a la misma actividad.'})

        return data

    def create(self, validated_data):
        actividad = validated_data.pop('actividad')
        evaluaciones = validated_data.pop('evaluaciones')

        # lista de IDs de evaluaciones anteriores
        evaluaciones_a_eliminar = list(
            Evaluacion.objects.filter(actividad=actividad).values_list('id', flat=True))

        for evaluacion in evaluaciones:
            nombre = evaluacion.get('nombre')

            evaluacion_actualizada, created = Evaluacion.objects.update_or_create(
                nombre=nombre, defaults=({**evaluacion}))

            if created is False:  # no eliminar evaluaciones actualizadas (mantener notas)
                evaluaciones_a_eliminar.remove(evaluacion_actualizada.pk)

        Evaluacion.objects.filter(id__in=evaluaciones_a_eliminar).delete()
        return {}

    class Meta:
        model = Actividad
        fields = ['id', 'evaluaciones', 'actividad']


class ReadEvaluacionesActividadSerializer(serializers.ModelSerializer):
    evaluaciones = EvaluacionSerializer(many=True)
    categoria_nombre = serializers.StringRelatedField(source='categoria_actividad.nombre')

    class Meta:
        model = Actividad
        fields = ['curso', 'ponderacion', 'categoria_actividad', 'categoria_nombre', 'evaluaciones']


class EvaluacionesCursoSerializer(serializers.ModelSerializer):
    actividades = ReadEvaluacionesActividadSerializer(many=True)

    class Meta:
        model = Curso
        fields = ['id', 'actividades']


class CursoEstudiantesSerializer(serializers.ModelSerializer):
    estudiantes = EstudianteCursoSerializer(many=True, required=False)

    class Meta:
        model = Curso
        fields = ['id', 'estudiantes']


class NotaEvaluacionSerializer(serializers.ModelSerializer):

    def validate(self, data):
        if data.get('evaluacion').actividad.curso != data.get('estudiante_curso').curso:
            raise ValidationError({
                'detail': 'La evaluación no coincide con el curso indicado.'})
        return data

    class Meta:
        model = Nota
        fields = ['id', 'evaluacion', 'estudiante_curso', 'nota', 'fecha_ingreso',
                  'fecha_actualizacion']
        validators = []


class EnvioNotasEvaluacionSerializer(serializers.ModelSerializer):
    notas = NotaEvaluacionSerializer(many=True)

    def create(self, validated_data):
        ret = []
        evaluacion = validated_data.pop('evaluacion')
        notas = evaluacion.pop('notas')

        for nota in notas:
            obj, _ = Nota.objects.update_or_create(
                evaluacion=nota.get('evaluacion'),
                estudiante_curso=nota.get('estudiante_curso'),
                defaults={**nota})
            ret.append(obj)
        # serializer = NotaEvaluacionSerializer(data=ret, many=True)
        # return serializer
        return obj  # TODO: devolver listado de notas creadas/actualizadas

    class Meta:
        model = Evaluacion
        fields = ['id', 'notas']


class ConfiguracionCursoSerializer(serializers.ModelSerializer):
    ramo = RamoCortoSerializer(read_only=True)

    class Meta:
        model = Curso
        fields = ['nota_aprobacion_curso', 'tiene_examen', 'examen_reprobatorio',
                  'nota_minima_examen', 'nota_eximicion_examen', 'ponderacion_examen',
                  'ramo']


class NotasPresentacionSerializer(serializers.ModelSerializer):

    class Meta:
        model = EstudianteCurso
        fields = ['id', 'nota_presentacion']


class NotasFinalesSerializer(serializers.ModelSerializer):

    class Meta:
        model = EstudianteCurso
        fields = ['id', 'nota_final']


class NotaExamenSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = EstudianteCurso
        fields = ['id', 'nota_examen']


class NotasVistaResumenSerializer(serializers.ModelSerializer):

    class Meta:
        model = EstudianteCurso
        fields = ['estudiante', 'nota_presentacion', 'nota_examen', 'nota_final']


class NotasExamenCursoSerializer(serializers.ModelSerializer):
    # https://github.com/encode/django-rest-framework/issues/2320#issuecomment-67502474
    notas = NotaExamenSerializer(many=True, source='estudiantes')

    def update(self, instance, validated_data):
        notas = validated_data.pop('estudiantes')
        for nota in notas:
            try:
                e = EstudianteCurso.objects.get(pk=nota.get('id'))
                e.nota_examen = nota.get('nota_examen')
                e.save()
            except EstudianteCurso.DoesNotExist:
                continue

        return instance

    class Meta:
        model = Curso
        fields = ['id', 'notas']


# serializadores para vista resumen curso
class EstudianteCursoDetalleSerializer(serializers.ModelSerializer):
    detalle_persona = PersonaCortaSerializer(source='estudiante.persona', read_only=True)
    id_estudiantecurso = serializers.IntegerField(source='pk', read_only=True)

    class Meta:
        model = EstudianteCurso
        fields = ['id_estudiantecurso', 'curso', 'detalle_persona',
                  'nota_examen', 'nota_presentacion']


class EvaluacionNotasSerializer(serializers.ModelSerializer):
    notas = NotaEvaluacionSerializer(many=True, read_only=True)

    class Meta:
        model = Evaluacion
        fields = ['id', 'notas']


class ActividadesDetalleSerializer(serializers.ModelSerializer):
    evaluaciones = EvaluacionNotasSerializer(many=True, read_only=True)

    class Meta:
        model = Actividad
        fields = ['id', 'evaluaciones']


class VistaResumenCursoSerializer(serializers.ModelSerializer):
    actividades = ActividadesDetalleSerializer(many=True)
    estudiantes = EstudianteCursoDetalleSerializer(many=True, required=False)

    class Meta:
        model = Curso
        fields = ['id', 'actividades', 'ramo', 'estudiantes']
