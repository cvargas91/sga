from persona.permisos import GRUPOS
from rest_access_policy import AccessPolicy


class SolicitudPermisos(AccessPolicy):
    statements = [
        {
            'action': ['SolicitudView', 'SolicitudDetalleView'],
            'principal': [f'group:{GRUPOS.SECRETARIO_ACADEMICO}'],
            'effect': 'allow'
        },
        {
            'action': ['SolicitudView'],
            'principal': 'authenticated',
            'effect': 'allow',
            'condition': 'son_solicitudes_propias',
        },
        {
            'action': ['SolicitudDetalleView'],
            'principal': 'authenticated',
            'effect': 'allow',
            'condition': 'es_solicitud_propia',
        }
    ]

    @classmethod
    def scope_fields(cls, request, fields: dict, instance=None) -> dict:
        if not request.user.groups.filter(name=GRUPOS.SECRETARIO_ACADEMICO).exists():
            fields.pop('comentario_revisor', None)
        return fields

    def son_solicitudes_propias(self, request, view, action) -> bool:
        persona = int(request.query_params.get('persona', -1))
        return persona == request.user.get_persona().id

    def es_solicitud_propia(self, request, view, action):
        return view.get_object().estudiante.persona == request.user.get_persona()


class ResolucionPermisos(AccessPolicy):
    statements = [
        {
            'action': ['ResolucionSolicitudView'],
            'principal': [f'group:{GRUPOS.SECRETARIO_ACADEMICO}'],
            'effect': 'allow',
            'condition': 'es_solicitud_pendiente',
        },
        {
            'action': ['DecretoResolucionSolicitudView'],
            'principal': [f'group:{GRUPOS.SECRETARIO_ACADEMICO}'],
            'effect': 'allow'
        }
    ]

    def es_solicitud_pendiente(self, request, view, action):
        return view.get_object().estado in [0, 5]
