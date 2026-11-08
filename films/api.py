from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import permissions
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .serializers import (
    FilmDetailSerializer,
    FilmSearchResultSerializer,
    RankingSerializer,
    StreamingSerializer,
)


class FilmSearchView(APIView):
    """GET /api/v1/films/search/?q=&type=multi|movie|tv"""
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        parameters=[
            OpenApiParameter("q", str, required=True),
            OpenApiParameter("type", str, required=False),
        ],
        responses=FilmSearchResultSerializer(many=True),
    )
    def get(self, request):
        query = request.query_params.get("q", "").strip()
        media_type = request.query_params.get("type", "multi")
        if len(query) < 2:
            raise ValidationError({"q": "Informe ao menos 2 caracteres."})
        try:
            results = services.search(query, media_type)
        except services.TMDBError as exc:
            raise NotFound(str(exc))
        return Response(FilmSearchResultSerializer(results, many=True).data)


class FilmDetailView(APIView):
    """GET /api/v1/films/{media_type}/{tmdb_id}/"""
    permission_classes = [permissions.AllowAny]

    @extend_schema(responses=FilmDetailSerializer)
    def get(self, request, media_type, tmdb_id):
        try:
            film = services.get_detail(media_type, tmdb_id, request_user_id=getattr(request.user, "id", None))
        except services.TMDBError:
            raise NotFound("Filme/série não encontrado na TMDB.")
        return Response(FilmDetailSerializer(film).data)


class StreamingView(APIView):
    """GET /api/v1/streaming/{media_type}/{tmdb_id}/"""
    permission_classes = [permissions.AllowAny]

    @extend_schema(responses=StreamingSerializer)
    def get(self, request, media_type, tmdb_id):
        try:
            data = services.get_streaming(media_type, tmdb_id)
        except services.TMDBError:
            raise NotFound("Não foi possível consultar os provedores de streaming.")
        return Response(StreamingSerializer(data).data)


class RankingView(APIView):
    """GET /api/v1/films/rankings/{category}/"""
    permission_classes = [permissions.AllowAny]

    @extend_schema(responses=RankingSerializer)
    def get(self, request, category):
        try:
            data = services.get_ranking(category)
        except ValueError:
            raise NotFound("Categoria de ranking inválida.")
        return Response(RankingSerializer(data).data)
