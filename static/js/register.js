document.addEventListener("DOMContentLoaded", function () {

    const form = document.getElementById("registerForm");

    const fullname = document.getElementById("fullname");
    const email = document.getElementById("email");
    const password = document.getElementById("password");
    const role = document.getElementById("role");

    const adminEmailGroup =
        document.getElementById("adminEmailGroup");

    const adminEmail =
        document.getElementById("admin_email");

    const fullnameError =
        document.getElementById("fullnameError");

    const emailError =
        document.getElementById("emailError");

    const passwordError =
        document.getElementById("passwordError");

    const roleError =
        document.getElementById("roleError");

    const adminEmailError =
        document.getElementById("adminEmailError");


    // Full Name
    fullname.addEventListener("input", function () {

        if (fullname.value.trim() === "") {

            fullnameError.textContent =
                "Full name is required.";

        }
        else if (fullname.value.trim().length < 3) {

            fullnameError.textContent =
                "Full name must contain at least 3 characters.";

        }
        else {

            fullnameError.textContent = "";

        }
    });


    // Email
    email.addEventListener("input", function () {

        const emailPattern =
            /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        if (email.value.trim() === "") {

            emailError.textContent =
                "Email is required.";

        }
        else if (!emailPattern.test(email.value.trim())) {

            emailError.textContent =
                "Please enter a valid email address.";

        }
        else {

            emailError.textContent = "";

        }
    });


    // Password
    password.addEventListener("input", function () {

        if (password.value === "") {

            passwordError.textContent =
                "Password is required.";

        }
        else if (password.value.length < 6) {

            passwordError.textContent =
                "Password must contain at least 6 characters.";

        }
        else {

            passwordError.textContent = "";

        }
    });


    // Role Change
    role.addEventListener("change", function () {

        if (role.value === "") {

            roleError.textContent =
                "Please select an account type.";

            adminEmailGroup.style.display = "none";
            adminEmail.required = false;

        }
        else {

            roleError.textContent = "";

            if (role.value === "Team Member") {

                // Show Admin Email
                adminEmailGroup.style.display = "block";

                adminEmail.required = true;

            }
            else {

                // Hide Admin Email for Admin
                adminEmailGroup.style.display = "none";

                adminEmail.required = false;
                adminEmail.value = "";
                adminEmailError.textContent = "";

            }
        }
    });


    // Admin Email Validation
    adminEmail.addEventListener("input", function () {

        const emailPattern =
            /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        if (adminEmail.value.trim() === "") {

            adminEmailError.textContent =
                "Admin email is required.";

        }
        else if (!emailPattern.test(adminEmail.value.trim())) {

            adminEmailError.textContent =
                "Please enter a valid Admin email.";

        }
        else {

            adminEmailError.textContent = "";

        }
    });


    // Submit
    form.addEventListener("submit", function (event) {

        event.preventDefault();

        let valid = true;


        // Full Name
        if (fullname.value.trim().length < 3) {

            fullnameError.textContent =
                "Full name must contain at least 3 characters.";

            valid = false;

        }


        // Email
        const emailPattern =
            /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        if (!emailPattern.test(email.value.trim())) {

            emailError.textContent =
                "Please enter a valid email address.";

            valid = false;

        }


        // Password
        if (password.value.length < 6) {

            passwordError.textContent =
                "Password must contain at least 6 characters.";

            valid = false;

        }


        // Role
        if (role.value === "") {

            roleError.textContent =
                "Please select an account type.";

            valid = false;

        }


        // Team Member → Admin Email
        if (role.value === "Team Member") {

            if (!emailPattern.test(adminEmail.value.trim())) {

                adminEmailError.textContent =
                    "Please enter a valid Admin email.";

                valid = false;

            }

        }


        if (!valid) {
            return;
        }


        const message =
            document.getElementById("message");

        message.textContent =
            "Creating account...";

        message.style.color = "green";


        fetch("/register", {

            method: "POST",

            body: new FormData(form)

        })
        .then(response => response.text())
        .then(data => {

            if (data.includes("Email already exists")) {

                emailError.textContent =
                    "This email is already registered.";

                message.textContent = "";

            }

            else if (data.includes("Admin email not found")) {

                adminEmailError.textContent =
                    "Admin email not found.";

                message.textContent = "";

            }

            else if (data.includes("Registration Successful")) {

                message.textContent =
                    "Registration Successful!";

                form.reset();

                adminEmailGroup.style.display =
                    "none";

                adminEmail.required = false;


                setTimeout(function () {

                    window.location.href =
                        "/login?registered=success";

                }, 1500);

            }

            else {

                message.textContent =
                    data || "Registration failed.";

                message.style.color = "red";

            }

        })
        .catch(error => {

            console.error(
                "Register Error:",
                error
            );

            message.textContent =
                "Registration failed. Please try again.";

            message.style.color = "red";

        });

    });

});