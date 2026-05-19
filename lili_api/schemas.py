# Documentación OpenAPI con drf-spectacular.
from lili_api.serializers import (
    AutorSerializer,
    LibroSerializer,
    UsuarioLiliSerializer,
    UsuarioLiliPublicoSerializer,
    SerieSerializer,
    CategoriaSerializer,
    UsuarioLibroSerializer,
    AmistadSerializer,
    PrestamoSerializer,
    NotificacionSerializer,
    LibroCategoriaSerializer,
    EditorialSerializer,
    ContactoSerializer,
)

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiResponse,
    OpenApiParameter,
    OpenApiExample,
    inline_serializer,
)
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers
from drf_spectacular.extensions import OpenApiAuthenticationExtension

class CookieJWTAuthenticationExtension(OpenApiAuthenticationExtension):
    target_class = "lili_api.authentication.authentication.CookieJWTAuthentication"
    name = "cookieJWTAuth"

    def get_security_requirement(self, auto_schema):
        return {"bearerAuth": []}

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }


# ──────────────────────────────────────────────
# Respuestas reutilizables
# ──────────────────────────────────────────────

R_401 = OpenApiResponse(description="No autenticado. Se requiere token de acceso.")
R_403 = OpenApiResponse(description="Permiso denegado. No tienes acceso a este recurso.")
R_404 = OpenApiResponse(description="Recurso no encontrado.")
R_400 = OpenApiResponse(description="Datos de entrada inválidos.")


def mensaje_ok(texto: str) -> OpenApiResponse:
    """Respuesta 200 con un campo 'mensaje' de texto libre."""
    return OpenApiResponse(
        response=inline_serializer(
            name=f"Mensaje_{texto[:20].replace(' ', '_')}",
            fields={"mensaje": serializers.CharField()},
        ),
        description=texto,
    )


def error_response(texto: str) -> OpenApiResponse:
    return OpenApiResponse(
        response=inline_serializer(
            name=f"Error_{texto[:20].replace(' ', '_')}",
            fields={"error": serializers.CharField()},
        ),
        description=texto,
    )


# ──────────────────────────────────────────────
# AUTOR
# ──────────────────────────────────────────────

autor_schema = extend_schema_view(
    list=extend_schema(
        summary="Listar autores",
        description=(
            "Devuelve todos los autores registrados. "
            "Admite búsqueda por `nombre` y ordenación."
        ),
        tags=["Autores"],
        responses={200: AutorSerializer(many=True), 401: R_401},
    ),
    retrieve=extend_schema(
        summary="Obtener un autor",
        description="Devuelve los datos de un autor concreto por su ID.",
        tags=["Autores"],
        responses={200: AutorSerializer, 401: R_401, 404: R_404},
    ),
    create=extend_schema(
        summary="Crear autor",
        description="Crea un nuevo autor. Requiere autenticación.",
        tags=["Autores"],
        responses={201: AutorSerializer, 400: R_400, 401: R_401},
    ),
    update=extend_schema(
        summary="Actualizar autor (completo)",
        description="Reemplaza todos los campos de un autor. Solo admins.",
        tags=["Autores"],
        responses={200: AutorSerializer, 400: R_400, 401: R_401, 403: R_403, 404: R_404},
    ),
    partial_update=extend_schema(
        summary="Actualizar autor (parcial)",
        description="Modifica uno o más campos de un autor. Solo admins.",
        tags=["Autores"],
        responses={200: AutorSerializer, 400: R_400, 401: R_401, 403: R_403, 404: R_404},
    ),
    destroy=extend_schema(
        summary="Eliminar autor",
        description="Elimina un autor por su ID. Solo admins.",
        tags=["Autores"],
        responses={204: None, 401: R_401, 403: R_403, 404: R_404},
    ),
)


# ──────────────────────────────────────────────
# EDITORIAL
# ──────────────────────────────────────────────

