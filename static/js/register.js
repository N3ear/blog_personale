function showMessage(text, type = "error") {
    const el = document.getElementById("message");
    if (!el) return;
    el.textContent = text;
    el.className = `message ${type}`;
}

document.getElementById("registerForm").addEventListener("submit", async function (e) {
    e.preventDefault();

    const username = document.getElementById("username").value;
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    try {
        const response = await fetch("/api/register", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ username, email, password })
        });

        const data = await response.json();

        if (response.ok) {
            showMessage("Registrazione completata. Ora puoi fare login.", "success");
            setTimeout(() => {
                window.location.href = "/login";
            }, 800);
        } else {
            const errorText = data.error || "Errore nella registrazione. Riprova.";
            showMessage(errorText);
            if (errorText.toLowerCase().includes("esist")) {
                setTimeout(() => {
                    window.location.href = "/login";
                }, 900);
            }
        }
    } catch (err) {
        showMessage("Errore di rete. Controlla la connessione e riprova.");
    }
});
