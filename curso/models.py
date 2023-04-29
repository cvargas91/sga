from decimal import Decimal, ROUND_HALF_UP
from django.db import models
from django.db.models.signals import post_save
from .validadores import validadores_ponderaciones, validatar_nota


class PeriodoManager(models.Manager):
    def get_by_natural_key(self, ano, numero):
        return self.get(ano=ano, numero=numero)


class Periodo(models.Model):
    numeros_periodo = [
        (1, 'primer semestre'),
        (2, 'segundo semestre'),
    ]

    ano = models.PositiveSmallIntegerField()
    numero = models.PositiveSmallIntegerField(choices=numeros_periodo)

    activo = models.BooleanField(
        help_text='''
            influye en la lógica del sistema, define qué ramos se están cursando actualmente, los
            procesos de inscripción académica a los que se puede acceder, entre otros.
        '''
    )
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)
    fecha_limite_primera_evaluacion = models.DateField(null=True, blank=True)

    link_decreto = models.CharField(
        max_length=300, blank=True, help_text='solo para guardar registro'
    )
    id_ucampus = models.CharField(max_length=50, blank=True)
    id_SAI = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        db_table = 'periodo'
        unique_together = ('ano', 'numero')
        ordering = ('ano', 'numero')

    objects = PeriodoManager()

    def save(self, *args, **kwargs):
        # desactivar todos los otros periodos cuando se activa un periodo nuevo
        if self.activo:
            Periodo.objects.update(activo=False)

        super().save(*args, **kwargs)
        if self.activo:
            Curso.objects.filter(periodo=self, estado_curso=0).update(estado_curso=1)

    def natural_key(self):
        return (self.ano, self.numero)

    def __str__(self):
        return f'{self.get_numero_display()} {self.ano}'

    @staticmethod
    def get_activo():
        return Periodo.objects.filter(activo=True)[0]

    def get_sgte_primer_semestre(self):
        sgt_primer_semestre, _ = Periodo.objects.get_or_create(
            ano=self.ano + 1, numero=1,
            defaults={'activo': False},
        )
        return sgt_primer_semestre

    def __gt__(self, other):
        if not isinstance(other, self.__class__):
            raise(Exception('No se pueden comparar periodos con otros objetos'))

        return self.ano > other.ano or (self.ano == other.ano and self.numero > other.numero)

    def __ge__(self, other):
        if not isinstance(other, self.__class__):
            raise(Exception('No se pueden comparar periodos con otros objetos'))

        return self.ano >= other.ano or (self.ano == other.ano and self.numero >= other.numero)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return self.ano == other.ano and self.numero == other.numero


class Curso(models.Model):
    ramo = models.ForeignKey('academica.Ramo', on_delete=models.PROTECT)
    creditos = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text='se guarda automáticamente en caso de que cambien los créditos de un ramo'
    )

    periodo = models.ForeignKey('Periodo', on_delete=models.PROTECT)
    seccion = models.PositiveSmallIntegerField(default=1)
    cupo = models.PositiveSmallIntegerField()

    fecha_examen = models.DateField(null=True, blank=True)
    fecha_recuperativa = models.DateField(null=True, blank=True)

    estados_curso = [
        (0, 'registrado'),
        (1, 'en progreso'),
        (2, 'terminado'),
    ]
    estado_curso = models.PositiveSmallIntegerField(
        choices=estados_curso, default=0,
        help_text='permite determinar si un curso sigue en progreso después del final del semestre',
    )

    id_ucampus = models.PositiveSmallIntegerField(null=True, blank=True)
    id_SAI = models.PositiveSmallIntegerField(null=True, blank=True)

    # tipos_examenes = [
    #     (0, 'sin examen'),
    #     (1, 'examen normal'),
    #     (2, 'examen reprobatorio'),
    # ]
    # tipo_examen = models.PositiveSmallIntegerField(choices=tipos_examenes)

    nota_aprobacion_curso = models.DecimalField(
        max_digits=3, decimal_places=2, validators=[validatar_nota], default=4)

    tiene_examen = models.BooleanField(default=True)
    examen_reprobatorio = models.BooleanField(default=False)

    nota_minima_examen = models.DecimalField(
        max_digits=3, decimal_places=2, null=True, blank=True,
        default=1, validators=[validatar_nota])

    nota_eximicion_examen = models.DecimalField(
        max_digits=3, decimal_places=2, null=True, blank=True,
        default=1, validators=[validatar_nota])

    ponderacion_examen = models.IntegerField(
        null=True, blank=True, validators=validadores_ponderaciones)

    class Meta:
        db_table = 'curso'
        unique_together = ('ramo', 'periodo', 'seccion')
        ordering = ['periodo', 'ramo']

    def __str__(self):
        return f'{self.ramo.codigo}-{self.seccion} {self.periodo}'

    def nombre_completo(self):
        return f'{self.ramo.codigo} {self.ramo.nombre}'

    @staticmethod
    def post_created(sender, instance, created, *args, **kwargs):
        if created:
            # guardar creditos del ramo cada vez que se crea un curso
            instance.creditos = instance.ramo.creditos
            instance.save()
        return


