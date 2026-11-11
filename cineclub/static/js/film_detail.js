// static/js/film_detail.js
(function () {
  const root = document.getElementById("filmDetailRoot");
  if (!root) return;

  const tmdbId = root.dataset.tmdbId;
  const mediaType = root.dataset.mediaType;

  // ── Trailer ──────────────────────────────────────────
  const playBtn = document.getElementById("playTrailerBtn");
  const closeTrailerBtn = document.getElementById("closeTrailerBtn");
  const trailerWrap = document.getElementById("trailerFrameWrap");
  const trailerFrame = document.getElementById("trailerFrame");
  const backdropWrap = document.getElementById("backdropWrap");
  const filmTypeBadge = document.getElementById("filmTypeBadge");
  const filmHero = document.getElementById("filmHero");

  if (playBtn) {
    playBtn.addEventListener("click", () => {
      trailerFrame.src = playBtn.dataset.trailerUrl;
      filmHero.classList.add("is-playing");
      trailerWrap.style.display = "block";
      backdropWrap.style.display = "none";
      closeTrailerBtn.style.display = "block";
      filmTypeBadge.style.display = "none";
    });
  }
  if (closeTrailerBtn) {
    closeTrailerBtn.addEventListener("click", () => {
      trailerFrame.src = "";
      filmHero.classList.remove("is-playing");
      trailerWrap.style.display = "none";
      backdropWrap.style.display = "block";
      closeTrailerBtn.style.display = "none";
      filmTypeBadge.style.display = "block";
    });
  }

  // ── Voltar ───────────────────────────────────────────
  // Volta para a página anterior do próprio site; sem histórico (link aberto
  // direto ou em nova aba) segue o href, que aponta para o feed.
  const backLink = document.getElementById("filmBackLink");
  if (backLink) {
    backLink.addEventListener("click", (e) => {
      const cameFromSite = document.referrer.startsWith(window.location.origin);
      if (cameFromSite && window.history.length > 1) {
        e.preventDefault();
        window.history.back();
      }
    });
  }

  // ── Tabs ─────────────────────────────────────────────
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById(`tab-${btn.dataset.tab}`).classList.add("active");
    });
  });

  // ── Avaliação (1 a 10) ───────────────────────────────
  const rateRow = document.getElementById("rateRow");
  const myScoreLabel = document.getElementById("myScoreLabel");

  function paintScore(score) {
    rateRow.querySelectorAll(".rate-btn").forEach((btn) => {
      btn.classList.toggle("active", parseInt(btn.dataset.score, 10) <= score);
    });
  }

  rateRow.querySelectorAll(".rate-btn").forEach((btn) => {
    btn.addEventListener("mouseenter", () => paintScore(parseInt(btn.dataset.score, 10)));
    btn.addEventListener("click", async () => {
      const score = parseInt(btn.dataset.score, 10);
      try {
        const data = await window.fetchJSON(`/avaliacoes/avaliar/`, {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: `tmdb_id=${tmdbId}&media_type=${mediaType}&score=${score}`,
        });
        paintScore(score);
        myScoreLabel.textContent = `Sua avaliação: ${score}/10`;
        const cineclubValueEl = document.querySelector(".score-card:nth-child(2) .value");
        if (cineclubValueEl) cineclubValueEl.textContent = data.average || "—";
        const cineclubSubEl = document.querySelector(".score-card:nth-child(2) .sub");
        if (cineclubSubEl) cineclubSubEl.textContent = `${data.total} avaliações`;
      } catch (e) {
        console.error(e);
      }
    });
  });

  rateRow.addEventListener("mouseleave", () => {
    const my = root.dataset.myScore;
    paintScore(my ? parseInt(my, 10) : 0);
  });
})();
