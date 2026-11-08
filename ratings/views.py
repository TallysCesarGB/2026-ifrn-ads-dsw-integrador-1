from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Rating


@login_required
@require_POST
def rate(request):
    """Cria/atualiza a avaliação do usuário logado para um filme/série
    (equivalente ao POST /ratings original — chamado via AJAX na página
    de detalhes do filme)."""
    try:
        tmdb_id = int(request.POST.get("tmdb_id"))
        media_type = request.POST.get("media_type", "movie")
        score = int(request.POST.get("score"))
    except (TypeError, ValueError):
        return JsonResponse({"error": "Parâmetros inválidos."}, status=400)

    if not 0 <= score <= 10:
        return JsonResponse({"error": "Score deve ser entre 0 e 10."}, status=400)

    Rating.objects.update_or_create(
        user=request.user, tmdb_id=tmdb_id, media_type=media_type, defaults={"score": score}
    )
    average, total = Rating.average_for(tmdb_id, media_type)
    return JsonResponse({"ok": True, "average": average, "total": total, "my_score": score})
