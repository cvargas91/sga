from django.db import models


class Departamento(models.Model):
    nombre = models.CharField(max_length=100)

    id_ucampus = models.PositiveSmallIntegerField(null=True, blank=True)
    id_SAI = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        db_table = 'departamento'

    def __str__(self):
        return f'{self.nombre}'


class Carrera(models.Model):
    departamento = models.ForeignKey('Departamento', on_delete=models.PROTECT)
    nombre = models.CharField(max_length=200)

    tipos_carreras = [
        (0, 'carrera'),  # carreras de pregrado
        (1, 'diplomado'),
        (2, 'curso de especializacion'),
    ]
    tipo_carrera = models.PositiveSmallIntegerField(choices=tipos_carreras)

    id_ucampus = models.PositiveSmallIntegerField(null=True, blank=True)
    codigo_ucampus = models.CharField(max_length=4, blank=True)
    id_SAI = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        db_table = 'carrera'

    def __str__(self):
        return f'{self.nombre}'


class Plan(models.Model):
    carrera = models.ForeignKey('Carrera', on_delete=models.PROTECT)
    version = models.PositiveSmallIntegerField()

    link_decreto = models.CharField(
        max_length=300, blank=True,
        help_text='''
            (solo para matrícula educación continua) ID del documento en google drive para generar
            link al decreto en matrícula.<br>
            Para obtenerlo se debe abrir el documento en una ventana nueva y en la url se encuentra
            el id.<br>
            e.g: en <a>https://drive.google.com/file/d/107vKi5LWk1fH2CwRLO_O-aC7SKBhkU84/view</a>
            el id es <b>107vKi5LWk1fH2CwRLO_O-aC7SKBhkU84</b>.
        ''',
    )

    codigo_demre = models.CharField(max_length=100, blank=True)
    codigo_sies = models.CharField(max_length=100, blank=True)

    id_ucampus = models.CharField(max_length=100, blank=True)
    id_SAI = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        db_table = 'plan'
        unique_together = ('carrera', 'version')
        verbose_name_plural = 'Planes'

    def __str__(self):
        return f'{self.carrera} v{self.version}'


class Ramo(models.Model):
    departamento = models.ForeignKey(
        'Departamento', on_delete=models.PROTECT, null=True, blank=True)
    codigo = models.CharField(unique=True, max_length=20)
    nombre = models.CharField(max_length=200)
    creditos = models.IntegerField()

    requisitos = models.ManyToManyField(
        'self', through='Requisito', related_name='+', symmetrical=False)
    requisito_creditaje = models.PositiveSmallIntegerField(null=True, blank=True)
    requisito_nivel = models.PositiveSmallIntegerField(null=True, blank=True)
    equivalencias = models.ManyToManyField('self')

    id_ucampus = models.PositiveSmallIntegerField(null=True, blank=True)
    id_SAI = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        db_table = 'ramo'
        ordering = ['departamento', 'codigo']

    def __str__(self):
        return f'{self.codigo} {self.nombre}'


class Malla(models.Model):
    plan = models.ForeignKey('Plan', on_delete=models.PROTECT)
    semestre = models.PositiveSmallIntegerField(
        help_text='semestre en el cuál se debe tomar este ramo/electivo')

    tipos_formacion = [
        (0, 'formación básica'),
        (1, 'formación transversal'),
        (2, 'formación especializada'),
    ]
    tipo_formacion = models.PositiveSmallIntegerField(choices=tipos_formacion)

    class Meta:
        abstract = True


class MallaObligatoria(Malla):
    ramo = models.ForeignKey('Ramo', on_delete=models.PROTECT)

    class Meta:
        db_table = 'malla_obligatoria'
        default_related_name = 'malla_obligatoria'
        unique_together = ('plan', 'ramo')

    def __str__(self):
        return f'{self.plan} - S{self.semestre} - {self.ramo}'


class ConjuntoRamos(models.Model):
    nombre = models.CharField(unique=True, max_length=200)
    ramos = models.ManyToManyField('Ramo', blank=True)

    class Meta:
        db_table = 'conjunto_ramos'

    def __str__(self):
        return f'{self.nombre}'


class MallaElectiva(Malla):
    conjunto_ramos = models.ForeignKey('ConjuntoRamos', on_delete=models.PROTECT)
    nombre = models.CharField(max_length=200)
    creditos = models.PositiveSmallIntegerField()

    class Meta:
        db_table = 'malla_electiva'
        default_related_name = 'malla_electiva'

    def __str__(self):
        return f'{self.plan} - S{self.semestre} - {self.nombre}'


class Requisito(models.Model):
    ramo = models.ForeignKey(
        'Ramo', on_delete=models.CASCADE,
        help_text='ramo que tiene el requisito')
    requisito = models.ForeignKey('Ramo', on_delete=models.CASCADE, related_name='+')

    class Meta:
        db_table = 'requisito'

    def __str__(self):
        return f'{self.ramo.codigo} tiene req {self.requisito.codigo}'
