from rest_framework.routers import DefaultRouter

from lili_api.views import AutorView, LibroView, UsuarioLiliView, SerieView, CategoriaView, UsuarioLibroView, \
    AmistadView, PrestamoView, NotificacionView, LibroCategoriaView, EditorialView

router = DefaultRouter()
router.register(r'autores', AutorView, basename='autor'),
router.register(r'editoriales', EditorialView, basename='editorial'),
router.register(r'libros', LibroView, basename='libro'),
router.register(r'usuarios', UsuarioLiliView, basename='usuario'),
router.register(r'series', SerieView, basename='serie'),
router.register(r'categorias', CategoriaView, basename='categoria'),
router.register(r'libros_usuarios', UsuarioLibroView, basename='libros_usuario'),
router.register(r'amistades', AmistadView, basename='amistad'),
router.register(r'prestamos', PrestamoView, basename='prestamo'),
router.register(r'notificaciones', NotificacionView, basename='notificacion'),
router.register(r'libros_categorias', LibroCategoriaView, basename='libro_categoria'),