// static/js/new_post.js
// Busca na TMDB (debounced) + seleção de filme/série para nova indicação.
(function () {
  const input = document.getElementById("filmSearchInput");
  if (!input) return;

  const resultsBox = document.getElementById("searchResults");
  const errorBox = document.getElementById("searchError");
  const icon = document.getElementById("searchIcon");
  const typeFilters = document.querySelectorAll(".type-filter-opt");

  const searchStep = document.getElementById("searchStep");
  const selectedStep = document.getElementById("selectedStep");
  const changeFilmBtn = document.getElementById("changeFilmBtn");

  let currentType = "multi";
  let debounceTimer = null;

  typeFilters.forEach((el) => {
    el.addEventListener("click", (e) => {
      e.preventDefault();
      typeFilters.forEach((x) => x.classList.remove("active"));
      el.classList.add("active");
      currentType = el.dataset.type;
      resultsBox.innerHTML = "";
      if (input.value.trim().length >= 2) doSearch();
    });
  });

  input.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    errorBox.textContent = "";
    if (input.value.trim().length < 2) {
      resultsBox.innerHTML = "";
      return;
    }
    debounceTimer = setTimeout(doSearch, 400);
  });

  async function doSearch() {
    icon.textContent = "⏳";
    try {
      const query = encodeURIComponent(input.value.trim());
      const data = await window.fetchJSON(`/filmes/buscar/?q=${query}&type=${currentType}`);
      renderResults(data);
      if (data.length === 0) errorBox.textContent = "Nenhum resultado encontrado. Tente outro título.";
    } catch (e) {
      errorBox.textContent = "Erro ao buscar na TMDB. Verifique se a API Key está configurada.";
    } finally {
      icon.textContent = "🔍";
    }
  }

  function renderResults(items) {
    resultsBox.innerHTML = items
      .map(
        (film, idx) => `
      <button type="button" class="search-result" data-idx="${idx}">
        ${
          film.poster_url
            ? `<img src="${film.poster_url}" alt="${escapeAttr(film.title)}">`
            : `<div style="width:46px;height:70px;background:#1a1a2e;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0;">${film.media_type === "tv" ? "📺" : "🎬"}</div>`
        }
        <div style="flex:1;min-width:0;text-align:left;">
          <div style="font-weight:700;font-size:14px;color:var(--fg);margin-bottom:3px;">${escapeHtml(film.title)}</div>
          <div style="font-size:12px;color:#666;display:flex;gap:10px;margin-bottom:4px;flex-wrap:wrap;">
            <span class="pill ${film.media_type}">${film.media_type === "tv" ? "📺 Série" : "🎬 Filme"}</span>
            ${film.year ? `<span>📅 ${film.year}</span>` : ""}
            ${film.rating ? `<span>★ ${Number(film.rating).toFixed(1)}</span>` : ""}
          </div>
        </div>
      </button>`
      )
      .join("");

    resultsBox.querySelectorAll(".search-result").forEach((btn) => {
      btn.addEventListener("click", () => selectFilm(items[parseInt(btn.dataset.idx, 10)]));
    });
  }

  function selectFilm(film) {
    document.getElementById("id_tmdb_id").value = film.tmdb_id;
    document.getElementById("id_media_type").value = film.media_type;
    document.getElementById("id_title").value = film.title;
    document.getElementById("id_poster_url").value = film.poster_url || "";

    document.getElementById("selectedTypePill").textContent = film.media_type === "tv" ? "📺 Série" : "🎬 Filme";
    document.getElementById("selectedTypePill").className = `pill ${film.media_type}`;
    document.getElementById("selectedTitle").textContent = film.title;
    const metaParts = [];
    if (film.year) metaParts.push(`📅 ${film.year}`);
    if (film.rating) metaParts.push(`★ ${Number(film.rating).toFixed(1)}`);
    document.getElementById("selectedMeta").textContent = metaParts.join(" · ");

    const posterEl = document.getElementById("selectedPoster");
    if (film.poster_url) {
      posterEl.src = film.poster_url;
      posterEl.style.display = "block";
    } else {
      posterEl.style.display = "none";
    }

    searchStep.style.display = "none";
    selectedStep.style.display = "block";
  }

  changeFilmBtn.addEventListener("click", () => {
    selectedStep.style.display = "none";
    searchStep.style.display = "block";
    input.value = "";
    resultsBox.innerHTML = "";
    input.focus();
  });

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }
  function escapeAttr(str) {
    return escapeHtml(str).replace(/"/g, "&quot;");
  }
})();
