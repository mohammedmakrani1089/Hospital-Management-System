document.addEventListener("DOMContentLoaded", function () {
    const modal = document.getElementById("authModal");
    if (!modal) return;

    const loginLink = document.getElementById("modalLoginLink");
    const signupLink = document.getElementById("modalSignupLink");
    const closeButton = modal.querySelector("[data-close-modal]");

    // Close Popup helper
    function closeModal() {
        modal.classList.remove("show");
        document.body.style.overflow = "";
    }

    // Open Login / Signup Popup
    document.querySelectorAll(".js-open-auth").forEach(button => {
        button.addEventListener("click", function (event) {
            event.preventDefault();

            const doctorId = this.dataset.doctorId;

            const loginUrl = new URL(
                modal.dataset.loginUrl || "/login",
                window.location.origin
            );

            const signupUrl = new URL(
                modal.dataset.signupUrl || "/signup",
                window.location.origin
            );

            // Sirf valid doctorId hone par query param set karein
            if (doctorId) {
                loginUrl.searchParams.set("doctor_id", doctorId);
                signupUrl.searchParams.set("doctor_id", doctorId);
            }

            if (loginLink) loginLink.href = loginUrl.toString();
            if (signupLink) signupLink.href = signupUrl.toString();

            modal.classList.add("show");
            document.body.style.overflow = "hidden";
        });
    });

    // Close button par click listener (with null check)
    if (closeButton) {
        closeButton.addEventListener("click", closeModal);
    }

    // Modal background click to close
    modal.addEventListener("click", function (event) {
        if (event.target === modal) {
            closeModal();
        }
    });

    // Close using Escape key only when visible
    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && modal.classList.contains("show")) {
            closeModal();
        }
    });
});