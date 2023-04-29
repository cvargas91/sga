from django.forms import FileField, ModelForm
from .models import Pagare


class PagareForm(ModelForm):
    documento_escaneado = FileField(required=True)

    class Meta:
        model = Pagare
        fields = ['documento_escaneado']
