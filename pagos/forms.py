from django.forms import CharField, ModelForm
from .models import OrdenCompra


class OrdenCompraForm(ModelForm):
    folio_dte = CharField(required=True)

    class Meta:
        model = OrdenCompra
        fields = ['folio_dte', 'comentario', 'forma_pago']
