function showMessage(text, type = "error") {
    const el = document.getElementById("message");
    if (!el) return;
    el.textContent = text;
    el.className = `message ${type}`;
}

document.getElementById("loginForm").addEventListener("submit", async function (e) {
    e.preventDefault();

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();

    try {
        const res = await fetch("/api/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });

        const data = await res.json();

        if (res.ok) {
            if (data.token) {
                localStorage.setItem("token", data.token);
            }
            window.location.href = "/articles";
            return;
        }

        showMessage(data.error || "Errore durante il login");
    } catch (err) {
        showMessage("Errore di rete. Controlla la connessione e riprova.");
    }
});
