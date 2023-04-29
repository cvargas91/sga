from rest_access_policy import AccessPolicy


class GRUPOS:
    ESTUDIANTES = 'Estudiantes'
    DOCENTES = 'Docentes'
    ADMINISTRADORES = 'Administradores'
    BIBLIOTECA = 'Encargade Biblioteca'
    FINANZAS = 'Encargade Finanzas'
    MATRICULA_PRIMER_ANO = 'Encargade Matrícula Primer Año'
    SECRETARIO_ACADEMICO = 'Secretario Académico'


class TodosSoloLeer(AccessPolicy):
    statements = [
        {
            'action': ['<safe_methods>'],
            'principal': 'authenticated',
            'effect': 'allow',
        },
    ]


class AdministradoresLeerEscribir(AccessPolicy):
    statements = [
        {
            'action': ['*'],
            'principal': [f'group:{GRUPOS.ADMINISTRADORES}', 'admin'],
            'effect': 'allow'
        },
    ]


def consulta_persona_propia(request, opcional=False):
    if 'persona' not in request.query_params:
        return opcional

    return request.user.get_persona().id == int(request.query_params.get('persona'))


class LeerInfoPropia(AccessPolicy):
    statements = [
        {
            'action': ['<safe_methods>'],
            'principal': 'authenticated',
            'effect': 'allow',
            'condition': 'es_info_propia',
        },
    ]

    def es_info_propia(self, request, view, action: str) -> bool:
        return consulta_persona_propia(request)


class LeerInfoPropiaOpcional(AccessPolicy):
    statements = [
        {
            'action': ['<safe_methods>'],
            'principal': 'authenticated',
            'effect': 'allow',
            'condition': 'es_info_propia',
        },
    ]

    def es_info_propia(self, request, view, action: str) -> bool:
        # permitir leer información global
        if 'persona' not in request.query_params:
            return True

        return consulta_persona_propia(request, opcional=True)
