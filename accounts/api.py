from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework import permissions
from rest_framework import serializers
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Follow
from .serializers import FollowActionSerializer
from .serializers import PublicUserSerializer
from .serializers import RegisterSerializer
from .serializers import UserSerializer

User = get_user_model()

MIN_SEARCH_LENGTH = 2


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Permite login via e-mail + senha (compatível com o comportamento do
    `auth-service` original), retornando o par de tokens JWT padrão do
    SimpleJWT junto com os dados do usuário autenticado.

    Reimplementa `validate()` do zero (em vez de reaproveitar a lógica do
    pai) porque o SimpleJWT amarra `username_field` ao nome do campo de
    entrada esperado por `authenticate()`, e nosso User usa `username`
    como USERNAME_FIELD — não `email`.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"] = serializers.EmailField()
        # remove o campo dinâmico criado pelo pai (baseado em USERNAME_FIELD)
        self.fields.pop(self.username_field, None)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        try:
            user_obj = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            raise AuthenticationFailed(
                "Credenciais inválidas.",
                "no_active_account",
            ) from None

        user = authenticate(username=user_obj.username, password=password)
        if not user:
            raise AuthenticationFailed("Credenciais inválidas.", "no_active_account")

        self.user = user
        refresh = self.get_token(self.user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UserSerializer(self.user).data,
        }


class LoginView(TokenObtainPairView):
    """POST /api/v1/auth/token/ — login por e-mail + senha, retorna par JWT."""

    serializer_class = EmailTokenObtainPairSerializer


@extend_schema(
    request=RegisterSerializer,
    responses={201: UserSerializer},
    description="Cria uma nova conta de usuário no CineClub.",
)
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class MeView(APIView):
    """GET /api/v1/auth/me/ — dados do usuário autenticado."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses=UserSerializer)
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class UserDetailView(generics.RetrieveAPIView):
    """GET /api/v1/users/{username}/"""

    queryset = User.objects.select_related("profile")
    serializer_class = PublicUserSerializer
    lookup_field = "username"
    permission_classes = [permissions.AllowAny]


class UserSearchView(generics.ListAPIView):
    """GET /api/v1/users/search/?q=tallys"""

    serializer_class = PublicUserSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        q = self.request.query_params.get("q", "").strip().lstrip("@")
        if len(q) < MIN_SEARCH_LENGTH:
            return User.objects.none()
        return (
            (
                User.objects.filter(username__icontains=q)
                | User.objects.filter(profile__display_name__icontains=q)
            )
            .distinct()
            .select_related("profile")[:20]
        )


class FollowToggleView(APIView):
    """POST /api/v1/users/{user_id}/follow/ e DELETE para deixar de seguir."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FollowActionSerializer

    @extend_schema(request=None, responses=FollowActionSerializer)
    def post(self, request, user_id):
        target = get_object_or_404(User, id=user_id)
        if target == request.user:
            return Response({"error": "Você não pode seguir a si mesmo."}, status=400)
        Follow.objects.get_or_create(follower=request.user, followed=target)
        return Response(
            {"following": True, "followers_count": target.profile.followers_count},
        )

    @extend_schema(request=None, responses=FollowActionSerializer)
    def delete(self, request, user_id):
        target = get_object_or_404(User, id=user_id)
        Follow.objects.filter(follower=request.user, followed=target).delete()
        return Response(
            {"following": False, "followers_count": target.profile.followers_count},
        )
