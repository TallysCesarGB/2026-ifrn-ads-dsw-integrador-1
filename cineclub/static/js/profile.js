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
})();
