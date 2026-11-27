from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Rating
from .serializers import RatingCreateSerializer


@login_required
@require_POST
def rate(request):
    """Cria/atualiza a avaliação do usuário logado para um filme/série
    (equivalente ao POST /ratings original — chamado via AJAX na página
    de detalhes do filme)."""
    data = {"media_type": "movie", **request.POST.dict()}
    serializer = RatingCreateSerializer(data=data)
    if not serializer.is_valid():
        return JsonResponse(
            {"error": "Parâmetros inválidos.", "fields": serializer.errors},
            status=400,
        )

    tmdb_id = serializer.validated_data["tmdb_id"]
    media_type = serializer.validated_data["media_type"]
    score = serializer.validated_data["score"]
    Rating.objects.update_or_create(
        user=request.user,
        tmdb_id=tmdb_id,
        media_type=media_type,
        defaults={"score": score},
    )
    average, total = Rating.average_for(tmdb_id, media_type)
    return JsonResponse(
        {"ok": True, "average": average, "total": total, "my_score": score},
    )
