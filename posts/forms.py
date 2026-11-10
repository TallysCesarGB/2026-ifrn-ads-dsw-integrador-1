from django import forms

from .models import Comment
from .models import Post


class NewPostForm(forms.Form):
    """Formulário de indicação — o filme escolhido é enviado como campos
    ocultos preenchidos via JS após a busca na TMDB (ver new_post.html)."""

    tmdb_id = forms.IntegerField(widget=forms.HiddenInput)
    media_type = forms.ChoiceField(
        choices=[("movie", "movie"), ("tv", "tv")],
        widget=forms.HiddenInput,
    )
    title = forms.CharField(widget=forms.HiddenInput)
    poster_url = forms.CharField(required=False, widget=forms.HiddenInput)
    comment = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": "Por que você recomenda? Qual cena te marcou?",
            },
        ),
    )

    def save(self, user):
        data = self.cleaned_data
        return Post.objects.create(
            user=user,
            tmdb_id=data["tmdb_id"],
            media_type=data["media_type"],
            title=data["title"],
            poster_url=data.get("poster_url") or None,
            comment=data.get("comment", ""),
        )


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["content"]
        widgets = {
            "content": forms.TextInput(
                attrs={"placeholder": "Adicione um comentário…"},
            ),
        }
