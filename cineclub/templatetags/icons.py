"""Ícones SVG do sprite Lucide servido em ``static/icons/sprite.svg``.

Uso nos templates::

    {% load icons %}
    {% icon "heart" %}                       → decorativo (aria-hidden)
    {% icon "log-out" label="Sair" %}        → com nome acessível
    {% icon "star" class="rating-star" %}    → classes extras além de .icon

Os scripts que montam HTML usam o helper equivalente ``window.icon(name)``,
definido em ``base.html``.
"""

from django import template
from django.templatetags.static import static
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()

SPRITE_PATH = "icons/sprite.svg"


@register.simple_tag
def icon(name: str, **attrs) -> str:
    css_class = " ".join(filter(None, ["icon", attrs.get("class", "")]))
    label = attrs.get("label", "")
    if label:
        a11y = format_html('role="img" aria-label="{}"', label)
    else:
        a11y = mark_safe('aria-hidden="true" focusable="false"')
    return format_html(
        '<svg class="{}" {}><use href="{}#{}"></use></svg>',
        css_class,
        a11y,
        static(SPRITE_PATH),
        name,
    )