editorial_schema = extend_schema_view(
    list=extend_schema(
        summary="Listar editoriales",
        description="Devuelve todas las editoriales. Admite búsqueda por `nombre`.",
        tags=["Editoriales"],
        responses={200: EditorialSerializer(many=True), 401: R_401},
    ),
    retrieve=extend_schema(
        summary="Obtener una editorial",
        tags=["Editoriales"],
        responses={200: EditorialSerializer, 401: R_401, 404: R_404},
    ),
    create=extend_schema(
        summary="Crear editorial",
        tags=["Editoriales"],
        responses={201: EditorialSerializer, 400: R_400, 401: R_401},
    ),
    update=extend_schema(
        summary="Actualizar editorial (completo)",
        tags=["Editoriales"],
        responses={200: EditorialSerializer, 401: R_401, 403: R_403, 404: R_404},
    ),
    partial_update=extend_schema(
        summary="Actualizar editorial (parcial). Solo admins.",
        tags=["Editoriales"],
        responses={200: EditorialSerializer, 401: R_401, 403: R_403, 404: R_404},
    ),
    destroy=extend_schema(
        summary="Eliminar editorial. Solo admins.",
        tags=["Editoriales"],
        responses={204: None, 401: R_401, 403: R_403, 404: R_404},
    ),
)


# ──────────────────────────────────────────────
# LIBRO
# ──────────────────────────────────────────────

_importar_schema = extend_schema(
    summary="Importar libro desde Open Library",
    description=(
        "Busca un libro por ISBN en Open Library y lo guarda en la base de datos. "
        "Devuelve 409 si el libro ya existe. "
        "Devuelve 404 si no se encuentra en Open Library."
    ),
    tags=["Libros"],
    request=inline_serializer(
        name="ImportarLibroRequest",
        fields={
            "isbn": serializers.CharField(help_text="ISBN del libro a importar"),
        },
    ),
    responses={
        201: LibroSerializer,
        400: error_response("ISBN no proporcionado"),
        404: R_404,
        409: OpenApiResponse(description="El libro ya existe en la base de datos."),
        500: OpenApiResponse(description="Error al guardar el libro."),
    },
)

libro_schema = extend_schema_view(
    list=extend_schema(
        summary="Listar libros",
        description=(
            "Devuelve el catálogo completo de libros con sus autores y editorial. "
            "Admite filtros avanzados (`LibroFilter`), búsqueda por título, sinopsis, "
            "autor o editorial, y ordenación."
        ),
        tags=["Libros"],
        responses={200: LibroSerializer(many=True), 401: R_401},
    ),
    retrieve=extend_schema(
        summary="Obtener un libro",
        tags=["Libros"],
        responses={200: LibroSerializer, 401: R_401, 404: R_404},
    ),
    create=extend_schema(
        summary="Crear libro",
        tags=["Libros"],
        responses={201: LibroSerializer, 400: R_400, 401: R_401},
    ),
    update=extend_schema(
        summary="Actualizar libro (completo)",
        tags=["Libros"],
        responses={200: LibroSerializer, 401: R_401, 403: R_403, 404: R_404},
    ),
    partial_update=extend_schema(
        summary="Actualizar libro (parcial). Solo admins.",
        tags=["Libros"],
        responses={200: LibroSerializer, 401: R_401, 403: R_403, 404: R_404},
    ),
    destroy=extend_schema(
        summary="Eliminar libro. Solo admins.",
        tags=["Libros"],
        responses={204: None, 401: R_401, 403: R_403, 404: R_404},
    ),
    importar=_importar_schema,
)


# ──────────────────────────────────────────────
# USUARIO LILI
# ──────────────────────────────────────────────

usuario_lili_schema = extend_schema_view(
    list=extend_schema(
        summary="Listar usuarios",
        description=(
            "Devuelve la lista de usuarios (excluye staff). "
            "Los admins reciben `UsuarioLiliSerializer` completo; "
            "el resto recibe `UsuarioLiliPublicoSerializer`."
        ),
        tags=["Usuarios"],
        responses={200: UsuarioLiliPublicoSerializer(many=True), 401: R_401},
    ),
    retrieve=extend_schema(
        summary="Obtener un usuario",
        description=(
            "El propio usuario y los admins reciben el perfil completo. "
            "Otros usuarios autenticados reciben la versión pública."
        ),
        tags=["Usuarios"],
        responses={
            200: UsuarioLiliSerializer,
            401: R_401,
            404: R_404,
        },
    ),
    create=extend_schema(
        summary="Crear usuario",
        tags=["Usuarios"],
        responses={201: UsuarioLiliSerializer, 400: R_400},
    ),
    update=extend_schema(
        summary="Actualizar usuario (completo)",
        description="Solo el propio usuario o un admin pueden actualizar el perfil.",
        tags=["Usuarios"],
        responses={200: UsuarioLiliSerializer, 401: R_401, 403: R_403, 404: R_404},
    ),
    partial_update=extend_schema(
        summary="Actualizar usuario (parcial)",
        tags=["Usuarios"],
        responses={200: UsuarioLiliSerializer, 401: R_401, 403: R_403, 404: R_404},
    ),
    destroy=extend_schema(
        summary="Eliminar usuario",
        tags=["Usuarios"],
        responses={204: None, 401: R_401, 403: R_403, 404: R_404},
    ),
)


