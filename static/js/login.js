document.addEventListener("DOMContentLoaded", function () {

    const form = document.getElementById("loginForm");

    const email = document.getElementById("email");
    const password = document.getElementById("password");

    const emailError = document.getElementById("emailError");
    const passwordError = document.getElementById("passwordError");

    // Email validation while typing
    email.addEventListener("input", function () {

        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        if (email.value.trim() === "") {
            emailError.textContent = "Email is required.";
        }
        else if (!emailPattern.test(email.value.trim())) {
            emailError.textContent = "Please enter a valid email address.";
        }
        else {
            emailError.textContent = "";
        }
    });

    // Password validation while typing
    password.addEventListener("input", function () {

        if (password.value === "") {
            passwordError.textContent = "Password is required.";
        }
        else if (password.value.length < 6) {
            passwordError.textContent =
                "Password must contain at least 6 characters.";
        }
        else {
            passwordError.textContent = "";
        }
    });

    // Login submit
    form.addEventListener("submit", function (event) {

        event.preventDefault();

        let valid = true;

        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        if (!emailPattern.test(email.value.trim())) {
            emailError.textContent =
                "Please enter a valid email address.";
            valid = false;
        }

        if (password.value.length < 6) {
            passwordError.textContent =
                "Password must contain at least 6 characters.";
            valid = false;
        }

        if (!valid) {
            return;
        }

        const formData = new FormData(form);

        fetch("/login", {
            method: "POST",
            body: new URLSearchParams(formData)
        })
        .then(response => {

            if (response.redirected) {
                window.location.href = response.url;
            }
            else {
                return response.text();
            }

        })
        .then(data => {

            if (data) {
                document.getElementById("message").textContent = data;
            }

        })
        .catch(error => {

            console.error("Login Error:", error);

            document.getElementById("message").textContent =
                "Login failed. Please try again.";

        });

    });

});