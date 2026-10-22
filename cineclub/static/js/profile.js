// static/js/profile.js
(function () {
  // ── Editar perfil (mostrar/ocultar formulário) ─────────
  const editBtn = document.getElementById("editProfileBtn");
  const cancelBtn = document.getElementById("cancelEditBtn");
  const editForm = document.getElementById("editProfileForm");
  const profileView = document.getElementById("profileView");

  if (editBtn) {
    editBtn.addEventListener("click", () => {
      editForm.style.display = "block";
      profileView.style.display = "none";
      editBtn.style.display = "none";
    });
  }
  if (cancelBtn) {
    cancelBtn.addEventListener("click", () => {
      editForm.style.display = "none";
      profileView.style.display = "block";
      editBtn.style.display = "inline-block";
    });
  }

  // ── Upload de avatar: clique no ícone abre o input de arquivo real ──
  const avatarEditBtn = document.getElementById("avatarEditBtn");
  const avatarFileInput = document.querySelector("#editProfileForm input[type=file]");
  if (avatarEditBtn && avatarFileInput) {
    avatarEditBtn.addEventListener("click", () => {
      editForm.style.display = "block";
      profileView.style.display = "none";
      if (editBtn) editBtn.style.display = "none";
      avatarFileInput.click();
    });
    avatarFileInput.addEventListener("change", () => {
      if (avatarFileInput.files.length) editForm.submit();
    });
  }

  // ── Seguir / deixar de seguir ───────────────────────────
  const followBtn = document.getElementById("followBtn");
  if (followBtn) {
    followBtn.addEventListener("click", async () => {
      const userId = followBtn.dataset.userId;
      followBtn.disabled = true;
      try {
        const data = await window.fetchJSON(`/accounts/seguir/${userId}/`, { method: "POST" });
        followBtn.classList.toggle("following", data.following);
        followBtn.textContent = data.following ? "Deixar de seguir" : "+ Seguir";
      } finally {
        followBtn.disabled = false;
      }
    });
  }

  // ── Abas: Posts | Buscar usuários ───────────────────────
  document.querySelectorAll(".profile-tabs a").forEach((tab) => {
    tab.addEventListener("click", (e) => {
      e.preventDefault();
      document.querySelectorAll(".profile-tabs a").forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      document.querySelectorAll(".tab-content").forEach((c) => (c.style.display = "none"));
      const target = document.getElementById(`tab-${tab.dataset.tab}`);
      if (target) target.style.display = "block";
    });
  });

  // ── Busca de usuários ───────────────────────────────────
  const searchInput = document.getElementById("userSearchInput");
  const searchResults = document.getElementById("userSearchResults");
  let debounceTimer = null;

  if (searchInput) {
    searchInput.addEventListener("input", () => {
      clearTimeout(debounceTimer);
      const q = searchInput.value.trim();
      if (q.length < 2) {
        searchResults.innerHTML = "";
        return;
      }
      debounceTimer = setTimeout(async () => {
        const data = await window.fetchJSON(`/accounts/buscar/?q=${encodeURIComponent(q)}`);
        renderUserResults(data);
      }, 400);
    });
  }

  function renderUserResults(users) {
    if (!users.length) {
      searchResults.innerHTML = `<div style="color:#555;font-size:14px;text-align:center;padding:20px 0;">Nenhum usuário encontrado.</div>`;
      return;
    }
    searchResults.innerHTML = users
      .map(
        (u) => `
      <a href="/accounts/perfil/${encodeURIComponent(u.username)}/" class="user-search-item" style="text-decoration:none;">
        <img src="${u.avatar_url}" alt="${u.username}">
        <div style="flex:1;">
          <div style="font-weight:700;font-size:14px;color:var(--fg);">${escapeHtml(u.display_name)}</div>
          <div style="font-size:12px;color:#555;">@${u.username}</div>
        </div>
        <div style="font-size:11px;color:#444;text-align:right;">
          <div>${u.posts_count} posts</div>
          <div>${u.followers_count} seguidores</div>
        </div>
      </a>`
      )
      .join("");
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }
})();