# ──────────────────────────────────────────────
# SERIE
# ──────────────────────────────────────────────

serie_schema = extend_schema_view(
    list=extend_schema(
        summary="Listar series",
        description=(
            "Devuelve las series del usuario autenticado. "
            "Los admins ven todas las series."
        ),
        tags=["Series"],
        responses={200: SerieSerializer(many=True), 401: R_401},
    ),
    retrieve=extend_schema(
        summary="Obtener una serie",
        tags=["Series"],
        responses={200: SerieSerializer, 401: R_401, 403: R_403, 404: R_404},
    ),
    create=extend_schema(
        summary="Crear serie",
        tags=["Series"],
        responses={201: SerieSerializer, 400: R_400, 401: R_401},
    ),
    update=extend_schema(
        summary="Actualizar serie (completo)",
        tags=["Series"],
        responses={200: SerieSerializer, 401: R_401, 403: R_403, 404: R_404},
    ),
    partial_update=extend_schema(
        summary="Actualizar serie (parcial)",
        tags=["Series"],
        responses={200: SerieSerializer, 401: R_401, 403: R_403, 404: R_404},
    ),
    destroy=extend_schema(
        summary="Eliminar serie",
        tags=["Series"],
        responses={204: None, 401: R_401, 403: R_403, 404: R_404},
    ),
)


# ──────────────────────────────────────────────
# CATEGORÍA
# ──────────────────────────────────────────────

_publicas_schema = extend_schema(
    summary="Listar categorías públicas",
    description=(
        "Devuelve todas las categorías con `publica=True`. "
        "Filtrable por `?usuario={id}`."
    ),
    tags=["Categorías"],
    parameters=[
        OpenApiParameter(
            name="usuario",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Filtra las categorías públicas de un usuario concreto.",
        )
    ],
    responses={200: CategoriaSerializer(many=True), 401: R_401},
)

categoria_schema = extend_schema_view(
    list=extend_schema(
        summary="Listar categorías",
        description=(
            "Devuelve las categorías del usuario autenticado. "
            "Los admins ven todas. Filtrable por `publica` y `usuario`."
        ),
        tags=["Categorías"],
        responses={200: CategoriaSerializer(many=True), 401: R_401},
    ),
    retrieve=extend_schema(
        summary="Obtener una categoría",
        tags=["Categorías"],
        responses={200: CategoriaSerializer, 401: R_401, 403: R_403, 404: R_404},
    ),
    create=extend_schema(
        summary="Crear categoría",
        tags=["Categorías"],
        responses={201: CategoriaSerializer, 400: R_400, 401: R_401},
    ),
    update=extend_schema(
        summary="Actualizar categoría (completo)",
        tags=["Categorías"],
        responses={200: CategoriaSerializer, 401: R_401, 403: R_403, 404: R_404},
    ),
    partial_update=extend_schema(
        summary="Actualizar categoría (parcial)",
        tags=["Categorías"],
        responses={200: CategoriaSerializer, 401: R_401, 403: R_403, 404: R_404},
    ),
    destroy=extend_schema(
        summary="Eliminar categoría",
        tags=["Categorías"],
        responses={204: None, 401: R_401, 403: R_403, 404: R_404},
    ),
    publicas=_publicas_schema,
)


# ──────────────────────────────────────────────
# USUARIO LIBRO
# ──────────────────────────────────────────────

_cambiar_estado_schema = extend_schema(
    summary="Cambiar estado de lectura",
    description=(
        "Actualiza el estado de lectura de un `UsuarioLibro`. "
        "Valores válidos: los definidos en `UsuarioLibro.EstadosLectura`."
    ),
    tags=["Biblioteca personal"],
    request=inline_serializer(
        name="CambiarEstadoRequest",
        fields={"estado": serializers.CharField(help_text="Nuevo estado de lectura")},
    ),
    responses={
        200: inline_serializer(
            name="CambiarEstadoResponse",
            fields={"estado": serializers.CharField()},
        ),
        400: error_response("Estado no válido"),
        401: R_401,
        403: R_403,
        404: R_404,
    },
)

