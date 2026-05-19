from datetime import datetime, date

import resend
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from .filters import UsuarioLibroFilter, AmistadFilter, PrestamoFilter, NotificacionFilter, LibroCategoriaFilter, \
    LibroFilter
from .models import Autor, Libro, UsuarioLili, Amistad, Prestamo, Serie, Categoria, UsuarioLibro, Notificacion, \
    LibroCategoria, Editorial
from lili_api.serializers import AutorSerializer, LibroSerializer, UsuarioLiliSerializer, SerieSerializer, \
    CategoriaSerializer, UsuarioLibroSerializer, AmistadSerializer, PrestamoSerializer, NotificacionSerializer, \
    LibroCategoriaSerializer, EditorialSerializer, UsuarioLiliPublicoSerializer, ContactoSerializer
from .permissions import OwnProfilePermission, PrestamoPermission, LibroCategoriaPermission, AmistadPermission

from .schemas import (
    autor_schema,
    editorial_schema,
    libro_schema,
    usuario_lili_schema,
    serie_schema,
    categoria_schema,
    usuario_libro_schema,
    amistad_schema,
    prestamo_schema,
    notificacion_schema,
    libro_categoria_schema,
    contacto_post_schema,
)
from .services import obtener_libro_por_isbn


@autor_schema
class AutorView(ModelViewSet):
    queryset = Autor.objects.all()
    serializer_class = AutorSerializer

    def create(self, request, *args, **kwargs):
        nombre = request.data.get('nombre', '').strip()
        editorial, created = Autor.objects.get_or_create(
            nombre__iexact=nombre,
            defaults={'nombre': nombre}
        )
        serializer = self.get_serializer(editorial)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(serializer.data, status=status_code)

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['nombre']
    ordering_fields = ['nombre']

    def get_permissions(self):
        if self.action not in ["destroy", "partial_update"]:
            return [IsAuthenticated()]
        return [IsAdminUser()]

@editorial_schema
class EditorialView(ModelViewSet):
    queryset = Editorial.objects.all()
    serializer_class = EditorialSerializer

    def create(self, request, *args, **kwargs):
        nombre = request.data.get('nombre', '').strip()
        editorial, created = Editorial.objects.get_or_create(
            nombre__iexact=nombre,
            defaults={'nombre': nombre}
        )
        serializer = self.get_serializer(editorial)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(serializer.data, status=status_code)

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['nombre']
    ordering_fields = ['nombre']

    def get_permissions(self):
        if self.action not in ["destroy", "partial_update"]:
            return [IsAuthenticated()]
        return [IsAdminUser()]

