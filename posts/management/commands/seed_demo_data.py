# ruff: noqa: S311, S106 -- dados fictícios: random e senhas de demo são intencionais
"""
Comando de management para popular o banco com dados fictícios, facilitando
a correção/demonstração do projeto sem depender de cadastro manual ou de
uma chave da TMDB configurada (os pôsteres usados são URLs reais da TMDB,
mas nenhuma chamada de API é feita durante o seed).

Uso:
    python manage.py seed_demo_data
    python manage.py seed_demo_data --users 20 --posts 80
    python manage.py seed_demo_data --reset   # apaga dados de demo antes de recriar
"""

import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import Follow
from posts.models import Comment
from posts.models import Like
from posts.models import Post
from posts.models import Recommendation
from ratings.models import Rating

User = get_user_model()

# Filmes/séries reais (tmdb_id + pôster real da TMDB) usados para o seed,
# sem precisar chamar a API durante a geração dos dados de demonstração.
DEMO_TITLES = [
    {
        "tmdb_id": 278,
        "media_type": "movie",
        "title": "Um Sonho de Liberdade",
        "poster_url": "https://image.tmdb.org/t/p/w500/q6y0Go1tsGEsmtFryDOJo3dEmqu.jpg",
    },
    {
        "tmdb_id": 238,
        "media_type": "movie",
        "title": "O Poderoso Chefão",
        "poster_url": "https://image.tmdb.org/t/p/w500/3bhkrj58Vtu7enYsLegHejKInmC.jpg",
    },
    {
        "tmdb_id": 155,
        "media_type": "movie",
        "title": "Batman: O Cavaleiro das Trevas",
        "poster_url": "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg",
    },
    {
        "tmdb_id": 424,
        "media_type": "movie",
        "title": "A Lista de Schindler",
        "poster_url": "https://image.tmdb.org/t/p/w500/sF1U4EUQS8YHUYjNl3pMGNIQyr0.jpg",
    },
    {
        "tmdb_id": 27205,
        "media_type": "movie",
        "title": "A Origem",
        "poster_url": "https://image.tmdb.org/t/p/w500/edv5CZvWj09upOsy2Y6IwDhK8bt.jpg",
    },
    {
        "tmdb_id": 550,
        "media_type": "movie",
        "title": "Clube da Luta",
        "poster_url": "https://image.tmdb.org/t/p/w500/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
    },
    {
        "tmdb_id": 157336,
        "media_type": "movie",
        "title": "Interestelar",
        "poster_url": "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg",
    },
    {
        "tmdb_id": 680,
        "media_type": "movie",
        "title": "Pulp Fiction",
        "poster_url": "https://image.tmdb.org/t/p/w500/d5iIlFn5s0ImszYzBPb8JPIfbXD.jpg",
    },
    {
        "tmdb_id": 497,
        "media_type": "movie",
        "title": "O Verde Mile",
        "poster_url": "https://image.tmdb.org/t/p/w500/velWPhVMQeQKcxggNEU8YmU1xZu.jpg",
    },
    {
        "tmdb_id": 68718,
        "media_type": "movie",
        "title": "Django Livre",
        "poster_url": "https://image.tmdb.org/t/p/w500/2YMnBRh8F6fEuzOGeGgbIKRFRn5.jpg",
    },
    {
        "tmdb_id": 1396,
        "media_type": "tv",
        "title": "Breaking Bad",
        "poster_url": "https://image.tmdb.org/t/p/w500/ggFHVNu6YYI5L9pCfOacjizRGt.jpg",
    },
    {
        "tmdb_id": 1399,
        "media_type": "tv",
        "title": "Game of Thrones",
        "poster_url": "https://image.tmdb.org/t/p/w500/7WUHnWGx5OrhL2FLR1ba05aMwhT.jpg",
    },
    {
        "tmdb_id": 60574,
        "media_type": "tv",
        "title": "Peaky Blinders",
        "poster_url": "https://image.tmdb.org/t/p/w500/vUUqzWa2LnHIVqkaKVlVGkPaQNb.jpg",
    },
    {
        "tmdb_id": 66732,
        "media_type": "tv",
        "title": "Stranger Things",
        "poster_url": "https://image.tmdb.org/t/p/w500/49WJfeN0moxb9IPfGn8AIqMGskD.jpg",
    },
    {
        "tmdb_id": 2316,
        "media_type": "tv",
        "title": "The Office",
        "poster_url": "https://image.tmdb.org/t/p/w500/qWnJzyZhyy74gjpSjIXWmuk0ifX.jpg",
    },
    {
        "tmdb_id": 1668,
        "media_type": "tv",
        "title": "Friends",
        "poster_url": "https://image.tmdb.org/t/p/w500/f496cm9enuEsZkSPzCwnTESEK5s.jpg",
    },
    {
        "tmdb_id": 71446,
        "media_type": "tv",
        "title": "La Casa de Papel",
        "poster_url": "https://image.tmdb.org/t/p/w500/reEMJA1O0oMfRxv4r9KrpBRLGYk.jpg",
    },
]

DEMO_COMMENTS = [
    "Um dos melhores que já vi, recomendo demais!",
    "A trilha sonora sozinha já vale a sessão.",
    "Achei um pouco lento no começo, mas o final compensa.",
    "Já assisti três vezes e ainda descubro detalhes novos.",
    "Elenco impecável, direção de outro nível.",
    "Não é para todo mundo, mas eu amei.",
    "Chorei no final, não vou mentir.",
    "Perfeito para maratonar num fim de semana chuvoso.",
    "A fotografia é de tirar o fôlego.",
    "Reviravolta que eu não vi vindo de jeito nenhum.",
]

