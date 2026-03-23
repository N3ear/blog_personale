function getToken() {
    return localStorage.getItem("token");
}

function getAuthHeaders(extra = {}) {
    const token = getToken();
    const headers = { ...extra };
    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }
    return headers;
}

async function authFetch(url, options = {}) {
    const opts = { ...options };
    opts.headers = getAuthHeaders(options.headers || {});
    const res = await fetch(url, opts);
    if (res.status === 401) {
        localStorage.removeItem("token");
        window.location.href = "/login";
    }
    return res;
}

function showMessage(text, type = "error") {
    const el = document.getElementById("message");
    if (!el) return;
    el.textContent = text;
    el.className = `message ${type}`;
}

let currentUser = null;
let categories = [];

async function loadCurrentUser() {
    try {
        const res = await authFetch("/api/me");
        if (!res.ok) {
            currentUser = null;
            return;
        }
        currentUser = await res.json();
    } catch (err) {
        currentUser = null;
    }
}

async function loadUserBar() {
    const res = await authFetch("/api/me");
    const userBar = document.getElementById("user-bar");
    const profileLinkContainer = document.getElementById("profile-link-container");

    if (res.status === 401) {
        userBar.innerHTML = `
            <p>Non sei loggato.
            <a href="/login">Login</a></p>
        `;
        if (profileLinkContainer) {
            profileLinkContainer.innerHTML = "";
        }
        return;
    }

    const user = await res.json();
    userBar.innerHTML = `
        <p>Ciao <strong>${user.username}</strong></p>
        <button onclick="logout()">Logout</button>
    `;
    if (profileLinkContainer) {
        profileLinkContainer.innerHTML = `<a class="profile-link-btn" href="/profile/${user.username}">Vai al mio profilo</a>`;
    }
}

async function logout() {
    const res = await authFetch("/api/logout", { method: "POST" });
    if (res.ok) {
        localStorage.removeItem("token");
        window.location.href = "/login";
    } else {
        showMessage("Errore nel logout");
    }
}

async function loadCategories() {
    await loadCurrentUser();
    const res = await fetch("/api/categories");
    if (!res.ok) {
        showMessage("Errore nel caricamento delle categorie.");
        return;
    }
    categories = await res.json();
    renderCategoryList();
}

function renderCategoryList() {
    const container = document.getElementById("category-list");
    if (!container) return;
    container.innerHTML = "";
    if (!categories.length) {
        container.textContent = "Nessuna categoria.";
        return;
    }
    categories.forEach(c => {
        const wrapper = document.createElement("div");
        const delBtn = currentUser && currentUser.is_admin
            ? `<button class="pill-button danger" onclick="deleteCategory(${c.id})">Elimina</button>`
            : "";
        wrapper.innerHTML = `
            <span class="pill-button">${c.name}</span>
            ${delBtn}
        `;
        container.appendChild(wrapper);
    });
}

async function createCategory() {
    const name = document.getElementById("new-category-name")?.value.trim();
    if (!name) {
        showMessage("Inserisci un nome categoria.");
        return;
    }
    const res = await authFetch("/api/categories", {
        method: "POST",
        headers: {
            ...getAuthHeaders(),
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ name })
    });
    if (res.ok) {
        document.getElementById("new-category-name").value = "";
        showMessage("Categoria creata.", "success");
        await loadCategories();
    } else {
        const data = await res.json().catch(() => ({}));
        showMessage(data.error || "Errore creazione categoria.");
    }
}

async function deleteCategory(categoryId) {
    if (!currentUser || !currentUser.is_admin) {
        showMessage("Solo admin possono eliminare categorie.");
        return;
    }
    const ok = confirm("Eliminare la categoria? Gli articoli resteranno senza categoria.");
    if (!ok) return;
    const res = await authFetch(`/api/categories/${categoryId}`, { method: "DELETE" });
    if (res.ok) {
        showMessage("Categoria eliminata.", "success");
        await loadCategories();
    } else {
        const data = await res.json().catch(() => ({}));
        showMessage(data.error || "Errore eliminazione categoria.");
    }
}

async function init() {
    await loadUserBar();
    await loadCategories();
}

init();
