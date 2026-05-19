from django.db.models import Q
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Autor, Editorial, Libro, UsuarioLili, Amistad, Prestamo, Serie, Categoria, UsuarioLibro, Notificacion, LibroCategoria

# ===================== Serializers de detalle ===========================
class LibroTituloSerializer(serializers.ModelSerializer):
    class Meta:
        model = Libro
        fields = ['id', 'titulo', 'portada']

class AutorNombreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Autor
        fields = ['id', 'nombre']

class EditorialNombreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Editorial
        fields = ['id', 'nombre']

class SerieNombreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Serie
        fields = ['id', 'nombre', 'volumenes']

class CategoriaNombreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ['id', 'nombre']

class UsuarioNombreSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsuarioLili
        fields = ['id', 'username']

# ===================== Serializers principales ===========================
class AutorSerializer(serializers.ModelSerializer):
    libros = LibroTituloSerializer(many=True, read_only=True)

    class Meta:
        model = Autor
        fields = ['id', 'nombre', 'openlibrary_key', 'libros']

class EditorialSerializer(serializers.ModelSerializer):
    libros = LibroTituloSerializer(many=True, read_only=True)

    class Meta:
        model = Editorial
        fields = ['id', 'nombre', 'libros']

class LibroSerializer(serializers.ModelSerializer):
    autores = serializers.PrimaryKeyRelatedField(queryset=Autor.objects.all(), many=True, write_only=True)
    autores_detalle = AutorNombreSerializer(source="autores", many=True, read_only=True)
    editorial = serializers.PrimaryKeyRelatedField(queryset=Editorial.objects.all(), write_only=True, allow_null=True, allow_empty=True)
    editorial_detalle = EditorialNombreSerializer(source="editorial", read_only=True)
    class Meta:
        model = Libro
        fields = ['id', 'isbn', 'titulo', 'formato',
                  'ano_pub', 'ano_pub_og',
                  'portada', 'sinopsis',
                  'openlibrary_key', 'fecha_actualizacion',
                  'autores', 'autores_detalle', 'editorial', 'editorial_detalle']

        def create(self, validated_data):
            autores = validated_data.pop('autores')
            libro = Libro.objects.create(**validated_data)
            libro.autores.set(autores)
            return libro

class AmistadSerializer(serializers.ModelSerializer):
    usuario_a = serializers.PrimaryKeyRelatedField(queryset=UsuarioLili.objects.all(), write_only=True)
    usuario_a_nombre = UsuarioNombreSerializer(source="usuario_a", read_only=True)
    usuario_b = serializers.PrimaryKeyRelatedField(queryset=UsuarioLili.objects.all(), write_only=True)
    usuario_b_nombre = UsuarioNombreSerializer(source="usuario_b", read_only=True)

    class Meta:
        model = Amistad
        fields = ['id', 'usuario_a', 'usuario_a_nombre', 'usuario_b', 'usuario_b_nombre', 'estado',
                  'fecha_creacion', 'fecha_actualizacion']

class PrestamoSerializer(serializers.ModelSerializer):
    usuario_libro = serializers.PrimaryKeyRelatedField(queryset=UsuarioLibro.objects.all(), write_only=True)
    libro_detalle = LibroTituloSerializer(source="usuario_libro.libro", read_only=True)
    prestatario = serializers.PrimaryKeyRelatedField(queryset=UsuarioLili.objects.all(), write_only=True)
    prestatario_nombre = UsuarioNombreSerializer(source='prestatario', read_only=True)
    prestador_id = serializers.IntegerField(source="usuario_libro.usuario.id", read_only=True)

    class Meta:
        model = Prestamo
        fields = ['id', 'usuario_libro', 'libro_detalle', 'prestatario', 'prestatario_nombre', 'prestador_id',
                  'fecha_inicio', 'fecha_fin', 'estado']

class UsuarioLiliSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    amistades = serializers.SerializerMethodField()
    prestamos_hechos = serializers.SerializerMethodField()
    prestamos_recibidos = serializers.SerializerMethodField()

    @extend_schema_field(AmistadSerializer(many=True))
    def get_amistades(self, obj):
        amistades = Amistad.objects.filter( Q(usuario_a=obj) | Q(usuario_b=obj) )
        return [
            {
                "id": amistad.pk,
                "usuario_a": amistad.usuario_a.username,
                "usuario_b": amistad.usuario_b.username,
                "estado": amistad.estado,
            }
            for amistad in amistades
        ]

    @extend_schema_field(PrestamoSerializer(many=True))
    def get_prestamos_hechos(self, obj):
        prestamos = Prestamo.objects.filter(usuario_libro__usuario=obj)
        return prestamos.values_list('id', flat=True)

    @extend_schema_field(PrestamoSerializer(many=True))
    def get_prestamos_recibidos(self, obj):
        prestamos = Prestamo.objects.filter(prestatario=obj)
        return prestamos.values_list('id', flat=True)

    def create(self, validated_data):
        libros = validated_data.pop('libros', [])
        user = UsuarioLili.objects.create_user(**validated_data)
        user.libros.set(libros)
        return user

    class Meta:
        model = UsuarioLili
        fields = ['id', 'username', 'first_name', 'last_name',
                  'email', 'password', 'is_staff', 'is_active', 'date_joined',
                  'libros', 'amistades', 'prestamos_hechos', 'prestamos_recibidos']

class UsuarioLiliPublicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsuarioLili
        fields = ['id', 'username', 'date_joined']

class SerieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Serie
        fields = ['id', 'usuario', 'nombre', 'volumenes']

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ['id', 'usuario', 'nombre', 'publica']

class UsuarioLibroSerializer(serializers.ModelSerializer):
    libro = serializers.PrimaryKeyRelatedField(queryset=Libro.objects.all(), write_only=True)
    libro_detalle = LibroTituloSerializer(source="libro", read_only=True)
    serie = serializers.PrimaryKeyRelatedField(queryset=Serie.objects.all(), allow_null=True, write_only=True)
    serie_detalle = SerieNombreSerializer(source="serie", read_only=True)
    categorias = serializers.PrimaryKeyRelatedField(queryset=Categoria.objects.all(), many=True, write_only=True)
    categorias_detalle = CategoriaNombreSerializer(source="categorias", read_only=True, many=True)

    def create(self, validated_data):
        categorias = validated_data.pop('categorias')
        libro_usuario = UsuarioLibro.objects.create(**validated_data)
        libro_usuario.categorias.set(categorias)
        return libro_usuario

    class Meta:
        model = UsuarioLibro
        fields = ['id', 'usuario', 'libro', 'libro_detalle',
                  'serie', 'serie_detalle', 'numero_en_serie',
                  'estado', 'favorito', 'publico',
                  'fecha_anadido', 'categorias', 'categorias_detalle']

class NotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacion
        fields = ['id', 'usuario', 'tipo',
                  'texto', 'leida', 'fecha_creacion',
                  'referencia']

class LibroCategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = LibroCategoria
        fields = ['id', 'usuario_libro', 'categoria', 'fecha_creacion']


# Emails de contacto
class ContactoSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    mensaje = serializers.CharField()