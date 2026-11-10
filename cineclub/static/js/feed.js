// static/js/feed.js
// Interações do feed: curtir, comentar, recomendar, paginação "ver mais".
(function () {
  const container = document.getElementById("postsContainer");
  if (!container) return;

  function bindPost(card) {
    const postId = card.dataset.postId;

    const likeBtn = card.querySelector(".like-btn");
    if (likeBtn) {
      likeBtn.addEventListener("click", async () => {
        try {
          const data = await window.fetchJSON(`/posts/${postId}/curtir/`, { method: "POST" });
          likeBtn.classList.toggle("liked", data.liked);
          likeBtn.querySelector(".like-icon").textContent = data.liked ? "❤️" : "🤍";
          likeBtn.querySelector(".like-count").textContent = data.likes_count || "";
        } catch (e) {
          console.error(e);
        }
      });
    }

    const recommendBtn = card.querySelector(".recommend-btn");
    if (recommendBtn) {
      recommendBtn.addEventListener("click", async () => {
        try {
          await window.fetchJSON(`/posts/${postId}/recomendar/`, { method: "POST" });
          alert("Indicação recomendada para seus seguidores! 🎬");
        } catch (e) {
          console.error(e);
        }
      });
    }

    const commentToggle = card.querySelector(".comment-toggle-btn");
    const commentsBox = card.querySelector(`#comments-${postId}`);
    if (commentToggle && commentsBox) {
      commentToggle.addEventListener("click", async () => {
        const isOpen = commentsBox.classList.contains("open");
        if (isOpen) {
          commentsBox.classList.remove("open");
          return;
        }
        commentsBox.classList.add("open");
        try {
          const comments = await window.fetchJSON(`/posts/${postId}/comentarios/`);
          const list = commentsBox.querySelector(".comments-list");
          list.innerHTML = comments
            .map(
              (c) => `
              <div class="comment-item">
                <span class="who">@${c.username}</span> ${escapeHtml(c.content)}
                ${c.movie_rating ? `<span style="margin-left:8px;color:#f5c518;font-size:11px;">★ ${Number(c.movie_rating).toFixed(1)}</span>` : ""}
              </div>`
            )
            .join("");
        } catch (e) {
          console.error(e);
        }
      });
    }

    const commentForm = card.querySelector(".comment-form");
    if (commentForm) {
      commentForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const input = commentForm.querySelector("input[name=content]");
        const content = input.value.trim();
        if (!content) return;
        try {
          const comment = await window.fetchJSON(`/posts/${postId}/comentarios/novo/`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: `content=${encodeURIComponent(content)}`,
          });
          const list = commentsBox.querySelector(".comments-list");
          list.insertAdjacentHTML(
            "beforeend",
            `<div class="comment-item"><span class="who">@${comment.username}</span> ${escapeHtml(comment.content)}</div>`
          );
          input.value = "";
          const countEl = card.querySelector(".comment-count");
          countEl.textContent = (parseInt(countEl.textContent || "0", 10) || 0) + 1;
        } catch (e) {
          console.error(e);
        }
      });
    }
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  function bindAll() {
    container.querySelectorAll(".post-card").forEach(bindPost);
  }

  bindAll();

  const loadMoreBtn = document.getElementById("loadMoreBtn");
  if (loadMoreBtn) {
    loadMoreBtn.addEventListener("click", async () => {
      const page = loadMoreBtn.dataset.nextPage;
      loadMoreBtn.disabled = true;
      loadMoreBtn.textContent = "Carregando…";
      try {
        const data = await window.fetchJSON(`/feed/mais/?page=${page}`);
        container.insertAdjacentHTML("beforeend", data.html);
        bindAll();
        if (data.has_next) {
          loadMoreBtn.dataset.nextPage = parseInt(page, 10) + 1;
          loadMoreBtn.disabled = false;
          loadMoreBtn.textContent = "Ver mais";
        } else {
          loadMoreBtn.remove();
        }
      } catch (e) {
        loadMoreBtn.disabled = false;
        loadMoreBtn.textContent = "Ver mais";
      }
    });
  }
})();
