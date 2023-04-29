from rest_framework import serializers

from academica.models import MallaObligatoria, MallaElectiva
from curso.models import Curso, EstudianteCurso
from persona.models import Estudiante, Persona
from persona.serializers import EstudianteSerializer, PlanesEstudienteSerializer
from .models import (
    ProcesoInscripcion, EnvioInscripcion, SolicitudCurso,
)


def obtener_nivel_estudiante(ramos_estudiante, semestre):
    malla_obligatoria = MallaObligatoria.objects.filter(semestre__exact=semestre) \
        .prefetch_related('ramo')
    #TODO: Consultar a Eduardo si el ramo anatomia e histologia (SA1002) es equivalente a anatomia (SA1014) e histologia (SA1015)
    malla = set()
    for obligatorio in malla_obligatoria:
        malla.add(obligatorio.ramo)
    return malla.issubset(ramos_estudiante)


def comprobar_requisitos(malla, ramos_aprobados):
    # usuarios test: 302, 526, 506, 441
    # RAMO PRUEBA: EN1018
    # contar creditos obtenidos, TODO: verificar problema con las equivalencias que se estan sumando

    creditos_aprobados = 0
    for ramo in ramos_aprobados:
        creditos_aprobados += ramo.creditos

    ramos_inscribibles = []
    for ramo in malla:
        # quitar ramos aprobados
        if ramo in ramos_aprobados:
            continue
        # chequear requisitos
        # TODO: consultar si requisitos de creditaje y/o nivel estan asociados siempre con requisitos de ramos o pueden ser unicos para un ramo (como son las modalidades?)

        requisitos = set(ramo.requisitos.all())

        if requisitos.issubset(ramos_aprobados) and ramo.requisito_nivel is None and ramo.requisito_creditaje is None:
            ramos_inscribibles.append(ramo)
        elif ramo.requisito_nivel is not None and ramo.requisito_nivel > 0:
            if requisitos.issubset(ramos_aprobados) and obtener_nivel_estudiante(ramos_aprobados, ramo.requisito_nivel):
                ramos_inscribibles.append(ramo)
        elif ramo.requisito_creditaje is not None and ramo.requisito_creditaje > 0:
            if requisitos.issubset(ramos_aprobados) and creditos_aprobados >= ramo.requisito_creditaje:
                ramos_inscribibles.append(ramo)
        else:
            # entra a todos los ramos no aprobados y que 5no cumplen condicion
            if requisitos.issubset(ramos_aprobados) and obtener_nivel_estudiante(ramos_aprobados, ramo.requisito_nivel):
                if creditos_aprobados >= ramo.requisito_creditaje:
                    ramos_inscribibles.append(ramo)
    return ramos_inscribibles


def cursos_inscribibles(persona, periodo):
    # Obtener planes activos del alumno
    planes = Estudiante.objects.filter(persona=persona, estado_estudiante_id=4).values_list('plan')

    # Obtener malla de planes
    malla = set()

    malla_obligatoria = MallaObligatoria.objects.filter(plan__in=planes) \
        .prefetch_related('ramo__requisitos')
    for obligatorio in malla_obligatoria:
        malla.add(obligatorio.ramo)
        for equivalencia in obligatorio.ramo.equivalencias.all():
            malla.add(equivalencia)

    malla_electiva = MallaElectiva.objects.filter(plan__in=planes) \
        .prefetch_related('conjunto_ramos__ramos__requisitos')
    for electivo in malla_electiva:
        malla.update(electivo.conjunto_ramos.ramos.all())

    # obtener ramos aprobados del estudiante
    cursos_aprobados = EstudianteCurso.objects.filter(
        estudiante__persona=persona, estado__aprobado=True
    ).select_related('curso__ramo')
    ramos_aprobados = set([aprobado.curso.ramo for aprobado in cursos_aprobados])

    # agregar equivalencias a la lista de aprobados
    equivalencias = set()
    for ramo in ramos_aprobados:
        equivalencias.update(ramo.equivalencias.all())
    ramos_aprobados.update(equivalencias)
    ramos_inscribibles = comprobar_requisitos(malla, ramos_aprobados)

    # obtener oferta de cursos
    return Curso.objects.filter(ramo__in=ramos_inscribibles, periodo=periodo)


