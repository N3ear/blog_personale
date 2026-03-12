(function () {
    const STORAGE_KEY = "theme";

    const applyTheme = (theme) => {
        if (theme === "dark") {
            document.body.classList.add("dark");
        } else {
            document.body.classList.remove("dark");
        }
    };

    const getPreferredTheme = () => {
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved === "dark" || saved === "light") return saved;
        return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches
            ? "dark"
            : "light";
    };

    const createToggle = () => {
        const btn = document.createElement("button");
        btn.className = "theme-toggle";
        btn.setAttribute("aria-label", "Attiva o disattiva modalità scura");

        const updateLabel = () => {
            const isDark = document.body.classList.contains("dark");
            btn.innerHTML = `<span class="theme-toggle__icon">${isDark ? "🌙" : "☀️"}</span>${isDark ? "Scuro" : "Chiaro"}`;
        };

        btn.addEventListener("click", () => {
            const nextTheme = document.body.classList.contains("dark") ? "light" : "dark";
            applyTheme(nextTheme);
            localStorage.setItem(STORAGE_KEY, nextTheme);
            updateLabel();
        });

        updateLabel();
        document.body.appendChild(btn);
    };

    // Init
    const theme = getPreferredTheme();
    applyTheme(theme);
    window.addEventListener("DOMContentLoaded", createToggle, { once: true });
})();
