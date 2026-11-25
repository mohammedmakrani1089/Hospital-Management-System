
document.addEventListener("DOMContentLoaded", function () {

    // Password Show / Hide
    const toggleButtons = document.querySelectorAll(".password-toggle");

    toggleButtons.forEach(button => {

        button.addEventListener("click", function () {

            const targetId = this.dataset.target;
            const passwordInput = document.getElementById(targetId);

            if (!passwordInput) return;

            const isPassword = passwordInput.type === "password";

            passwordInput.type = isPassword ? "text" : "password";

            this.innerHTML = isPassword
                ? '<i class="fa-regular fa-eye-slash"></i>'
                : '<i class="fa-regular fa-eye"></i>';

            this.setAttribute(
                "aria-label",
                isPassword ? "Hide password" : "Show password"
            );

        });

    });

});