DEMO_BIOS = [
    "Cinéfilo(a) de carteirinha 🎬",
    "Assistindo tudo que aparece na frente.",
    "Ficção científica > tudo.",
    "Fã de terror e suspense.",
    "Sempre em busca da próxima obra-prima.",
    "",
]

# Chance de uma indicação fictícia vir com comentário do autor.
COMMENT_PROBABILITY = 0.8


class Command(BaseCommand):
    help = (
        "Popula o banco com usuários, indicações, curtidas, comentários "
        "e avaliações fictícias."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--users",
            type=int,
            default=12,
            help="Quantidade de usuários fictícios (padrão: 12).",
        )
        parser.add_argument(
            "--posts",
            type=int,
            default=40,
            help="Quantidade de indicações fictícias (padrão: 40).",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help=(
                "Apaga indicações, curtidas, comentários, avaliações, follows "
                "e usuários de demo antes de recriar."
            ),
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=None,
            help="Seed do gerador aleatório, para resultados reprodutíveis.",
        )

    def handle(self, *args, **options):
        try:
            from faker import Faker  # noqa: PLC0415 -- Faker é dependência de dev
        except ImportError:
            self.stderr.write(
                self.style.ERROR(
                    "O pacote 'Faker' é necessário para este comando. "
                    "Instale as dependências de desenvolvimento: uv sync",
                ),
            )
            return

        if options["seed"] is not None:
            random.seed(options["seed"])
            Faker.seed(options["seed"])

        fake = Faker("pt_BR")
        n_users = options["users"]
        n_posts = options["posts"]

        if options["reset"]:
            self._reset()

        with transaction.atomic():
            demo_user = self._create_demo_user()
            users = [demo_user, *self._create_fake_users(fake, n_users)]
            self._create_follows(users)
            posts = self._create_posts(fake, users, n_posts)
            self._create_likes(users, posts)
            self._create_comments(fake, users, posts)
            self._create_ratings(users, posts)

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Seed concluído: {len(users)} usuários, "
                f"{len(posts)} indicações.\n"
                "   Login de demonstração → e-mail: demo@cineclub.com"
                " | senha: cineclub123\n",
            ),
        )

    # ── Helpers ──────────────────────────────────────────────────────
    def _reset(self):
        self.stdout.write("Removendo dados de demonstração anteriores...")
        Comment.objects.all().delete()
        Like.objects.all().delete()
        Recommendation.objects.all().delete()
        Rating.objects.all().delete()
        Post.objects.all().delete()
        Follow.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

    def _create_demo_user(self):
        user, created = User.objects.get_or_create(
            username="demo",
            defaults={"email": "demo@cineclub.com"},
        )
        if created:
            user.set_password("cineclub123")
            user.save()
            user.profile.display_name = "Usuário Demo"
            user.profile.bio = "Conta de demonstração para correção do projeto."
            user.profile.save()
            self.stdout.write(
                "Usuário de demonstração criado (demo@cineclub.com / cineclub123).",
            )
        return user

    def _create_fake_users(self, fake, n):
        users = []
        for _ in range(n):
            username = fake.unique.user_name()
            user = User.objects.create_user(
                username=username,
                email=f"{username}@example.com",
                password="senha123456",
            )
            user.profile.display_name = fake.name()
            user.profile.bio = random.choice(DEMO_BIOS)
            user.profile.save()
            users.append(user)
        self.stdout.write(f"{n} usuários fictícios criados.")
        return users

    def _create_follows(self, users):
        count = 0
        for user in users:
            possible = [u for u in users if u != user]
            to_follow = random.sample(
                possible,
                k=min(random.randint(1, 5), len(possible)),
            )
            for target in to_follow:
                _, created = Follow.objects.get_or_create(
                    follower=user,
                    followed=target,
                )
                count += created
        self.stdout.write(f"{count} relações de 'seguir' criadas.")

    def _create_posts(self, fake, users, n):
        posts = []
        for _ in range(n):
            film = random.choice(DEMO_TITLES)
            author = random.choice(users)
            post = Post.objects.create(
                user=author,
                tmdb_id=film["tmdb_id"],
                media_type=film["media_type"],
                title=film["title"],
                poster_url=film["poster_url"],
                comment=(
                    random.choice(DEMO_COMMENTS)
                    if random.random() < COMMENT_PROBABILITY
                    else ""
                ),
            )
            posts.append(post)
        self.stdout.write(f"{n} indicações criadas.")
        return posts

    def _create_likes(self, users, posts):
        count = 0
        for post in posts:
            likers = random.sample(users, k=random.randint(0, min(8, len(users))))
            for liker in likers:
                _, created = Like.objects.get_or_create(user=liker, post=post)
                count += created
        self.stdout.write(f"{count} curtidas criadas.")

    def _create_comments(self, fake, users, posts):
        count = 0
        for post in posts:
            n_comments = random.randint(0, 4)
            commenters = random.sample(users, k=min(n_comments, len(users)))
            for commenter in commenters:
                Comment.objects.create(
                    post=post,
                    user=commenter,
                    content=random.choice(DEMO_COMMENTS),
                )
                count += 1
        self.stdout.write(f"{count} comentários criados.")

    def _create_ratings(self, users, posts):
        count = 0
        seen_films = {(p.tmdb_id, p.media_type) for p in posts}
        for tmdb_id, media_type in seen_films:
            raters = random.sample(users, k=random.randint(1, min(10, len(users))))
            for rater in raters:
                _, created = Rating.objects.get_or_create(
                    user=rater,
                    tmdb_id=tmdb_id,
                    media_type=media_type,
                    defaults={"score": random.randint(4, 10)},
                )
                count += created
        self.stdout.write(f"{count} avaliações criadas.")
