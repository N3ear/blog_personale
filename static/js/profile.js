function showProfileMessage(text, type = "error") {
    const el = document.getElementById("profile-message");
    if (!el) return;
    el.textContent = text;
    el.className = `message ${type}`;
}

function getToken() {
    return localStorage.getItem("token");
}

function authHeaders(extra = {}) {
    const token = getToken();
    const headers = { ...extra };
    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }
    return headers;
}

async function initProfileEditor() {
    const form = document.getElementById("profile-edit-form");
    if (!form) return;

    const username = form.dataset.username;
    const token = getToken();
    if (!token) return;

    try {
        const meRes = await fetch("/api/me", { headers: authHeaders() });
        if (!meRes.ok) return;
        const me = await meRes.json();
        if (me.username !== username && !me.is_admin) return;

        form.style.display = "grid";

        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            const formData = new FormData(form);

            const res = await fetch(`/api/profile/${username}`, {
                method: "POST",
                headers: authHeaders(),
                body: formData
            });

            const data = await res.json();
            if (!res.ok) {
                showProfileMessage(data.error || "Errore aggiornamento profilo");
                return;
            }

            showProfileMessage("Profilo aggiornato con successo.", "success");
            setTimeout(() => window.location.reload(), 600);
        });
    } catch (err) {
        showProfileMessage("Errore di rete.");
    }
}

initProfileEditor();
