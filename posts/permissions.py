from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Leitura liberada; escrita/exclusão só para o dono do objeto (`obj.user`)."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user_id == request.user.id


class IsCommentAuthorOrPostOwnerOrReadOnly(permissions.BasePermission):
    """Comentário pode ser excluído pelo autor dele ou pelo dono do post (#47)."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.id in (obj.user_id, obj.post.user_id)