_cambiar_favorito_schema = extend_schema(
    summary="Alternar favorito",
    description="Cambia el campo `favorito` del `UsuarioLibro` al valor opuesto.",
    tags=["Biblioteca personal"],
    request=None,
    responses={
        200: inline_serializer(
            name="CambiarFavoritoResponse",
            fields={
                "mensaje": serializers.CharField(),
                "data": serializers.DictField(),
            },
        ),
        401: R_401,
        403: R_403,
        404: R_404,
    },
)

_leyendo_schema = extend_schema(
    summary="Libros en estado 'leyendo'",
    description="Devuelve los libros que el usuario tiene marcados como 'leyendo'.",
    tags=["Biblioteca personal"],
    responses={200: UsuarioLibroSerializer(many=True), 401: R_401},
)

_favoritos_schema = extend_schema(
    summary="Libros favoritos",
    description="Devuelve los libros marcados como favoritos por el usuario.",
    tags=["Biblioteca personal"],
    responses={200: UsuarioLibroSerializer(many=True), 401: R_401},
)

_anadir_schema = extend_schema(
    summary="Añadir libro a una categoría",
    description=(
        "Añade un libro a la biblioteca del usuario y lo asocia a una categoría. "
        "Si la categoría no existe se crea automáticamente. "
        "Si el libro ya estaba en la biblioteca se reutiliza el registro existente."
    ),
    tags=["Biblioteca personal"],
    request=inline_serializer(
        name="AnadirRequest",
        fields={
            "libro_id": serializers.IntegerField(help_text="ID del libro a añadir"),
            "categoria": serializers.CharField(
                help_text="Nombre o ID (int) de la categoría"
            ),
        },
    ),
    responses={
        201: inline_serializer(
            name="AnadirResponse",
            fields={
                "usuario_libro": serializers.DictField(),
                "categoria": serializers.DictField(),
                "relacion": LibroCategoriaSerializer,
            },
        ),
        200: OpenApiResponse(description="El libro ya estaba en esa categoría."),
        400: error_response("Faltan libro_id o categoría"),
        401: R_401,
    },
    examples=[
        OpenApiExample(
            "Añadir por nombre de categoría",
            value={"libro_id": 42, "categoria": "Ciencia Ficción"},
            request_only=True,
        ),
        OpenApiExample(
            "Añadir por ID de categoría",
            value={"libro_id": 42, "categoria": 7},
            request_only=True,
        ),
    ],
)

_anadir_serie_schema = extend_schema(
    summary="Asignar libro a una serie",
    description=(
        "Vincula un `UsuarioLibro` a una serie y establece su número en ella. "
        "Si la serie no existe se crea automáticamente."
    ),
    tags=["Biblioteca personal"],
    request=inline_serializer(
        name="AnadirSerieRequest",
        fields={
            "serie": serializers.CharField(
                help_text="Nombre o ID (int) de la serie"
            ),
            "num_en_serie": serializers.IntegerField(
                required=False, help_text="Posición del libro dentro de la serie"
            ),
        },
    ),
    responses={
        201: inline_serializer(
            name="AnadirSerieResponse",
            fields={
                "usuario_libro": serializers.DictField(),
                "serie": serializers.DictField(),
            },
        ),
        400: error_response("Falta el campo serie"),
        401: R_401,
        403: R_403,
        404: R_404,
    },
)

_cambiar_publico_schema = extend_schema(
    summary="Alternar público",
    description="Cambia el campo `publico` del `UsuarioLibro` al valor opuesto.",
    tags=["Biblioteca personal"],
    request=None,
    responses={
        200: inline_serializer(
            name="CambiarPublicoResponse",
            fields={
                "mensaje": serializers.CharField(),
                "data": serializers.DictField(),
            },
        ),
        401: R_401,
        403: R_403,
        404: R_404,
    },
)

_publicos_schema = extend_schema(
    summary="Libros públicos",
    description=(
        "Devuelve los libros marcados como públicos. "
        "Filtrable por `?usuario_id={id}` para obtener los de un usuario concreto."
    ),
    tags=["Biblioteca personal"],
    parameters=[
        OpenApiParameter(
            name="usuario_id",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            required=False,
            description="ID del usuario cuyos libros públicos se quieren obtener.",
        )
    ],
    responses={200: UsuarioLibroSerializer(many=True), 401: R_401},
)

