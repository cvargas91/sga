from django.db import models


class ModeloRegistraFechas(models.Model):
    creado = models.DateTimeField(auto_now_add=True, editable=False)
    modificado = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        abstract = True


class RegionManager(models.Manager):
    def get_by_natural_key(self, codigo_demre):
        return self.get(codigo_demre=codigo_demre)


class Region(models.Model):
    nombre = models.CharField(max_length=200)
    codigo_demre = models.CharField(max_length=50, null=True, blank=True, unique=True)

    class Meta:
        db_table = 'region'

    def __str__(self):
        return f'{self.nombre}'

    objects = RegionManager()

    def natural_key(self):
        return (self.codigo_demre, )

    # sobreescribir guardado para asegurar que se puedan guardar nulos y así permitir valores únicos
    def save(self, *args, **kwargs):
        if not self.codigo_demre:
            self.codigo_demre = None

        super().save(*args, **kwargs)


class ProvinciaManager(models.Manager):
    def get_by_natural_key(self, codigo_demre):
        return self.get(codigo_demre=codigo_demre)


class Provincia(models.Model):
    nombre = models.CharField(max_length=200)
    region = models.ForeignKey('Region', on_delete=models.PROTECT, related_name='provincias')
    codigo_demre = models.CharField(max_length=50, null=True, blank=True, unique=True)

    class Meta:
        db_table = 'provincia'

    def __str__(self):
        return f'{self.nombre}'

    def natural_key(self):
        return (self.codigo_demre, )

    objects = ProvinciaManager()

    # sobreescribir guardado para asegurar que se puedan guardar nulos y así permitir valores únicos
    def save(self, *args, **kwargs):
        if not self.codigo_demre:
            self.codigo_demre = None

        super().save(*args, **kwargs)


class Comuna(models.Model):
    nombre = models.CharField(max_length=200)
    region = models.ForeignKey('Region', on_delete=models.PROTECT, related_name='comunas')
    provincia = models.ForeignKey(
        'Provincia', on_delete=models.PROTECT, related_name='comunas', null=True)

    codigo_demre = models.CharField(max_length=50, null=True, blank=True, unique=True)

    class Meta:
        db_table = 'comuna'

    def __str__(self):
        return f'{self.nombre}'

    # sobreescribir guardado para asegurar que se puedan guardar nulos y así permitir valores únicos
    def save(self, *args, **kwargs):
        if not self.codigo_demre:
            self.codigo_demre = None

        super().save(*args, **kwargs)


class Pais(models.Model):
    nombre = models.CharField(max_length=200)

    codigo_demre = models.CharField(max_length=50, null=True, blank=True, unique=True)
    codigo_mineduc = models.CharField(max_length=50, null=True, blank=True, unique=True)

    class Meta:
        db_table = 'pais'

    def __str__(self):
        return f'{self.nombre}'

    # sobreescribir guardado para asegurar que se puedan guardar nulos y así permitir valores únicos
    def save(self, *args, **kwargs):
        if not self.codigo_demre:
            self.codigo_demre = None
        if not self.codigo_mineduc:
            self.codigo_mineduc = None

        super().save(*args, **kwargs)


class Sede(models.Model):
    nombre = models.CharField(max_length=200)
    direccion_comuna = models.ForeignKey('general.Comuna', on_delete=models.PROTECT)
    direccion_texto = models.CharField(max_length=200)

    class Meta:
        db_table = 'sede'

    def __str__(self):
        return f'{self.nombre}'


class Espacio(models.Model):
    nombre = models.CharField(max_length=200)
    sede = models.ForeignKey('Sede', on_delete=models.PROTECT)

    capacidad = models.PositiveSmallIntegerField()

    class Meta:
        db_table = 'espacio'

    def __str__(self):
        return f'{self.nombre}'
