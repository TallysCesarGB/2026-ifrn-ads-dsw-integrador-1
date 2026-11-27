"""Ícones SVG no lugar de emojis (#54)."""

import re
from pathlib import Path

import pytest
from django.conf import settings
from django.template import Context
from django.template import Template
from django.templatetags.static import static

APPS_DIR = Path(settings.APPS_DIR)
REPO_DIR = APPS_DIR.parent
SPRITE = APPS_DIR / "static" / "icons" / "sprite.svg"
TEMPLATES = sorted((APPS_DIR / "templates").rglob("*.html"))
SCRIPTS = sorted((APPS_DIR / "static" / "js").glob("*.js"))
SERVICES = REPO_DIR / "films" / "services.py"

# Emojis e símbolos usados como ícone (setas, ✕, ⏻, ⓘ, ▶, ★…). Fica de fora
# o bloco de "box drawing" (U+2500 a U+259F), usado nos comentários de seção.
ICON_LIKE_CHARS = re.compile(
    "[\u2190-\u21ff\u2300-\u23ff\u2460-\u24ff\u25a0-\u27bf"
    "\u2b00-\u2bff\U0001f000-\U0001faff\ufe0f]",
)


def render(source: str, **context) -> str:
    return Template("{% load icons %}" + source).render(Context(context))


def used_icons() -> set[str]:
    names: set[str] = set()
    for path in TEMPLATES:
        names |= set(re.findall(r'{%\s*icon\s+"([a-z0-9-]+)"', path.read_text()))
    for path in SCRIPTS:
        text = path.read_text()
        names |= set(re.findall(r'\bicon\(\s*"([a-z0-9-]+)"', text))
        names |= set(re.findall(r'setIcon\([^,]+,\s*"([a-z0-9-]+)"', text))
        names |= set(re.findall(r'\bicon:\s*"([a-z0-9-]+)"', text))
        # icon(film.media_type === "tv" ? "tv" : "clapperboard")
        for pair in re.findall(r'\?\s*"([a-z0-9-]+)"\s*:\s*"([a-z0-9-]+)"\)', text):
            names |= set(pair)
    names |= set(
        re.findall(r'\("[^"]+",\s*"([a-z0-9-]+)",\s*ranking_', SERVICES.read_text()),
    )
    return names


def sprite_symbols() -> set[str]:
    return set(re.findall(r'<symbol id="([a-z0-9-]+)"', SPRITE.read_text()))


class TestIconTag:
    def test_decorative_icon_is_hidden_from_screen_readers(self):
        html = render('{% icon "heart" %}')

        assert html == (
            '<svg class="icon" aria-hidden="true" focusable="false">'
            f'<use href="{static("icons/sprite.svg")}#heart"></use></svg>'
        )

    def test_label_gives_accessible_name(self):
        html = render('{% icon "log-out" label="Sair" %}')

        assert 'role="img" aria-label="Sair"' in html
        assert "aria-hidden" not in html

    def test_extra_class_is_appended(self):
        assert 'class="icon icon-sm"' in render('{% icon "star" class="icon-sm" %}')

    def test_values_are_escaped(self):
        html = render('{% icon "x" label=nome %}', nome="<b>")

        assert "<b>" not in html
        assert "&lt;b&gt;" in html


class TestSprite:
    def test_every_used_icon_exists_in_sprite(self):
        missing = used_icons() - sprite_symbols()
        assert not missing, f"Ícones sem <symbol> no sprite: {sorted(missing)}"

    def test_sprite_has_only_used_icons(self):
        unused = sprite_symbols() - used_icons()
        assert not unused, f"Ícones no sprite que ninguém usa: {sorted(unused)}"


@pytest.mark.parametrize(
    "path",
    [*TEMPLATES, *SCRIPTS, SERVICES],
    ids=lambda p: str(p.relative_to(REPO_DIR)),
)
def test_no_emoji_used_as_icon(path):
    offenders = [
        f"{n}: {line.strip()}"
        for n, line in enumerate(path.read_text().splitlines(), 1)
        if ICON_LIKE_CHARS.search(line)
    ]
    assert not offenders, "\n".join(offenders)
