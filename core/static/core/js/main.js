(function () {
    const gate = document.getElementById("age-verification");
    const siteContent = document.getElementById("site-content");
    const confirmButton = document.getElementById("age-verification-confirm");
    const denyButton = document.getElementById("age-verification-deny");
    const deniedMessage = document.getElementById("age-verification-denied");
    const storageKey = "liquor-store-a-age-verified";

    if (!gate || !siteContent || !confirmButton || !denyButton || !deniedMessage) {
        return;
    }

    function closeGate() {
        gate.hidden = true;
        siteContent.inert = false;
        document.body.classList.remove("age-gate-open");
        siteContent.focus();
    }

    try {
        if (window.localStorage.getItem(storageKey) === "true") {
            closeGate();
            return;
        }
    } catch (error) {
        // Keep the gate usable if browser storage is unavailable.
    }

    confirmButton.focus();

    confirmButton.addEventListener("click", function () {
        try {
            window.localStorage.setItem(storageKey, "true");
        } catch (error) {
            // Allow entry for this visit when browser storage is unavailable.
        }
        closeGate();
    });

    denyButton.addEventListener("click", function () {
        deniedMessage.hidden = false;
        denyButton.disabled = true;
        confirmButton.focus();
    });

    gate.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            event.preventDefault();
            return;
        }

        if (event.key === "Tab") {
            event.preventDefault();
            const nextButton = document.activeElement === confirmButton
                ? denyButton
                : confirmButton;
            nextButton.focus();
        }
    });
})();