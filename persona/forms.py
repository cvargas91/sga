from django.contrib.admin.widgets import AdminDateWidget
from django.forms import ModelForm, CharField, DateField, EmailField

from .models import Persona


# formulario simplificado para agregar personas, todos los campos son requeridos
class AgregarPersonaForm(ModelForm):
    apellido1 = CharField(required=True)
    fecha_nacimiento = DateField(required=True, widget=AdminDateWidget())
    mail_secundario = EmailField(required=True)

    class Meta:
        model = Persona
        fields = [
            'tipo_identificacion',
            'numero_documento',
            'digito_verificador',
            'nombres',
            'apellido1',
            'apellido2',
            'fecha_nacimiento',
            'sexo',
            'mail_secundario',
        ]
