
document.addEventListener("DOMContentLoaded", function () {

    const passwordInput = document.getElementById("loginPassword");
    const toggleButton = document.getElementById("togglePassword");

    if (passwordInput && toggleButton) {

        toggleButton.addEventListener("click", function () {

            const isPassword = passwordInput.type === "password";

            passwordInput.type = isPassword ? "text" : "password";

            toggleButton.innerHTML = isPassword
                ? '<i class="fa-regular fa-eye-slash"></i>'
                : '<i class="fa-regular fa-eye"></i>';

            toggleButton.setAttribute(
                "aria-label",
                isPassword ? "Hide password" : "Show password"
            );

        });

    }

});
