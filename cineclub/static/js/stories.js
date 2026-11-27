// static/js/stories.js
// Reimplementação do visualizador de "stories" (Stories.jsx) em vanilla JS.
(function () {
  const CATEGORIES = [
    { key: "movies", icon: "clapperboard", label: "Filmes BR" },
    { key: "series", icon: "tv", label: "Séries BR" },
    { key: "world", icon: "globe", label: "Top Mundo" },
    { key: "upcoming", icon: "rocket", label: "Lançamentos" },
    { key: "app", icon: "star", label: "CineClub" },
    { key: "rated", icon: "trophy", label: "Avaliados" },
  ];

  const STORY_DURATION = 5000;
  const cache = {};
  const viewed = {};

  const viewer = document.getElementById("storyViewer");
  if (!viewer) return;

  const backdrop = document.getElementById("storyBackdrop");
  const barsWrap = document.getElementById("storyBars");
  const catIcon = document.getElementById("storyCatIcon");
  const catLabel = document.getElementById("storyCatLabel");
  const rankLabel = document.getElementById("storyRankLabel");
  const rankGhost = document.getElementById("storyRankGhost");
  const poster = document.getElementById("storyPoster");
  const badge = document.getElementById("storyBadge");
  const titleEl = document.getElementById("storyTitle");
  const metaEl = document.getElementById("storyMeta");
  const overviewEl = document.getElementById("storyOverview");
  const ctaBtn = document.getElementById("storyCta");
  const closeBtn = document.getElementById("storyCloseBtn");

  let currentCategory = null;
  let currentIndex = 0;
  let timer = null;
  let startedAt = 0;

  // Selo da posição: medalha ouro/prata/bronze no pódio, chama no top 5.
  function rankBadgeHTML(rank) {
    const icon = window.icon;
    if (rank === 1) return `${icon("medal", "icon-sm medal-1")} #1 — O Melhor!`;
    if (rank === 2) return `${icon("medal", "icon-sm medal-2")} #2 — Vice`;
    if (rank === 3) return `${icon("medal", "icon-sm medal-3")} #3 — Pódio`;
    if (rank <= 5) return `${icon("flame", "icon-sm")} #${rank} — Top 5`;
    return `#${rank} — Top 10`;
  }

  async function loadCategory(key) {
    if (cache[key]) return cache[key];
    const data = await window.fetchJSON(`/filmes/rankings/${key}/`);
    cache[key] = data;
    return data;
  }

  function renderBars(total, activeIndex, progress) {
    barsWrap.innerHTML = "";
    for (let i = 0; i < total; i++) {
      const barIndex = total - 1 - i;
      let fill = 0;
      if (barIndex > activeIndex) fill = 100;
      else if (barIndex === activeIndex) fill = progress;
      const bar = document.createElement("div");
      bar.className = "story-bar";
      const inner = document.createElement("div");
      inner.className = "story-bar-fill";
      inner.style.width = fill + "%";
      bar.appendChild(inner);
      barsWrap.appendChild(bar);
    }
  }

  function renderItem() {
    const data = cache[currentCategory];
    if (!data || !data.items || !data.items.length) return;
    const total = data.items.length;
    const item = data.items[currentIndex];
    const currentRank = total - currentIndex;

    const catMeta = CATEGORIES.find((c) => c.key === currentCategory);
    // O ícone vem da API (`icon`); o da lista local é só fallback.
    catIcon.innerHTML = window.icon(data.icon || catMeta.icon);
    catLabel.textContent = data.label;
    rankLabel.textContent = `#${currentRank} de ${total}`;
    rankGhost.textContent = `#${currentRank}`;
    badge.innerHTML = rankBadgeHTML(currentRank);
    titleEl.textContent = item.title;
    overviewEl.textContent = item.overview || "";

    if (item.backdrop_url || item.poster_url) {
      backdrop.src = item.backdrop_url || item.poster_url;
      backdrop.style.display = "block";
    } else {
      backdrop.removeAttribute("src");
      backdrop.style.display = "none";
    }

    if (item.poster_url) {
      poster.src = item.poster_url;
      poster.style.display = "block";
    } else {
      poster.style.display = "none";
    }

    const metaParts = [];
    // Os valores vêm da API como números; só os ícones são HTML.
    const icon = window.icon;
    if (item.year) metaParts.push(`${icon("calendar")} ${Number(item.year)}`);
    if (item.rating > 0) metaParts.push(`${icon("star", "rating-star")} ${Number(item.rating)}`);
    if (item.total_posts > 0) metaParts.push(`${icon("clapperboard")} ${Number(item.total_posts)} indicações`);
    if (item.total_ratings > 0) metaParts.push(`${icon("chart-column")} ${Number(item.total_ratings)} avaliações`);
    metaEl.innerHTML = metaParts.map((p) => `<span class="with-icon">${p}</span>`).join("");

    ctaBtn.onclick = () => goToFilm(item);
    poster.onclick = () => goToFilm(item);

    renderBars(total, currentIndex, 0);
    startTimer();
  }

  function goToFilm(item) {
    window.location.href = `/filmes/${item.media_type}/${item.tmdb_id}/`;
  }

  function startTimer() {
    clearInterval(timer);
    startedAt = Date.now();
    timer = setInterval(() => {
      const elapsed = Date.now() - startedAt;
      const pct = Math.min((elapsed / STORY_DURATION) * 100, 100);
      const data = cache[currentCategory];
      renderBars(data.items.length, currentIndex, pct);
      if (pct >= 100) {
        nextItem();
      }
    }, 60);
  }

  function pauseTimer() {
    clearInterval(timer);
  }

  function nextItem() {
    const data = cache[currentCategory];
    if (currentIndex > 0) {
      currentIndex -= 1;
      renderItem();
    } else {
      viewed[currentCategory] = true;
      const idx = CATEGORIES.findIndex((c) => c.key === currentCategory);
      const nextCat = CATEGORIES.slice(idx + 1).find((c) => cache[c.key]);
      if (nextCat) {
        openStory(nextCat.key);
      } else {
        closeStory();
      }
    }
  }

  function prevItem() {
    const data = cache[currentCategory];
    if (currentIndex < data.items.length - 1) {
      currentIndex += 1;
      renderItem();
    }
  }

  async function openStory(key) {
    try {
      await loadCategory(key);
    } catch (e) {
      return;
    }
    currentCategory = key;
    currentIndex = cache[key].items.length - 1;
    viewer.classList.add("open");
    renderItem();
    markBubbleViewed(key);
  }

  function closeStory() {
    if (currentCategory) viewed[currentCategory] = true;
    pauseTimer();
    viewer.classList.remove("open");
    currentCategory = null;
  }

  function markBubbleViewed(key) {
    const bubble = document.querySelector(`.story-bubble[data-category="${key}"]`);
    if (!bubble) return;
    bubble.querySelector(".story-ring").classList.add("viewed");
    bubble.querySelector(".story-label").classList.add("viewed");
  }

  document.querySelectorAll(".story-bubble").forEach((btn) => {
    btn.addEventListener("click", () => openStory(btn.dataset.category));
  });

  closeBtn.addEventListener("click", closeStory);

  // Toque/clique: metade esquerda volta, direita avança. Segurar pausa.
  let pointerDownX = null;
  let pointerDownTime = null;

  function onDown(e) {
    pauseTimer();
    const x = e.touches ? e.touches[0].clientX : e.clientX;
    pointerDownX = x;
    pointerDownTime = Date.now();
  }

  function onUp(e) {
    if (pointerDownX === null) return;
    const x = e.changedTouches ? e.changedTouches[0].clientX : e.clientX;
    const dt = Date.now() - pointerDownTime;
    const dx = Math.abs(x - pointerDownX);
    pointerDownX = null;
    startTimer();
    if (dx > 15) return;
    if (dt < 300) {
      // Mede pela coluna do story (no desktop ela fica centralizada, não ocupa a tela toda)
      const area = viewer.querySelector(".story-content").getBoundingClientRect();
      if (x < area.left + area.width / 3) prevItem();
      else nextItem();
    }
  }

  viewer.addEventListener("mousedown", (e) => {
    if (e.target.closest(".story-close, .story-cta, #storyPoster")) return;
    onDown(e);
  });
  viewer.addEventListener("mouseup", (e) => {
    if (e.target.closest(".story-close, .story-cta, #storyPoster")) return;
    onUp(e);
  });
  viewer.addEventListener("touchstart", (e) => {
    if (e.target.closest(".story-close, .story-cta, #storyPoster")) return;
    onDown(e);
  });
  viewer.addEventListener("touchend", (e) => {
    if (e.target.closest(".story-close, .story-cta, #storyPoster")) return;
    onUp(e);
  });
})();
