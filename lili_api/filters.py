import django_filters
from django_filters import CharFilter
from django_filters.rest_framework import filters

from lili_api.models import Amistad, UsuarioLibro, Prestamo, Notificacion, LibroCategoria, Libro


class LibroFilter(django_filters.FilterSet):
    autor_nombre = django_filters.CharFilter(
        field_name='autores__nombre',
        lookup_expr='iexact')

    isbn = CharFilter(field_name='isbn', lookup_expr='exact')

    class Meta:
        model = Libro
        fields = ['autores']

class UsuarioLibroFilter(django_filters.FilterSet):
    categoria_nombre = filters.CharFilter(
        field_name='categorias__nombre',
        lookup_expr='icontains')

    class Meta:
        model = UsuarioLibro
        fields = ['serie', 'estado', 'favorito', 'categorias', 'categoria_nombre']

class AmistadFilter(django_filters.FilterSet):
    usuario_a_nombre = filters.CharFilter(
        field_name='usuario_a__username',
        lookup_expr='iexact'
    )
    usuario_b_nombre = filters.CharFilter(
        field_name='usuario_b__username',
        lookup_expr='iexact'
    )

    class Meta:
        model = Amistad
        fields = ['usuario_a', 'usuario_b', 'usuario_a_nombre', 'usuario_b_nombre', 'estado']

class PrestamoFilter(django_filters.FilterSet):
    usuario_libro_usuario_nombre = filters.CharFilter(
        field_name='usuario_libro__usuario__username',
        lookup_expr='iexact'
    )

    prestatario_nombre = filters.CharFilter(
        field_name='prestatario__username',
        lookup_expr='iexact'
    )

    class Meta:
        model = Prestamo
        fields = ['usuario_libro', 'prestatario', 'usuario_libro_usuario_nombre', 'prestatario_nombre', 'estado']

class NotificacionFilter(django_filters.FilterSet):
    usuario_nombre = filters.CharFilter(
        field_name='usuario__username',
        lookup_expr='iexact'
    )

    tipo = filters.CharFilter(
        field_name='tipo',
        lookup_expr='icontains'
    )

    class Meta:
        model = Notificacion
        fields = ['usuario', 'usuario_nombre', 'tipo', 'leida']

class LibroCategoriaFilter(django_filters.FilterSet):
    usuario_libro_nombre = filters.CharFilter(
        field_name='usuario_libro__usuario__username',
        lookup_expr='iexact'
    )

    categoria_nombre = filters.CharFilter(
        field_name='categoria__nombre',
        lookup_expr='icontains'
    )

    class Meta:
        model = LibroCategoria
        fields = ['usuario_libro', 'usuario_libro_nombre', 'categoria', 'categoria_nombre']