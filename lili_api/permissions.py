from rest_framework.permissions import BasePermission


class PrestamoPermission(BasePermission):
    def has_permission(self, request, view):
        # Debe estar autenticado para cualquier acción
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Admin puede todo
        if request.user.is_staff:
            return True

        es_dueno = obj.usuario_libro.usuario == request.user
        es_prestatario = obj.prestatario == request.user

        # La acción 'devolver' solo la puede hacer el dueño del libro
        if view.action == 'devolver':
            return es_dueno
        
        # El resto de acciones las puede hacer cualquiera de los dos
        return es_dueno or es_prestatario

class OwnProfilePermission(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True

        propio = obj.usuario == request.user
        return propio

class UsuarioLiliPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True

        propio = obj == request.user
        return propio

class LibroCategoriaPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        propio = obj.usuario_libro.usuario == request.user
        return propio

class AmistadPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True

        is_user_a = obj.usuario_a == request.user
        is_user_b = obj.usuario_b == request.user

        return is_user_a or is_user_b