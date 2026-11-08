from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Rating
from .serializers import MyRatingSerializer, RatingCreateSerializer, RatingSummarySerializer


class RatingCreateView(APIView):
    """POST /api/v1/ratings/ — cria ou atualiza a nota do usuário autenticado."""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=RatingCreateSerializer, responses=RatingSummarySerializer)
    def post(self, request):
        serializer = RatingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        Rating.objects.update_or_create(
            user=request.user,
            tmdb_id=data["tmdb_id"],
            media_type=data["media_type"],
            defaults={"score": data["score"]},
        )
        average, total = Rating.average_for(data["tmdb_id"], data["media_type"])
        return Response({"average": average, "total": total}, status=status.HTTP_200_OK)


class RatingSummaryView(APIView):
    """GET /api/v1/ratings/{tmdb_id}/?media_type=movie"""
    permission_classes = [permissions.AllowAny]

    @extend_schema(responses=RatingSummarySerializer)
    def get(self, request, tmdb_id):
        media_type = request.query_params.get("media_type", "movie")
        average, total = Rating.average_for(tmdb_id, media_type)
        return Response({"average": average, "total": total})


class MyRatingView(APIView):
    """GET /api/v1/ratings/{tmdb_id}/me/?media_type=movie"""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses=MyRatingSerializer)
    def get(self, request, tmdb_id):
        media_type = request.query_params.get("media_type", "movie")
        score = (
            Rating.objects.filter(user=request.user, tmdb_id=tmdb_id, media_type=media_type)
            .values_list("score", flat=True)
            .first()
        )
        return Response({"score": score})