usuario_libro_schema = extend_schema_view(
    list=extend_schema(
        summary="Listar biblioteca personal",
        description=(
            "Devuelve los libros de la biblioteca del usuario autenticado. "
            "Los admins ven todos los registros. "
            "Admite filtros por estado, favorito, serie y categoría."
        ),
        tags=["Biblioteca personal"],
        responses={200: UsuarioLibroSerializer(many=True), 401: R_401},
    ),
    retrieve=extend_schema(
        summary="Obtener un libro de la biblioteca",
        tags=["Biblioteca personal"],
        responses={200: UsuarioLibroSerializer, 401: R_401, 403: R_403, 404: R_404},
    ),
    create=extend_schema(
        summary="Añadir libro a la biblioteca",
        tags=["Biblioteca personal"],
        responses={201: UsuarioLibroSerializer, 400: R_400, 401: R_401},
    ),
    update=extend_schema(
        summary="Actualizar libro de la biblioteca (completo)",
        tags=["Biblioteca personal"],
        responses={200: UsuarioLibroSerializer, 401: R_401, 403: R_403, 404: R_404},
    ),
    partial_update=extend_schema(
        summary="Actualizar libro de la biblioteca (parcial)",
        tags=["Biblioteca personal"],
        responses={200: UsuarioLibroSerializer, 401: R_401, 403: R_403, 404: R_404},
    ),
    destroy=extend_schema(
        summary="Eliminar libro de la biblioteca",
        tags=["Biblioteca personal"],
        responses={204: None, 401: R_401, 403: R_403, 404: R_404},
    ),
    cambiar_estado=_cambiar_estado_schema,
    cambiar_favorito=_cambiar_favorito_schema,
    leyendo=_leyendo_schema,
    favoritos=_favoritos_schema,
    anadir=_anadir_schema,
    anadir_serie=_anadir_serie_schema,
    cambiar_publico=_cambiar_publico_schema,
    publicos=_publicos_schema,
)


# ──────────────────────────────────────────────
# AMISTAD
# ──────────────────────────────────────────────

_aceptar_schema = extend_schema(
    summary="Aceptar solicitud de amistad",
    description="Cambia el estado de la amistad a ACEPTADA.",
    tags=["Amistades"],
    request=None,
    responses={
        200: mensaje_ok("Amistad aceptada"),
        401: R_401,
        403: R_403,
        404: R_404,
    },
)

_ignorar_schema = extend_schema(
    summary="Ignorar solicitud de amistad",
    description="Revierte el estado de la amistad a SIN_SOLICITAR.",
    tags=["Amistades"],
    request=None,
    responses={
        200: mensaje_ok("Amistad ignorada"),
        401: R_401,
        403: R_403,
        404: R_404,
    },
)

_bloquear_schema = extend_schema(
    summary="Bloquear usuario",
    description="Cambia el estado de la amistad a BLOQUEADA.",
    tags=["Amistades"],
    request=None,
    responses={
        200: mensaje_ok("Amistad bloqueada"),
        401: R_401,
        403: R_403,
        404: R_404,
    },
)

_pendientes_schema = extend_schema(
    summary="Solicitudes de amistad pendientes",
    description="Devuelve las amistades en estado 'pendiente' del usuario autenticado.",
    tags=["Amistades"],
    responses={200: AmistadSerializer(many=True), 401: R_401},
)

amistad_schema = extend_schema_view(
    list=extend_schema(
        summary="Listar amistades",
        description=(
            "Devuelve las amistades del usuario autenticado (como usuario_a o usuario_b). "
            "Los admins ven todas."
        ),
        tags=["Amistades"],
        responses={200: AmistadSerializer(many=True), 401: R_401},
    ),
    retrieve=extend_schema(
        summary="Obtener una amistad",
        tags=["Amistades"],
        responses={200: AmistadSerializer, 401: R_401, 403: R_403, 404: R_404},
    ),
    create=extend_schema(
        summary="Enviar solicitud de amistad",
        tags=["Amistades"],
        responses={201: AmistadSerializer, 400: R_400, 401: R_401},
    ),
    update=extend_schema(
        summary="Actualizar amistad (completo)",
        tags=["Amistades"],
        responses={200: AmistadSerializer, 401: R_401, 403: R_403, 404: R_404},
    ),
    partial_update=extend_schema(
        summary="Actualizar amistad (parcial)",
        tags=["Amistades"],
        responses={200: AmistadSerializer, 401: R_401, 403: R_403, 404: R_404},
    ),
    destroy=extend_schema(
        summary="Eliminar amistad",
        tags=["Amistades"],
        responses={204: None, 401: R_401, 403: R_403, 404: R_404},
    ),
    aceptar=_aceptar_schema,
    ignorar=_ignorar_schema,
    bloquear=_bloquear_schema,
    pendientes=_pendientes_schema,
)


