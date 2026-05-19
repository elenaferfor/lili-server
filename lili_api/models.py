import datetime
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models
from django.conf import settings

class Autor(models.Model):
    nombre = models.CharField(max_length=120, blank=False, null=False)
    openlibrary_key = models.CharField(max_length=16, blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Autores'

    def __str__(self):
        return self.nombre

class Editorial(models.Model):
    nombre = models.CharField(max_length=120, blank=False, null=False)
    class Meta:
        verbose_name_plural = 'Editoriales'
    def __str__(self):
        return self.nombre

class Libro(models.Model):
    isbn = models.CharField(max_length=13, unique=True)
    titulo = models.CharField(max_length=120)

    class FormatoLibro(models.TextChoices):
        TAPA_DURA = "t_dura", "Tapa dura"
        TAPA_BLANDA = "t_blanda", "Tapa blanda"
        BOLSILLO = "bolsillo", "Bolsillo"

    formato = models.CharField(max_length=10, choices=FormatoLibro.choices, blank=True, null=True)
    ano_pub = models.DateField(blank=True, null=True)
    ano_pub_og = models.DateField(blank=True, null=True)
    portada = models.CharField(max_length=200, blank=True, null=True)
    sinopsis = models.TextField(blank=True, null=True)
    openlibrary_key = models.CharField(max_length=16, blank=True, null=True)
    fecha_actualizacion = models.DateField(auto_now=True)
    editorial = models.ForeignKey(Editorial, on_delete=models.SET_NULL, blank=True, null=True)

    autores = models.ManyToManyField(Autor, related_name='libros')

    class Meta:
        verbose_name_plural = 'Libros'

    def __str__(self):
        return self.titulo

# Usuario personalizado
class UsuarioLili(AbstractUser):
    libros = models.ManyToManyField(Libro, through='UsuarioLibro', related_name='usuarios')

    class Meta:
        verbose_name_plural = 'Usuarios Lili'

    def __str__(self):
        return self.username

class Serie (models.Model):
    usuario = models.ForeignKey(UsuarioLili, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=120, blank=False, null=False)
    volumenes = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(1)])

    class Meta:
        verbose_name_plural = 'Series'

    def __str__(self):
        return self.nombre

class Categoria(models.Model):
    usuario = models.ForeignKey(UsuarioLili, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=120, blank=False, null=False)
    publica = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'Categorias'

        constraints = [
            models.UniqueConstraint(
                fields=['usuario', 'nombre'],
                name='categorias_no_duplicadas'
            )
        ]

    def __str__(self):
        return f'{self.nombre} de {self.usuario.username}'

class UsuarioLibro(models.Model):
    usuario = models.ForeignKey(UsuarioLili, on_delete=models.CASCADE)
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE, related_name='libros')
    serie = models.ForeignKey(Serie, blank=True, null=True, on_delete=models.SET_NULL)
    numero_en_serie = models.IntegerField(blank=True, null=True)

    class EstadosLectura(models.TextChoices):
        LEIDO = "leido", "Leído"
        LEYENDO = "leyendo", "Leyendo"
        ABANDONADO = "ab", "Abandonado"
        SIN_EMPEZAR = "s_e", "Sin empezar"

    estado = models.CharField(max_length=10, choices=EstadosLectura.choices, blank=True, null=True, default='s_e')
    favorito = models.BooleanField(default=False)
    publico = models.BooleanField(default=False)
    fecha_anadido = models.DateTimeField(auto_now_add=True)

    categorias = models.ManyToManyField(Categoria, through='LibroCategoria', related_name='libros_usuario')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['usuario', 'libro'],
                name='libros_no_duplicados'
            )
        ]

    def __str__(self):
        return f'Libro {self.libro.titulo} del usuario {self.usuario.username}'

class Amistad(models.Model):
    usuario_a = models.ForeignKey(UsuarioLili, on_delete=models.CASCADE, related_name='amistades_enviadas')
    usuario_b = models.ForeignKey(UsuarioLili, on_delete=models.CASCADE, related_name='amistades_recibidas')

    class EstadosAmistad(models.TextChoices):
        SIN_SOLICITAR = 's_s', 'Sin solicitar'
        PENDIENTE = 'pen', 'Pendiente'
        ACEPTADA = 'ac', 'Aceptada'
        BLOQUEADA = 'blo', 'Bloqueada'

    estado = models.CharField(max_length=16, choices=EstadosAmistad.choices, default='s_s')
    fecha_creacion = models.DateField(auto_now_add=True)
    fecha_actualizacion = models.DateField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Amistades'

        constraints = [
            models.UniqueConstraint(
                fields=['usuario_a', 'usuario_b'],
                name='unique_amistad'
            ),
            models.CheckConstraint(
                check=~models.Q(usuario_a = models.F('usuario_b')),
                name='no_autoamistad'
            )
        ]

    def save(self, *args, **kwargs):
        if self.usuario_a.id > self.usuario_b.id:
            self.usuario_a.id, self.usuario_b.id = self.usuario_b.id, self.usuario_a.id
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Amistad {self.pk} entre {self.usuario_a} y {self.usuario_b}'

class Prestamo(models.Model):
    usuario_libro = models.ForeignKey(UsuarioLibro, on_delete=models.CASCADE)
    prestatario = models.ForeignKey(UsuarioLili, on_delete=models.SET_NULL, null=True)
    fecha_solicitud = models.DateField(auto_now_add=True)
    fecha_inicio = models.DateField(blank=True, null=True)
    fecha_fin = models.DateField(blank=True, null=True)

    class EstadosPrestamo(models.TextChoices):
        ACTIVO = 'activo', 'Activo'
        DEVUELTO = 'devuelto', 'Devuelto'
        SOLICITADO = 'solicitado', 'Solicitado'

    estado = models.CharField(max_length=16, choices=EstadosPrestamo.choices, default='activo')

    class Meta:
        verbose_name_plural = 'Prestamos'
        constraints = [
            models.UniqueConstraint(
                fields=['usuario_libro'],
                condition=models.Q(estado='activo'),
                name='unique_prestamo_activo'
            )
        ]

    def __str__(self):
        return f'Prestamo {self.pk} del libro {self.usuario_libro.libro.titulo} del usuario {self.usuario_libro.usuario.username} a {self.prestatario.username}'

class Notificacion(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=42)
    texto = models.TextField()
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    referencia = models.IntegerField()

    class Meta:
        verbose_name_plural = 'Notificaciones'

    def __str__(self):
        return f'Notificación {self.pk} del usuario {self.usuario.username}'

class LibroCategoria(models.Model):
    usuario_libro = models.ForeignKey(UsuarioLibro, on_delete=models.CASCADE)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    fecha_creacion = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario_libro', 'categoria')
