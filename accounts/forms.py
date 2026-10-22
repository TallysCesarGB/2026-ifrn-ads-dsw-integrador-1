from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

from .models import Profile

User = get_user_model()


class RegisterForm(forms.Form):
    """Formulário de cadastro — equivalente ao POST /auth/register original."""

    display_name = forms.CharField(
        label="Nome de exibição",
        max_length=120,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Seu nome"}),
    )
    username = forms.CharField(
        label="Username",
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": "@seunome"}),
    )
    email = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(attrs={"placeholder": "seu@email.com"}),
    )
    password = forms.CharField(
        label="Senha",
        min_length=6,
        widget=forms.PasswordInput(attrs={"placeholder": "••••••••"}),
    )

    def clean_username(self):
        username = self.cleaned_data["username"].lstrip("@").strip()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("Esse username já está em uso.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Esse e-mail já está cadastrado.")
        return email

    def save(self):
        data = self.cleaned_data
        user = User.objects.create_user(
            username=data["username"],
            email=data["email"],
            password=data["password"],
        )
        profile = user.profile
        profile.display_name = data.get("display_name") or data["username"]
        profile.save()
        return user


class LoginForm(AuthenticationForm):
    """Login por e-mail + senha (o projeto original autentica por e-mail)."""

    username = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(attrs={"placeholder": "seu@email.com"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password"].widget.attrs["placeholder"] = "••••••••"

    def clean(self):
        email = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")
        if email and password:
            try:
                user_obj = User.objects.get(email__iexact=email)
            except User.DoesNotExist:
                raise ValidationError("Credenciais inválidas.") from None
            self.cleaned_data["username"] = user_obj.username
        return super().clean()


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["display_name", "bio", "avatar"]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 3, "maxlength": 280}),
        }