# ──────────────────────────────────────────────
# PRÉSTAMO
# ──────────────────────────────────────────────

_prestar_schema = extend_schema(
    summary="Aceptar préstamo",
    description=(
        "Marca el préstamo como ACTIVO y registra la `fecha_inicio`. "
        "Solo pueden hacerlo el propietario del libro o el prestatario."
    ),
    tags=["Préstamos"],
    request=None,
    responses={
        200: mensaje_ok("Préstamo aceptado"),
        401: R_401,
        403: R_403,
        404: R_404,
    },
)

_devolver_schema = extend_schema(
    summary="Devolver préstamo",
    description=(
        "Marca el préstamo como DEVUELTO y registra la `fecha_fin`. "
        "Solo pueden hacerlo el propietario o el prestatario."
    ),
    tags=["Préstamos"],
    request=None,
    responses={
        200: mensaje_ok("Préstamo devuelto"),
        401: R_401,
        403: R_403,
        404: R_404,
    },
)

_recibidos_schema = extend_schema(
    summary="Préstamos recibidos activos",
    description="Devuelve los préstamos activos en los que el usuario es prestatario.",
    tags=["Préstamos"],
    responses={200: PrestamoSerializer(many=True), 401: R_401},
)

_cedidos_schema = extend_schema(
    summary="Préstamos cedidos activos",
    description="Devuelve los préstamos activos en los que el usuario es propietario del libro.",
    tags=["Préstamos"],
    responses={200: PrestamoSerializer(many=True), 401: R_401},
)

_solicitados_por_mi_schema = extend_schema(
    summary="Préstamos solicitados por mí",
    description="Devuelve las solicitudes de préstamo enviadas por el usuario autenticado.",
    tags=["Préstamos"],
    responses={200: PrestamoSerializer(many=True), 401: R_401},
)

_solicitados_a_mi_schema = extend_schema(
    summary="Préstamos solicitados a mí",
    description="Devuelve las solicitudes de préstamo recibidas por el usuario autenticado.",
    tags=["Préstamos"],
    responses={200: PrestamoSerializer(many=True), 401: R_401},
)

_crear_prestamo_prestador_schema = extend_schema(
    summary="Crear préstamo como prestador",
    description=(
        "El propietario de un libro inicia directamente un préstamo activo a otro usuario. "
        "Crea el préstamo en estado ACTIVO con `fecha_inicio` de hoy. "
        "Si el prestatario no tiene el libro en su biblioteca, se le añade automáticamente."
    ),
    tags=["Préstamos"],
    request=inline_serializer(
        name="CrearPrestamoPrestadorRequest",
        fields={
            "usuario_libro_id": serializers.IntegerField(
                help_text="ID del UsuarioLibro del prestador"
            ),
            "prestatario_id": serializers.IntegerField(
                help_text="ID del usuario que recibirá el préstamo"
            ),
        },
    ),
    responses={
        201: PrestamoSerializer,
        400: error_response("Faltan campos o el libro ya tiene un préstamo activo"),
        401: R_401,
        403: R_403,
        404: R_404,
    },
)

