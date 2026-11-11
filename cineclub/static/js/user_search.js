// static/js/user_search.js
// Busca de usuários (página principal). Usa GET /accounts/buscar/?q=
(function () {
  const input = document.getElementById("userSearchInput");
  const results = document.getElementById("userSearchResults");
  if (!input || !results) return;

  const MIN_LENGTH = 2;
  const DEBOUNCE_MS = 400;
  let debounceTimer = null;
  let lastQuery = "";

  input.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    const q = input.value.trim();
    lastQuery = q;
    if (q.length < MIN_LENGTH) {
      results.replaceChildren();
      return;
    }
    debounceTimer = setTimeout(() => search(q), DEBOUNCE_MS);
  });

  async function search(q) {
    try {
      const users = await window.fetchJSON(`/accounts/buscar/?q=${encodeURIComponent(q)}`);
      // Ignora respostas atrasadas de uma busca que já não é a atual.
      if (q === lastQuery) render(users);
    } catch (e) {
      if (q === lastQuery) showMessage("Não foi possível buscar agora. Tente novamente.");
      console.error(e);
    }
  }

  // Monta o HTML com DOM (textContent/setAttribute) em vez de concatenar
  // strings: nome, username e avatar vêm do usuário e não podem virar HTML.
  function render(users) {
    if (!users.length) {
      showMessage("Nenhum usuário encontrado.");
      return;
    }
    results.replaceChildren(...users.map(userItem));
  }

  function userItem(u) {
    const link = el("a", "user-search-item");
    link.href = `/accounts/perfil/${encodeURIComponent(u.username)}/`;

    const avatar = el("img");
    avatar.src = u.avatar_url;
    avatar.alt = "";

    const names = el("div", "user-search-names");
    names.append(el("div", "user-search-name", u.display_name), el("div", "user-search-username", `@${u.username}`));

    const stats = el("div", "user-search-stats");
    stats.append(el("div", null, `${u.posts_count} posts`), el("div", null, `${u.followers_count} seguidores`));

    link.append(avatar, names, stats);
    return link;
  }

  function showMessage(text) {
    results.replaceChildren(el("div", "user-search-empty", text));
  }

  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }
})();
