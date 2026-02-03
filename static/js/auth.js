function showMessage(text, type = "error") {
    const el = document.getElementById("message");
    if (!el) return;
    el.textContent = text;
    el.className = `message ${type}`;
}

document.getElementById("loginForm").addEventListener("submit", async function (e) {
    e.preventDefault();

    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    try {
        const response = await fetch("/api/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok) {
            showMessage("Login effettuato. Reindirizzamento in corso...", "success");
            window.location.href = "/articles";
        } else {
            showMessage(data.error || "Credenziali non valide. Riprova.");
        }
    } catch (err) {
        showMessage("Errore di rete. Controlla la connessione e riprova.");
    }
});
