from django.db.models.signals import post_save
from django.dispatch import receiver
from lili_api.models import Categoria, UsuarioLili


@receiver(post_save, sender=UsuarioLili)
def crear_categoria_deseos(sender, instance, created, **kwargs):
    if created:
        Categoria.objects.create(nombre='Deseos', usuario=instance)