post_save.connect(Curso.post_created, sender=Curso)


class EstadoEstudianteCurso(models.Model):
    nombre = models.CharField(max_length=50, blank=True, unique=True)
    completado = models.BooleanField()
    aprobado = models.BooleanField()

    id_ucampus = models.PositiveSmallIntegerField(null=True, blank=True)
    id_SAI = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        db_table = 'estado_estudiante_curso'

    def __str__(self):
        return f'{self.nombre}'


class EstudianteCurso(models.Model):
    curso = models.ForeignKey('Curso', on_delete=models.PROTECT, related_name='estudiantes')
    estudiante = models.ForeignKey(
        'persona.Estudiante', on_delete=models.PROTECT, related_name='cursos')

    estado = models.ForeignKey('EstadoEstudianteCurso', on_delete=models.PROTECT)
    nota_recuperativa = models.ForeignKey('Nota', blank=True, null=True, on_delete=models.CASCADE)
    nota_presentacion = models.DecimalField(
        max_digits=3, decimal_places=2, null=True, blank=True)
    nota_examen = models.DecimalField(
        max_digits=3, decimal_places=2, null=True, blank=True)

    nota_final = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)

    def get_nota_presentacion(self):
        nota_presentacion = Decimal(0.0)   # se usa clase Decimal para aritmetica con DecimalField
        actividades_curso = Actividad.objects.filter(curso=self.curso)

        # cancelar ejecución si no hay actividades configuradas en el curso
        if not actividades_curso.exists():
            return
        for actividad in actividades_curso:
            nota_actividad = Decimal(0.0)
            factor_actividad = Decimal(actividad.ponderacion/100)
            evaluaciones = actividad.evaluaciones.all()

            for evaluacion in evaluaciones:
                factor_evaluacion = Decimal(evaluacion.ponderacion / 100)
                try:
                    nota_evaluacion = evaluacion.notas.get(estudiante_curso=self)
                except Nota.DoesNotExist:
                    return  # cancelar si falta alguna nota por ingresar
                nota_ponderada = Decimal(nota_evaluacion.nota * factor_evaluacion)
                nota_actividad += nota_ponderada

            nota_actividad = nota_actividad * factor_actividad
            nota_presentacion += nota_actividad

        # aproximación según art. 36 reglamento de pregrado
        nota_presentacion = round(nota_presentacion, 2)
        nota_presentacion = nota_presentacion.quantize(Decimal('.1'), rounding=ROUND_HALF_UP)

        self.nota_presentacion = nota_presentacion
        self.save()
        return nota_presentacion

    def get_nota_final(self):
        nota_presentacion = self.nota_presentacion
        if nota_presentacion is None:
            return

        nota_eximicion = self.curso.nota_eximicion_examen
        nota_minima = self.curso.nota_minima_examen

        # caso curso sin examen o nota no cumple con requisitos para rendir examen
        if (nota_presentacion > nota_eximicion) or (nota_presentacion < nota_minima) or \
                (self.curso.tiene_examen is False):
            nota_final = self.nota_presentacion

        # los cursos con otra configuración requieren que nota_examen sea ingresada previamente
        if self.nota_examen is None:
            return  # si no se encuentra, cancela la ejecución

        if self.curso.examen_reprobatorio is True:
            nota_final = self.nota_examen

        else:
            ponderacion_examen = self.curso.ponderacion_examen
            factor_examen = Decimal(ponderacion_examen / 100)
            factor_nota_presentacion = (1 - factor_examen)
            nota_final = (self.nota_presentacion * factor_nota_presentacion) + \
                         (self.nota_examen * factor_examen)

        # guardar nota final y cambiar estado
        nota_final = nota_final.quantize(Decimal('.1'), rounding=ROUND_HALF_UP)
        self.nota_final = nota_final

        if nota_final >= self.curso.nota_aprobacion_curso:
            self.estado = EstadoEstudianteCurso.objects.get(nombre="Aprobado")
        else:
            self.estado = EstadoEstudianteCurso.objects.get(nombre="Reprobado")
        self.save()
        return nota_final

    class Meta:
        db_table = 'estudiante_curso'
        unique_together = ('curso', 'estudiante')

    def __str__(self):
        return f'{self.curso} - {self.estudiante} ({self.estado.nombre})'

    def finalizado(self):
        return self.estado.completado


class DocenteCurso(models.Model):
    curso = models.ForeignKey('Curso', on_delete=models.CASCADE, related_name='docentes')
    persona = models.ForeignKey('persona.Persona', on_delete=models.PROTECT)

    roles = [
        (0, 'profesor responsable'),
        (1, 'profesor cátedra'),
        (2, 'profesor práctica'),
        (3, 'profesor colaborador'),
    ]
    rol = models.PositiveSmallIntegerField(choices=roles, default=0)

    class Meta:
        db_table = 'docente_curso'
        unique_together = ('curso', 'persona')

    def __str__(self):
        return f'{self.curso} - {self.persona} ({self.get_rol_display()})'


