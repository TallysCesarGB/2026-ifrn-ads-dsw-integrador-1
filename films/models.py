# O app "films" não possui tabelas próprias: os dados de filmes/séries vêm
# sempre da API pública da TMDB (com cache em memória). Os relacionamentos
# do CineClub com filmes (posts, avaliações) ficam nos apps `posts` e
# `ratings`, referenciando apenas `tmdb_id` + `media_type`.