prestamo_schema = extend_schema_view(
    list=extend_schema(
        summary="Listar préstamos",
        description=(
            "Devuelve los préstamos donde el usuario participa como propietario o prestatario. "
            "Los admins ven todos."
        ),
        tags=["Préstamos"],
        responses={200: PrestamoSerializer(many=True), 401: R_401},
    ),
    retrieve=extend_schema(
        summary="Obtener un préstamo",
        tags=["Préstamos"],
        responses={200: PrestamoSerializer, 401: R_401, 403: R_403, 404: R_404},
    ),
    create=extend_schema(
        summary="Solicitar préstamo",
        tags=["Préstamos"],
        responses={201: PrestamoSerializer, 400: R_400, 401: R_401},
    ),
    update=extend_schema(
        summary="Actualizar préstamo (completo)",
        tags=["Préstamos"],
        responses={200: PrestamoSerializer, 401: R_401, 403: R_403, 404: R_404},
    ),
    partial_update=extend_schema(
        summary="Actualizar préstamo (parcial)",
        tags=["Préstamos"],
        responses={200: PrestamoSerializer, 401: R_401, 403: R_403, 404: R_404},
    ),
    destroy=extend_schema(
        summary="Cancelar préstamo",
        tags=["Préstamos"],
        responses={204: None, 401: R_401, 403: R_403, 404: R_404},
    ),
    prestar=_prestar_schema,
    devolver=_devolver_schema,
    recibidos=_recibidos_schema,
    cedidos=_cedidos_schema,
    solicitados_por_mi=_solicitados_por_mi_schema,
    solicitados_a_mi=_solicitados_a_mi_schema,
    crear_prestamo_prestador=_crear_prestamo_prestador_schema,
)


# ──────────────────────────────────────────────
# NOTIFICACIÓN
# ──────────────────────────────────────────────

notificacion_schema = extend_schema_view(
    list=extend_schema(
        summary="Listar notificaciones",
        description=(
            "Devuelve las notificaciones del usuario autenticado. "
            "Los admins ven todas. Filtrable por `leida` y `tipo`."
        ),
        tags=["Notificaciones"],
        responses={200: NotificacionSerializer(many=True), 401: R_401},
    ),
    retrieve=extend_schema(
        summary="Obtener una notificación",
        tags=["Notificaciones"],
        responses={200: NotificacionSerializer, 401: R_401, 403: R_403, 404: R_404},
    ),
    create=extend_schema(
        summary="Crear notificación",
        tags=["Notificaciones"],
        responses={201: NotificacionSerializer, 400: R_400, 401: R_401},
    ),
    update=extend_schema(
        summary="Actualizar notificación (completo)",
        tags=["Notificaciones"],
        responses={200: NotificacionSerializer, 401: R_401, 403: R_403, 404: R_404},
    ),
    partial_update=extend_schema(
        summary="Marcar notificación como leída (parcial)",
        description="Útil para actualizar solo el campo `leida`.",
        tags=["Notificaciones"],
        responses={200: NotificacionSerializer, 401: R_401, 403: R_403, 404: R_404},
    ),
    destroy=extend_schema(
        summary="Eliminar notificación",
        tags=["Notificaciones"],
        responses={204: None, 401: R_401, 403: R_403, 404: R_404},
    ),
)


# ──────────────────────────────────────────────
# LIBRO CATEGORÍA
# ──────────────────────────────────────────────

libro_categoria_schema = extend_schema_view(
    list=extend_schema(
        summary="Listar relaciones libro-categoría",
        description=(
            "Devuelve las relaciones entre libros de la biblioteca y categorías "
            "del usuario autenticado."
        ),
        tags=["LibroCategoría"],
        responses={200: LibroCategoriaSerializer(many=True), 401: R_401},
    ),
    retrieve=extend_schema(
        summary="Obtener una relación libro-categoría",
        tags=["LibroCategoría"],
        responses={200: LibroCategoriaSerializer, 401: R_401, 403: R_403, 404: R_404},
    ),
    create=extend_schema(
        summary="Crear relación libro-categoría",
        tags=["LibroCategoría"],
        responses={201: LibroCategoriaSerializer, 400: R_400, 401: R_401},
    ),
    update=extend_schema(
        summary="Actualizar relación libro-categoría (completo)",
        tags=["LibroCategoría"],
        responses={200: LibroCategoriaSerializer, 401: R_401, 403: R_403, 404: R_404},
    ),
    partial_update=extend_schema(
        summary="Actualizar relación libro-categoría (parcial)",
        tags=["LibroCategoría"],
        responses={200: LibroCategoriaSerializer, 401: R_401, 403: R_403, 404: R_404},
    ),
    destroy=extend_schema(
        summary="Eliminar relación libro-categoría",
        tags=["LibroCategoría"],
        responses={204: None, 401: R_401, 403: R_403, 404: R_404},
    ),
)


# ──────────────────────────────────────────────
# CONTACTO
# ──────────────────────────────────────────────