class AyudanteCurso(models.Model):
    curso = models.ForeignKey('Curso', on_delete=models.CASCADE, related_name='ayudantes')
    persona = models.ForeignKey('persona.Persona', on_delete=models.PROTECT)

    class Meta:
        db_table = 'ayudante_curso'
        unique_together = ('curso', 'persona')

    def __str__(self):
        return f'{self.curso} - {self.persona}'


class CategoriaActividad(models.Model):
    nombre = models.CharField(max_length=50)
    plan = models.ForeignKey('academica.Plan', on_delete=models.PROTECT, blank=True, null=True)

    def __str__(self):
        return f'{self.nombre}  {self.plan if self.plan else ""}'


class Actividad(models.Model):
    curso = models.ForeignKey('Curso', on_delete=models.CASCADE, related_name='actividades')
    ponderacion = models.IntegerField(validators=validadores_ponderaciones)
    categoria_actividad = models.ForeignKey('CategoriaActividad', on_delete=models.PROTECT)

    class Meta:
        unique_together = ('curso', 'categoria_actividad')

    def __str__(self):
        return f'{self.curso}: {self.categoria_actividad} - {self.ponderacion}% '


class Evaluacion(models.Model):
    actividad = models.ForeignKey(
        'Actividad', on_delete=models.CASCADE, related_name='evaluaciones')
    nombre = models.CharField(max_length=200)
    fecha = models.DateField()
    lugar = models.CharField(max_length=200, blank=True, null=True)
    ponderacion = models.IntegerField(validators=validadores_ponderaciones)
    descripcion = models.CharField(max_length=400, blank=True, null=True)

    class Meta:
        db_table = 'evaluacion'

    def __str__(self):
        return f'{self.nombre} {self.ponderacion}% actividad: {self.actividad}'


class Nota(models.Model):
    evaluacion = models.ForeignKey('Evaluacion', on_delete=models.CASCADE, related_name='notas')
    estudiante_curso = models.ForeignKey('EstudianteCurso', on_delete=models.PROTECT)
    nota = models.DecimalField(max_digits=4, decimal_places=2, validators=[validatar_nota])
    fecha_ingreso = models.DateTimeField(auto_now_add=True, editable=False)
    fecha_actualizacion = models.DateTimeField(auto_now=True, editable=False)
    pendiente_ingreso = models.BooleanField(default=False)

    class Meta:
        db_table = 'nota'
        unique_together = ('evaluacion', 'estudiante_curso')

    def __str__(self):
        return f'{self.evaluacion} - {self.estudiante_curso} ({self.nota})'


class Acta(models.Model):
    estudiante_curso = models.OneToOneField(
        'EstudianteCurso', on_delete=models.PROTECT, related_name='acta')

    fecha_envio = models.DateField(auto_now_add=True)
    nota = models.DecimalField(max_digits=4, decimal_places=2)
    # TODO: agregar usuario que envió el acta y modificaciones (acta anterior?)

    class Meta:
        db_table = 'acta'

    def __str__(self):
        return f'{self.estudiante_curso} ({self.nota})'


class Modulo(models.Model):
    hora_inicio = models.TimeField()
    hora_termino = models.TimeField()

    class Meta:
        db_table = 'modulo'

    def __str__(self):
        return f'{self.hora_inicio} - {self.hora_termino}'


class Horario(models.Model):
    curso = models.ForeignKey('Curso', on_delete=models.CASCADE, related_name='horario')

    dias = [
        (1, 'lunes'),
        (2, 'martes'),
        (3, 'miércoles'),
        (4, 'jueves'),
        (5, 'viernes'),
        (6, 'sábado'),
    ]
    dia = models.PositiveSmallIntegerField(choices=dias)
    modulo = models.ForeignKey('Modulo', on_delete=models.PROTECT)

    tipos_horario = [
        (0, 'catedra'),
        (1, 'ayudantía'),
        (2, 'laboratorio'),
        (3, 'taller'),
        (4, 'práctica'),
        (5, 'otro'),
    ]
    tipo_horario = models.PositiveSmallIntegerField(choices=tipos_horario, default=0)

    sala = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = 'horario'
        ordering = ['curso']

    def __str__(self):
        return (
            f'{self.curso} - {self.get_tipo_horario_display()} {self.get_dia_display()} '
            f'{self.modulo}'
        )

    def id_bloque(self):
        return f'{self.dia}-{self.modulo.id}'


class CursosCompartidos(models.Model):
    ramo = models.ForeignKey('academica.Ramo', on_delete=models.PROTECT)
    seccion = models.PositiveSmallIntegerField(default=1)
    plan = models.ForeignKey('academica.Plan', on_delete=models.PROTECT)

    class Meta:
        db_table = 'cursos_compartidos'
        unique_together = ('ramo', 'seccion', 'plan')

    def __str__(self):
        return (
            f'{self.ramo} - {self.seccion} {self.plan}')
