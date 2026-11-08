from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from ratings.models import Rating

from . import services


@login_required
def film_detail(request, media_type, tmdb_id):
    """Página de detalhes do filme/série — equivalente à FilmDetail.jsx."""
    try:
        film = services.get_detail(media_type, tmdb_id, request_user_id=request.user.id)
    except services.TMDBError:
        raise Http404("Filme/série não encontrado na TMDB.")

    average, total = Rating.average_for(tmdb_id, film["media_type"])
    my_score = Rating.objects.filter(
        user=request.user, tmdb_id=tmdb_id, media_type=film["media_type"]
    ).values_list("score", flat=True).first()

    return render(
        request,
        "films/film_detail.html",
        {
            "film": film,
            "rating_average": average,
            "rating_total": total,
            "my_score": my_score,
            "score_range": range(1, 11),
        },
    )


@login_required
@require_GET
def search_json(request):
    """Endpoint AJAX usado pela página 'Nova indicação' para buscar na TMDB."""
    query = request.GET.get("q", "").strip()
    media_type = request.GET.get("type", "multi")
    if len(query) < 2:
        return JsonResponse([], safe=False)
    try:
        results = services.search(query, media_type)
    except services.TMDBError:
        return JsonResponse({"error": "Erro ao buscar na TMDB."}, status=502)
    return JsonResponse(results, safe=False)


@login_required
@require_GET
def rankings_json(request, category):
    """Endpoint AJAX usado pelos Stories no topo do feed."""
    try:
        data = services.get_ranking(category)
    except ValueError:
        return JsonResponse({"error": "Categoria inválida."}, status=404)
    return JsonResponse(data)