contacto_post_schema = extend_schema(
    summary="Enviar mensaje de contacto",
    description=(
        "Envía un email al equipo de Lili con el nombre, email y mensaje del remitente. "
        "No requiere autenticación."
    ),
    tags=["Contacto"],
    request=ContactoSerializer,
    responses={
        200: inline_serializer(
            name="ContactoSuccessResponse",
            fields={"success": serializers.BooleanField()},
        ),
        400: R_400,
        500: OpenApiResponse(
            response=inline_serializer(
                name="ContactoErrorResponse",
                fields={"error": serializers.CharField()},
            ),
            description="Error al enviar el email (fallo del servicio de correo).",
        ),
    },
    examples=[
        OpenApiExample(
            "Ejemplo de contacto",
            value={
                "nombre": "Ada Lovelace",
                "email": "ada@example.com",
                "mensaje": "Hola, tengo una duda sobre mi cuenta.",
            },
            request_only=True,
        )
    ],
)


# ──────────────────────────────────────────────
# AUTH
# ──────────────────────────────────────────────

_LoginRequest = inline_serializer(
    name="LoginRequest",
    fields={
        "username": serializers.CharField(),
        "password": serializers.CharField(),
    },
)

_LoginResponse = inline_serializer(
    name="LoginResponse",
    fields={
        "detail": serializers.CharField(default="Login correcto"),
    },
)

_RegisterRequest = inline_serializer(
    name="RegisterRequest",
    fields={
        "username": serializers.CharField(),
        "email": serializers.EmailField(),
        "password": serializers.CharField(),
        "password2": serializers.CharField(help_text="Confirmación de contraseña"),
    },
)

_RegisterResponse = inline_serializer(
    name="RegisterResponse",
    fields={
        "detail": serializers.CharField(default="Usuario creado correctamente"),
    },
)

_RefreshResponse = inline_serializer(
    name="RefreshResponse",
    fields={
        "detail": serializers.CharField(default="Token renovado correctamente"),
    },
)

_MeResponse = inline_serializer(
    name="MeResponse",
    fields={
        "id": serializers.IntegerField(),
        "username": serializers.CharField(),
        "email": serializers.EmailField(),
    },
)

login_schema = extend_schema(
    summary="Iniciar sesión",
    description=(
        "Autentica al usuario con `username` y `password`. "
        "Si las credenciales son correctas, establece la cookie `access_token` (HttpOnly) "
        "y la cookie `refresh_token` en la respuesta. "
        "No requiere autenticación previa."
    ),
    tags=["Auth"],
    request=_LoginRequest,
    responses={
        200: _LoginResponse,
        400: error_response("Credenciales incorrectas o datos inválidos"),
    },
    examples=[
        OpenApiExample(
            "Login correcto",
            value={"username": "ada", "password": "s3cr3t"},
            request_only=True,
        )
    ],
)

logout_schema = extend_schema(
    summary="Cerrar sesión",
    description=(
        "Elimina las cookies `access_token` y `refresh_token`. "
        "Requiere estar autenticado."
    ),
    tags=["Auth"],
    request=None,
    responses={
        200: inline_serializer(
            name="LogoutResponse",
            fields={"detail": serializers.CharField(default="Sesión cerrada")},
        ),
        401: R_401,
    },
)

refresh_schema = extend_schema(
    summary="Renovar access token",
    description=(
        "Usa la cookie `refresh_token` para emitir un nuevo `access_token`. "
        "Devuelve la nueva cookie `access_token` en la respuesta."
    ),
    tags=["Auth"],
    request=None,
    responses={
        200: _RefreshResponse,
        401: OpenApiResponse(description="Refresh token inválido o expirado"),
    },
)

me_schema = extend_schema(
    summary="Perfil del usuario autenticado",
    description="Devuelve los datos del usuario identificado por la cookie `access_token`.",
    tags=["Auth"],
    request=None,
    responses={
        200: _MeResponse,
        401: R_401,
    },
)

register_schema = extend_schema(
    summary="Registrar nuevo usuario",
    description=(
        "Crea una nueva cuenta de usuario. "
        "No requiere autenticación previa."
    ),
    tags=["Auth"],
    request=_RegisterRequest,
    responses={
        201: _RegisterResponse,
        400: error_response("Datos inválidos o usuario ya existente"),
    },
    examples=[
        OpenApiExample(
            "Registro correcto",
            value={
                "username": "ada",
                "email": "ada@example.com",
                "password": "s3cr3t",
                "password2": "s3cr3t",
            },
            request_only=True,
        )
    ],
)