class InfoEstudiantesProcesoSerializer(serializers.ModelSerializer):
    nombres = serializers.CharField(source='persona.nombres', read_only=True)
    apellido1 = serializers.CharField(source='persona.apellido1', read_only=True)
    apellido2 = serializers.CharField(source='persona.apellido1', read_only=True)
    plan_nombre = serializers.CharField(source='plan.__str__', read_only=True)
    numero_documento = serializers.CharField(source='persona.numero_documento', read_only=True)
    mail_institucional = serializers.CharField(source='persona.mail_institucional', read_only=True)

    class Meta:
        model = Estudiante
        fields = [
            'id', 'nombres', 'apellido1', 'apellido2', 'plan', 'plan_nombre',
            'numero_documento', 'mail_institucional',
        ]


class ProcesoInscripcionSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    estado = serializers.IntegerField(source='get_estado', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    estudiantes = serializers.PrimaryKeyRelatedField(
        source='estudiante', many=True, queryset=Estudiante.objects.all(),
        required=False, write_only=True)
    estudiantes_datos = InfoEstudiantesProcesoSerializer(
        source='estudiante', many=True, read_only=True)

    class Meta:
        model = ProcesoInscripcion
        fields = [
            'id', 'nombre', 'periodo', 'fecha_apertura', 'fecha_cierre', 'tipo', 'tipo_display',
            'estado', 'estado_display', 'estudiantes', 'estudiantes_datos',
        ]


class SolicitudCursoSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    curso_nombre = serializers.CharField(source='curso.nombre_completo', read_only=True)

    class Meta:
        model = SolicitudCurso
        fields = [
            'id', 'curso', 'curso_nombre', 'curso2', 'tipo', 'tipo_display',
            'estado', 'estado_display', 'prioridad',
        ]
        extra_kwargs = {
            'curso2': {'required': False},
            'estado': {'required': False},
            'prioridad': {'read_only': True},
        }


class EnvioInscripcionSerializer(serializers.ModelSerializer):
    solicitudes = SolicitudCursoSerializer(many=True)

    class Meta:
        model = EnvioInscripcion
        fields = ['id', 'proceso', 'persona', 'fecha_envio', 'solicitudes']
        extra_kwargs = {
            'fecha_envio': {'read_only': True},
        }

    def crear_solicitudes(self, envio, solicitudes):
        inscribibles = cursos_inscribibles(envio.persona, envio.proceso.periodo)
        inscritos = EstudianteCurso.objects.filter(
            estudiante__persona=envio.persona, curso__periodo=envio.proceso.periodo)

        print(inscritos.count())
        for i in inscritos:
            print(i)
        solicitudes_tipo = dict()

        for solicitud in solicitudes:
            print(solicitud)
            curso = solicitud.get('curso')
            tipo = solicitud.get('tipo')

            # solo agregar cursos inscribibles
            if tipo == 0 and not inscribibles.filter(pk=curso.id).exists():
                continue

            # solo eliminar cursos inscritos
            if tipo == 1 and not inscritos.filter(curso=curso).exists():
                continue

            SolicitudCurso.objects.create(
                envio=envio,
                **solicitud,
                prioridad=solicitudes_tipo.get(tipo, 0)
            )
            solicitudes_tipo[tipo] = solicitudes_tipo.get(tipo, 0) + 1

        return

    def create(self, validated_data):
        solicitudes = validated_data.pop('solicitudes')
        envio = EnvioInscripcion.objects.create(**validated_data)
        # crear solicitudes nuevas
        self.crear_solicitudes(envio, solicitudes)
        return envio

    def update(self, instance, validated_data):
        solicitudes = validated_data.pop('solicitudes')
        total_creditos = 0
        for solicitud in solicitudes:
            total_creditos += solicitud['curso'].creditos
        if total_creditos > 30:
            # actualizar fecha de envio automáticamente
            instance.save()

            # eliminar solicitudes antiguas
            SolicitudCurso.objects.filter(envio=instance).delete()

            # crear solicitudes nuevas
            self.crear_solicitudes(instance, solicitudes)

            # actualizar estado solicitud curso
            solicitud = SolicitudCurso.objects.filter(envio=instance).first()
            solicitud.estado = 6
            solicitud.save()

            # llamar a funcion de email para que envie a jefe de carrera

            return instance
        else:
            # actualizar fecha de envio automáticamente
            instance.save()

            # eliminar solicitudes antiguas
            SolicitudCurso.objects.filter(envio=instance).delete()

            # crear solicitudes nuevas
            self.crear_solicitudes(instance, solicitudes)
            return instance