@libro_schema
class LibroView(ModelViewSet):
    queryset = Libro.objects.all().select_related('editorial').prefetch_related('autores').order_by('id')
    serializer_class = LibroSerializer

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['titulo', 'sinopsis', 'autores__nombre', 'editorial__nombre']
    ordering_fields = ['nombre', 'autores__nombre', 'editorial__nombre']
    filterset_class = LibroFilter

    def get_permissions(self):
        if self.action not in ["destroy", "partial_update"]:
            return [IsAuthenticated()]
        return [IsAdminUser()]

    # Sobreescribe list() para devolver según la BD o según resultados de OL
    def list(self, request, *args, **kwargs):
        # Búsqueda normal
        queryset = self.filter_queryset(self.get_queryset())

        # Si hay resultados, respuesta normal
        if queryset.exists():
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        # Si no hay resultados, comprueba si se busca ISBN
        query = request.query_params.get("isbn", "").strip()
        if query:
            datos = obtener_libro_por_isbn(query)
            if datos:
                datos["fuente"] = "openlibrary"
                datos["autores_detalle"] = [{"nombre": a.nombre} for a in datos.pop("autores")]
                editorial = datos.pop("editorial")
                datos["editorial_detalle"] = {"nombre": editorial.nombre} if editorial else None
                return Response({"results": [datos], "fuente": "openlibrary"})

        # Si no hay resultados en ningún lado
        return Response({"results": []})

    @action(detail=False, methods=['post'], url_path='importar')
    def importar(self, request):
        """
            POST /libros/importar/
            Body: { "isbn": "9780140328721" }
        """
        isbn = request.data.get('isbn')
        if not isbn:
            return Response(
                {"error": "Se requiere un ISBN"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Si ya existe en la BD
        if Libro.objects.filter(isbn=isbn).exists():
            return Response(
                {"error": "El libro ya existe en la base de datos"},
                status=status.HTTP_409_CONFLICT
            )

        # Si no existe, busca en Open Library
        datos = obtener_libro_por_isbn(isbn)
        if not datos:
            return Response(
                {"error": "No se encontró el libro en Open Library"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Si existe, lo mapea y guarda en BD
        try:
            with transaction.atomic():
                autores = datos.pop('autores')
                editorial = datos.pop('editorial')

                libro = Libro.objects.create(**datos, editorial=editorial)
                libro.autores.set(autores)
        except Exception as e:
            return Response(
                {"error": f"Error al guardar el libro: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        serializer = self.get_serializer(libro)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

@usuario_lili_schema
class UsuarioLiliView(ModelViewSet):
    # Los admins no salen en la lista
    queryset = UsuarioLili.objects.filter(is_staff=False).prefetch_related('libros')

    def get_serializer_class(self):
        # admin y uno mismo pueden ver todo
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            try:
                obj = self.get_object()
                if self.request.user.is_staff or obj == self.request.user:
                    return UsuarioLiliSerializer
                return UsuarioLiliPublicoSerializer
            except Exception:
                return UsuarioLiliSerializer

        # en la lista completa sólo admin puede ver todo
        if self.request.user.is_staff:
            return UsuarioLiliSerializer
        return UsuarioLiliPublicoSerializer


    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['username']
    ordering_fields = ['username', 'date_joined']

    # Permisos: cada usuario puede cambiar sus cosas
    def get_permissions(self):
        return [IsAuthenticated()]

@serie_schema
class SerieView(ModelViewSet):
    def get_queryset(self):
        if self.request.user.is_staff:
            return Serie.objects.all().select_related('usuario')
        return Serie.objects.filter(usuario__pk=self.request.user.pk).select_related('usuario')

    serializer_class = SerieSerializer

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['nombre', 'usuario__username']
    filterset_fields = ['usuario']
    ordering_fields = ['nombre']

    # Permisos: cada usuario puede cambiar sus cosas y el admin las de todos
    def get_permissions(self):
        return [OwnProfilePermission()]

@categoria_schema
class CategoriaView(ModelViewSet):
    def get_queryset(self):
        if self.request.user.is_staff:
            return Categoria.objects.all().select_related('usuario')
        return Categoria.objects.filter(usuario__pk=self.request.user.pk).select_related('usuario')

    #queryset = Categoria.objects.all().select_related('usuario')
    serializer_class = CategoriaSerializer

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['nombre', 'usuario__username']
    filterset_fields = ['publica', 'usuario']
    ordering_fields = ['nombre']

    @action(detail=False, methods=['get'], url_path='publicas')
    def publicas(self, request):
        """
        GET categorías públicas, se filtra con ?usuario={id}
        """

        qs = Categoria.objects.filter(publica=True).select_related('usuario')

        usuario_id = request.query_params.get('usuario')
        if usuario_id:
            qs = qs.filter(usuario__pk=usuario_id)

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    # Permisos: cada usuario puede cambiar sus cosas y el admin las de todos
    def get_permissions(self):
        return [OwnProfilePermission()]

@usuario_libro_schema
class UsuarioLibroView(ModelViewSet):
    serializer_class = UsuarioLibroSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return (UsuarioLibro.objects.all()
                    .select_related('usuario', 'libro', 'serie')
                    .prefetch_related('categorias').order_by('id'))
        return (UsuarioLibro.objects.filter(usuario__pk=self.request.user.pk)
                .select_related('usuario', 'libro', 'serie')
                .prefetch_related('categorias'))

    # Cambiar estado de libro
    @action(detail=True, methods=['post']) # permission_classes=[]
    def cambiar_estado(self, request, pk=None):
        libro = self.get_object()
        nuevo_estado = request.data.get('estado')

        if nuevo_estado not in UsuarioLibro.EstadosLectura.values:
            return Response(
                {"error": "El estado no es válido"},
                status=status.HTTP_400_BAD_REQUEST
            )

        libro.estado = nuevo_estado
        libro.save()
        return Response(
            {"estado": f'Estado de {libro.libro.titulo} cambiado correctamente a {libro.estado}'},
            status=status.HTTP_200_OK
        )

    # Alternar favorito libro
    @action(detail=True, methods=['post'])
    def cambiar_favorito(self, request, pk=None):
        libro = self.get_object()

        if libro.favorito:
            libro.favorito = False
        else:
            libro.favorito = True

        libro.save()

        serializer = self.get_serializer(libro)
        return Response(
            {"mensaje": "Estado de favorito cambiado correctamente", "data": serializer.data},
            status=status.HTTP_200_OK
        )

    # Alternar público libro
    @action(detail=True, methods=['post'])
    def cambiar_publico(self, request, pk=None):
        libro = self.get_object()

        if libro.publico:
            libro.publico = False
        else:
            libro.publico = True

        libro.save()

        serializer = self.get_serializer(libro)
        return Response(
            {"mensaje": "Estado público cambiado correctamente", "data": serializer.data},
            status=status.HTTP_200_OK
        )

    # Mostrar lista de libros en estado "leyendo"
    @action(detail=False, methods=['get'])
    def leyendo(self, request):
        libros_leyendo = UsuarioLibro.objects.filter(
            usuario=request.user,
            estado='leyendo'
        )
        return Response(UsuarioLibroSerializer(libros_leyendo, many=True).data)

    # Mostrar lista de favoritos
    @action(detail=False, methods=['get'])
    def favoritos(self, request):
        libros_favoritos = UsuarioLibro.objects.filter(
            usuario=request.user,
            favorito=True
        )
        return Response(UsuarioLibroSerializer(libros_favoritos, many=True).data)

    # Mostrar lista de públicos
    @action(detail=False, methods=['get'])
    def publicos(self, request):
        # GET /usuario-libros/publicos/?usuario_id=3
        libros_publicos = UsuarioLibro.objects.filter(
            publico=True
        ).select_related('usuario', 'libro', 'serie').prefetch_related('categorias')

        usuario_id = request.query_params.get('usuario_id')
        if usuario_id:
            libros_publicos = libros_publicos.filter(usuario__pk=usuario_id)

        return Response(
            UsuarioLibroSerializer(libros_publicos, many=True).data,
            status=status.HTTP_200_OK
        )

    # Añadir libro a una categoría, si la categoría no existe, la crea
    @action(detail=False, methods=['post'])
    @transaction.atomic # Sin commits intermedios
    def anadir(self, request):
        """
        :param request:
            {
                "libro_id": 1,
                "categoria": "Sci-fi" # o ID
            }
        """
        libro_id = request.data.get('libro_id')
        categoria = request.data.get('categoria')

        if not libro_id or not categoria:
            return Response(
                {"error": "Es necesario indicar libro_id y categoría"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Crear UsuarioLibro
        usuario_libro, _ = UsuarioLibro.objects.get_or_create(
            usuario=request.user,
            libro=libro_id,
            defaults={'estado': UsuarioLibro.EstadosLectura.SIN_EMPEZAR}
        )

        # Categoría ID o nombre
        if isinstance(categoria, int):
            cat, _ = Categoria.objects.get_or_create(
                id=categoria,
                usuario=request.user,
            )
        else:
            cat, _ = Categoria.objects.get_or_create(
                nombre=categoria,
                usuario=request.user,
                defaults={'publica': False}
            )

        # Crear relación
        relacion, creada = LibroCategoria.objects.get_or_create(
            usuario_libro=usuario_libro,
            categoria=cat,
        )

        return Response(
            {
                'usuario_libro': UsuarioLibroSerializer(usuario_libro).data,
                'categoria': CategoriaSerializer(cat).data,
                'relacion': LibroCategoriaSerializer(relacion).data,
            },
            status=status.HTTP_201_CREATED if creada else status.HTTP_200_OK
        )

    # Añadir libro a una serie, si la serie no existe, la crea
    @action(detail=True, methods=['post'])
    @transaction.atomic
    def anadir_serie(self, request, pk=None):
        """
            :param pk: 1
            :param request:
                {
                    "serie": "La Tumba Sellada", # o ID
                    "num_en_serie": 1
                }
        """
        usuario_libro = self.get_object()
        serie = request.data.get('serie')
        num_en_serie = request.data.get('num_en_serie')

        if not serie:
            return Response(
                {"error": "Es necesario indicar la serie"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Comprobar si serie es id o nombre
        if isinstance(serie, int):
            serie, _ = Serie.objects.get_or_create(
                id=serie,
                usuario=request.user,
            )
        else:
            serie, _ = Serie.objects.get_or_create(
                nombre=serie,
                usuario=request.user,
                defaults={'volumenes': 0}
            )

        # Asignar serie y num en serie a usuario_libro
        usuario_libro.serie = serie
        usuario_libro.numero_en_serie = num_en_serie
        usuario_libro.save()

        return Response(
        {
                'usuario_libro': UsuarioLibroSerializer(usuario_libro).data,
                'serie': SerieSerializer(serie).data,
            },
            status=status.HTTP_201_CREATED if serie else status.HTTP_200_OK
        )

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = UsuarioLibroFilter
    search_fields = ['libro__titulo', 'serie__nombre']
    ordering_fields = ['estado', 'fecha_anadido', 'libro__titulo']

    # Permisos: cada usuario puede cambiar sus cosas y el admin las de todos
    def get_permissions(self):
        return [OwnProfilePermission()]

@amistad_schema
class AmistadView(ModelViewSet):
    def get_queryset(self):
        if self.request.user.is_staff:
            return Amistad.objects.all().select_related('usuario_a', 'usuario_b')
        return Amistad.objects.filter(Q(usuario_a__pk=self.request.user.pk) | Q(usuario_b__pk=self.request.user.pk)).select_related('usuario_a', 'usuario_b')

    serializer_class = AmistadSerializer

    @action(detail=True, methods=['post'])
    def aceptar(self, request, pk=None):
        amistad = self.get_object()

        if amistad.usuario_a != request.user and amistad.usuario_b != request.user:
            return Response(
                status=status.HTTP_403_FORBIDDEN
            )

        amistad.estado = Amistad.EstadosAmistad.ACEPTADA
        amistad.save()
        return Response(
            {"mensaje": "Amistad aceptada"},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def ignorar(self, request, pk=None):
        amistad = self.get_object()

        if amistad.usuario_a != request.user and amistad.usuario_b != request.user:
            return Response(
                status=status.HTTP_403_FORBIDDEN
            )

        amistad.estado = Amistad.EstadosAmistad.SIN_SOLICITAR
        amistad.save()
        return Response(
            {"mensaje": "Amistad ignorada"},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def bloquear(self, request, pk=None):
        amistad = self.get_object()

        if amistad.usuario_a != request.user and amistad.usuario_b != request.user:
            return Response(
                status=status.HTTP_403_FORBIDDEN
            )

        amistad.estado = Amistad.EstadosAmistad.BLOQUEADA
        amistad.save()
        return Response(
            {"mensaje": "Usuario bloqueado"},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'])
    def pendientes(self, request):
        amistades_pendientes = Amistad.objects.filter(
            Q(usuario_a = request.user) | Q(usuario_b = request.user),
            estado = 'pen'
        )
        return Response(
            AmistadSerializer(amistades_pendientes, many=True).data,
            status=status.HTTP_200_OK
        )

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = AmistadFilter
    search_fields = ['usuario_a__username', 'usuario_b__username']
    ordering_fields = ['fecha_creacion', 'fecha_actualizacion']

    # Permisos: cada usuario puede cambiar sus cosas y el admin las de todos
    def get_permissions(self):
        return [AmistadPermission()]

@prestamo_schema
class PrestamoView(ModelViewSet):
    queryset = Prestamo.objects.none()
    def get_queryset(self):
        if self.request.user.is_staff:
            return Prestamo.objects.all().select_related('usuario_libro', 'prestatario')
        return Prestamo.objects.filter(Q(usuario_libro__usuario__pk=self.request.user.pk) | Q(prestatario__pk=self.request.user.pk)).select_related('usuario_libro', 'prestatario')

    serializer_class = PrestamoSerializer

    @action(detail=True, methods=['post'])
    def prestar(self, request, pk=None):
        prestamo = self.get_object()

        if prestamo.usuario_libro.usuario != request.user and prestamo.prestatario != request.user:
            return Response(
                status=status.HTTP_403_FORBIDDEN
            )

        prestamo.estado = Prestamo.EstadosPrestamo.ACTIVO
        prestamo.fecha_inicio = date.today()
        prestamo.save()
        return Response(
            {"mensaje": "Préstamo aceptado"},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def devolver(self, request, pk=None):
        prestamo = self.get_object()

        if prestamo.prestatario != request.user and prestamo.usuario_libro.usuario != request.user:
            return Response(
                status=status.HTTP_403_FORBIDDEN
            )

        prestamo.estado = Prestamo.EstadosPrestamo.DEVUELTO
        prestamo.fecha_fin = date.today()
        prestamo.save()
        return Response(
            {"mensaje": "Préstamo devuelto"},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'])
    def recibidos(self, request):
        prestamos_recibidos = Prestamo.objects.filter(
            prestatario = request.user,
            estado = Prestamo.EstadosPrestamo.ACTIVO
        )
        return Response(
            PrestamoSerializer(prestamos_recibidos, many=True).data,
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'])
    def cedidos(self, request):
        prestamos_cedidos = Prestamo.objects.filter(
            usuario_libro__usuario = request.user,
            estado = "activo"
        )
        return Response(
            PrestamoSerializer(prestamos_cedidos, many=True).data,
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'])
    def solicitados_por_mi(self, request):
        prestamos_solicitados = Prestamo.objects.filter(
            prestatario = request.user,
            estado = Prestamo.EstadosPrestamo.SOLICITADO
        )
        return Response(
            PrestamoSerializer(prestamos_solicitados, many=True).data,
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'])
    def solicitados_a_mi(self, request):
        prestamos_solicitados = Prestamo.objects.filter(
            usuario_libro__usuario = request.user,
            estado = Prestamo.EstadosPrestamo.SOLICITADO
        )
        return Response(
            PrestamoSerializer(prestamos_solicitados, many=True).data,
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'])
    @transaction.atomic
    def crear_prestamo_prestador(self, request):
        """
        {
            "usuario_libro_id": 1, # UsuarioLibro del prestador
            "prestatario_id": 3 # ID del prestatario
        }
        """
        usuario_libro_id = request.data.get('usuario_libro_id')
        prestatario_id = request.data.get('prestatario_id')

        if not usuario_libro_id or not prestatario_id:
            return Response(
                {"error": "Se necesita indicar usuario_libro_id y prestatario_id"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            usuario_libro = UsuarioLibro.objects.get(pk=usuario_libro_id)
        except UsuarioLibro.DoesNotExist:
            return Response({"error": "UsuarioLibro no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        if usuario_libro.usuario != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        if Prestamo.objects.filter(usuario_libro=usuario_libro, estado=Prestamo.EstadosPrestamo.ACTIVO).exists():
            return Response(
                {"error": "Este libro ya tiene un préstamo activo"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            prestatario = UsuarioLili.objects.get(pk=prestatario_id)
        except UsuarioLili.DoesNotExist:
            return Response({"error": "Prestatario no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        UsuarioLibro.objects.get_or_create(
            usuario=prestatario,
            libro=usuario_libro.libro,
            defaults={'estado': UsuarioLibro.EstadosLectura.SIN_EMPEZAR}
        )

        prestamo = Prestamo.objects.create(
            usuario_libro=usuario_libro,
            prestatario=prestatario,
            estado=Prestamo.EstadosPrestamo.ACTIVO,
            fecha_inicio=date.today()
        )

        return Response(
            PrestamoSerializer(prestamo).data,
            status=status.HTTP_201_CREATED
        )

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = PrestamoFilter
    search_fields = ['usuario_libro__usuario__username', 'prestatario__username']
    ordering_fields = ['usuario_libro', 'fecha_inicio', 'fecha_fin']

    # Permisos: cada usuario puede cambiar sus cosas, pero sólo el prestador puede marcar devuelto
    # y el admin las de todos
    def get_permissions(self):
        return [PrestamoPermission()]

@notificacion_schema
class NotificacionView(ModelViewSet):
    def get_queryset(self):
        if self.request.user.is_staff:
            return Notificacion.objects.all().select_related('usuario')
        return Notificacion.objects.filter(usuario__pk=self.request.user.pk).select_related('usuario')

    serializer_class = NotificacionSerializer

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = NotificacionFilter
    search_fields = ['usuario__username', 'tipo']
    ordering_fields = ['usuario', 'fecha_creacion', 'leida']

    # Permisos: cada usuario puede cambiar sus cosas y el admin las de todos
    def get_permissions(self):
        return [OwnProfilePermission()]

@libro_categoria_schema
class LibroCategoriaView(ModelViewSet):
    def get_queryset(self):
        if self.request.user.is_staff:
            return LibroCategoria.objects.all().select_related('usuario_libro', 'categoria')
        return LibroCategoria.objects.filter(usuario_libro__usuario__pk=self.request.user.pk).select_related('usuario_libro', 'categoria')

    serializer_class = LibroCategoriaSerializer

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = LibroCategoriaFilter
    search_fields = ['usuario_libro', 'categoria']
    ordering_fields = ['usuario_libro', 'fecha_creacion']

    # Permisos: cada usuario puede cambiar sus cosas y el admin las de todos
    def get_permissions(self):
        return [LibroCategoriaPermission()]

# Emails de contacto
resend.api_key = settings.RESEND_API_KEY

class ContactoView(APIView):
    @contacto_post_schema
    def post(self, request):
        serializer = ContactoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            resend.Emails.send({
                "from": "onboarding@resend.dev",
                "to": [settings.CONTACT_RECIPIENT_EMAIL],
                "subject": f"Mensaje de {data['nombre']}",
                "html": f"""
                    <p><strong>Nombre:</strong> {data['nombre']}</p>
                    <p><strong>Email:</strong> {data['email']}</p>
                    <p><strong>Mensaje:</strong> {data['mensaje']}</p>
                """,
            })
            return Response({'success': True}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
