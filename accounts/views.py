from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_POST

from posts.models import Post

from .forms import LoginForm
from .forms import ProfileEditForm
from .forms import RegisterForm
from .models import Follow

User = get_user_model()

MIN_SEARCH_LENGTH = 2

# Abas da grade do perfil: valor de ?tipo= -> media_type (None = todos).
PROFILE_TABS = {"todos": None, "filmes": "movie", "series": "tv"}


def auth_view(request):
    """Página única com abas de Entrar / Criar conta (equivalente à
    Auth.jsx do front-end original)."""
    if request.user.is_authenticated:
        return redirect("posts:feed")

    mode = request.POST.get("mode", request.GET.get("mode", "login"))
    login_form = LoginForm(request)
    register_form = RegisterForm()

    if request.method == "POST":
        if mode == "register":
            register_form = RegisterForm(request.POST)
            if register_form.is_valid():
                user = register_form.save()
                auth_login(
                    request,
                    user,
                    backend="django.contrib.auth.backends.ModelBackend",
                )
                messages.success(request, f"Bem-vindo(a), {user.username}!")
                return redirect("posts:feed")
        else:
            login_form = LoginForm(request, data=request.POST)
            if login_form.is_valid():
                auth_login(request, login_form.get_user())
                return redirect("posts:feed")
            messages.error(request, "Credenciais inválidas.")

    return render(
        request,
        "accounts/auth.html",
        {"mode": mode, "login_form": login_form, "register_form": register_form},
    )


@require_POST
def logout_view(request):
    auth_logout(request)
    return redirect("accounts:login")


@login_required
def profile_view(request, username):
    """Perfil público — posts do usuário em grade + edição inline se for o dono."""
    profile_user = get_object_or_404(User, username=username)
    profile = profile_user.profile
    is_me = profile_user == request.user
    is_following = False
    if not is_me:
        is_following = Follow.objects.filter(
            follower=request.user,
            followed=profile_user,
        ).exists()

    user_posts = Post.objects.filter(user=profile_user)
    counts = user_posts.aggregate(
        todos=Count("id"),
        filmes=Count("id", filter=Q(media_type="movie")),
        series=Count("id", filter=Q(media_type="tv")),
    )
    active_tab = request.GET.get("tipo", "todos")
    if active_tab not in PROFILE_TABS:
        active_tab = "todos"
    posts = user_posts.order_by("-created_at")
    if PROFILE_TABS[active_tab]:
        posts = posts.filter(media_type=PROFILE_TABS[active_tab])

    edit_form = ProfileEditForm(instance=profile) if is_me else None

    if request.method == "POST" and is_me:
        edit_form = ProfileEditForm(request.POST, request.FILES, instance=profile)
        if edit_form.is_valid():
            edit_form.save()
            messages.success(request, "Perfil atualizado!")
            return redirect("accounts:profile", username=username)

    return render(
        request,
        "accounts/profile.html",
        {
            "profile_user": profile_user,
            "profile": profile,
            "posts": posts,
            "active_tab": active_tab,
            "tab_counts": counts,
            "is_me": is_me,
            "is_following": is_following,
            "edit_form": edit_form,
        },
    )


@login_required
@require_POST
def toggle_follow(request, user_id):
    target = get_object_or_404(User, id=user_id)
    if target == request.user:
        return JsonResponse({"error": "Você não pode seguir a si mesmo."}, status=400)

    follow, created = Follow.objects.get_or_create(
        follower=request.user,
        followed=target,
    )
    if not created:
        follow.delete()
        following = False
    else:
        following = True

    return JsonResponse(
        {"following": following, "followers_count": target.profile.followers_count},
    )


@login_required
@require_GET
def search_users(request):
    """Busca de usuários por username/nome (AJAX), usada no feed (user_search.js)."""
    q = request.GET.get("q", "").strip().lstrip("@")
    results = []
    if len(q) >= MIN_SEARCH_LENGTH:
        users = (
            (
                User.objects.filter(username__icontains=q)
                | User.objects.filter(profile__display_name__icontains=q)
            )
            .distinct()
            .select_related("profile")[:20]
        )
        results = [
            {
                "id": u.id,
                "username": u.username,
                "display_name": u.profile.display_name_or_username,
                "avatar_url": u.profile.avatar_url,
                "posts_count": u.profile.posts_count,
                "followers_count": u.profile.followers_count,
            }
            for u in users
        ]
    return JsonResponse(results, safe=False)
