document.addEventListener("DOMContentLoaded", function () {

    const form = document.querySelector("form");

    const message = document.createElement("div");
    message.id = "message";

    form.appendChild(message);

    form.addEventListener("submit", function (event) {

        event.preventDefault();

        const formData = new FormData(form);

        message.textContent = "Creating event...";
        message.style.color = "#d9a441";

        fetch("/create-event", {
            method: "POST",
            body: formData
        })
        .then(async response => {

            const text = await response.text();

            console.log("Server Response:", text);

            try {
                return JSON.parse(text);
            } catch (error) {
                throw new Error(text);
            }

        })
        .then(data => {

            if (data.success) {

                message.textContent = "✓ " + data.message;
                message.style.color = "green";

                form.reset();

            } else {

                message.textContent =
                    "❌ " + (data.error || "Event creation failed.");

                message.style.color = "red";
            }

        })
        .catch(error => {

            console.error("Create Event Error:", error);

            message.textContent =
                "❌ " + error.message;

            message.style.color = "red";
        });

    });

});