from django.db.models import Exists
from django.db.models import OuterRef
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Follow

from .models import Comment
from .models import Like
from .models import Post
from .models import Recommendation
from .serializers import CommentSerializer
from .serializers import LikeActionSerializer
from .serializers import PostSerializer
from .serializers import RecommendActionSerializer


def _annotate(qs, user):
    if user and user.is_authenticated:
        return qs.annotate(
            is_liked=Exists(Like.objects.filter(post=OuterRef("pk"), user=user)),
        )
    return qs


class PostListCreateView(generics.ListCreateAPIView):
    """GET /api/v1/posts/ — timeline pública · POST cria uma nova indicação."""

    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = Post.objects.select_related("user", "user__profile").order_by(
            "-created_at",
        )
        return _annotate(qs, self.request.user)


class FeedView(generics.ListAPIView):
    """GET /api/v1/feed/ — posts de quem o usuário autenticado segue
    (com fallback para timeline pública, igual ao comportamento do site)."""

    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        following_ids = Follow.objects.filter(follower=user).values_list(
            "followed_id",
            flat=True,
        )
        qs = Post.objects.filter(user_id__in=following_ids)
        if not qs.exists():
            qs = Post.objects.all()
        qs = qs.select_related("user", "user__profile").order_by("-created_at")
        return _annotate(qs, user)


class PostLikeView(APIView):
    """POST /api/v1/posts/{id}/like/ — curte/descurte (toggle)."""

    permission_classes = [permissions.IsAuthenticated]

    serializer_class = LikeActionSerializer

    @extend_schema(request=None, responses=LikeActionSerializer)
    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        like, created = Like.objects.get_or_create(user=request.user, post=post)
        if not created:
            like.delete()
            liked = False
        else:
            liked = True
        return Response({"liked": liked, "likes_count": post.likes_count})


class PostRecommendView(APIView):
    """POST /api/v1/posts/{id}/recommend/"""

    permission_classes = [permissions.IsAuthenticated]

    serializer_class = RecommendActionSerializer

    @extend_schema(request=None, responses=RecommendActionSerializer)
    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        Recommendation.objects.create(original_post=post, recommended_by=request.user)
        return Response({"ok": True})


class PostCommentsView(generics.ListCreateAPIView):
    """GET/POST /api/v1/posts/{id}/comments/"""

    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Comment.objects.filter(post_id=self.kwargs["post_id"]).select_related(
            "user",
            "user__profile",
        )

    def perform_create(self, serializer):
        post = get_object_or_404(Post, id=self.kwargs["post_id"])
        serializer.save(post=post, user=self.request.user)
