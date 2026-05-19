from django.contrib import admin

from lili_api import models

# Register your models here.
admin.site.register(models.UsuarioLili)
admin.site.register(models.Autor)
admin.site.register(models.Libro)
admin.site.register(models.Serie)
admin.site.register(models.Categoria)
admin.site.register(models.UsuarioLibro)
admin.site.register(models.Amistad)
admin.site.register(models.Prestamo)
admin.site.register(models.Notificacion)
admin.site.register(models.LibroCategoria)