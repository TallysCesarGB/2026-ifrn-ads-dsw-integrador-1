from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Exists
from django.db.models import OuterRef
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_POST

from accounts.models import Follow
from ratings.models import Rating

from .forms import CommentForm
from .forms import NewPostForm
from .models import Like
from .models import Post
from .models import Recommendation


def _feed_queryset(user):
    """Posts de quem o usuário segue; se ainda não segue ninguém (ou não
    há posts), cai para a timeline global — igual ao comportamento
    original do Feed.jsx (fallback para /posts quando o feed vem vazio)."""
    following_ids = Follow.objects.filter(follower=user).values_list(
        "followed_id",
        flat=True,
    )
    qs = Post.objects.filter(user_id__in=following_ids)
    if not qs.exists():
        qs = Post.objects.all()
    return qs


def _annotate_posts(qs, user):
    liked_subquery = Like.objects.filter(post=OuterRef("pk"), user=user)
    return qs.select_related("user", "user__profile").annotate(
        is_liked=Exists(liked_subquery),
    )


@login_required
def feed(request):
    qs = _annotate_posts(_feed_queryset(request.user), request.user).order_by(
        "-created_at",
    )
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get("page", 1))
    return render(
        request,
        "posts/feed.html",
        {"page_obj": page_obj, "posts": page_obj.object_list},
    )


@login_required
@require_GET
def feed_more(request):
    """Paginação via AJAX (botão "Ver mais")."""
    qs = _annotate_posts(_feed_queryset(request.user), request.user).order_by(
        "-created_at",
    )
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get("page", 1))
    html = render_to_string(
        "posts/_post_list.html",
        {"posts": page_obj.object_list},
        request=request,
    )
    return JsonResponse({"html": html, "has_next": page_obj.has_next()})


@login_required
def new_post(request):
    form = NewPostForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            post = form.save(user=request.user)
            messages.success(request, f'Indicação de "{post.title}" publicada!')
            return redirect("posts:feed")
        messages.error(request, "Selecione um filme/série antes de publicar.")
    return render(request, "posts/new_post.html", {"form": form})


@login_required
@require_POST
def toggle_like(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    like, created = Like.objects.get_or_create(user=request.user, post=post)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    return JsonResponse({"liked": liked, "likes_count": post.likes_count})


@login_required
@require_POST
def recommend_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    Recommendation.objects.create(original_post=post, recommended_by=request.user)
    return JsonResponse({"ok": True})


@login_required
@require_GET
def list_comments(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comment_set.select_related("user", "user__profile")
    my_rating = dict(
        Rating.objects.filter(
            tmdb_id=post.tmdb_id,
            media_type=post.media_type,
        ).values_list(
            "user_id",
            "score",
        ),
    )
    data = [
        {
            "id": c.id,
            "username": c.user.username,
            "avatar_url": c.user.profile.avatar_url,
            "content": c.content,
            "movie_rating": my_rating.get(c.user_id),
            "created_at": c.created_at.isoformat(),
        }
        for c in comments
    ]
    return JsonResponse(data, safe=False)


@login_required
@require_POST
def create_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"errors": form.errors}, status=400)
    comment = form.save(commit=False)
    comment.post = post
    comment.user = request.user
    comment.save()
    return JsonResponse(
        {
            "id": comment.id,
            "username": comment.user.username,
            "avatar_url": comment.user.profile.avatar_url,
            "content": comment.content,
            "created_at": comment.created_at.isoformat(),
        },
        status=201,
    )
