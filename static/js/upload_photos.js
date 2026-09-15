document.addEventListener("DOMContentLoaded", function () {

    const params = new URLSearchParams(window.location.search);
    const eventId = params.get("event_id");

    console.log("Event ID:", eventId);

    if (!eventId) {
        document.getElementById("eventName").textContent =
            "Event not selected";
        return;
    }

    loadEvent(eventId);

});


function loadEvent(eventId) {

    fetch("/api/event/" + eventId)
        .then(response => response.json())
        .then(data => {

            if (data.error) {
                document.getElementById("eventName").textContent =
                    data.error;
                return;
            }

            document.getElementById("eventName").textContent =
                data.event_name;

        })
        .catch(error => {

            console.error("Event Error:", error);

            document.getElementById("eventName").textContent =
                "Error loading event";

        });
}



document.getElementById("uploadForm").addEventListener("submit", function (event) {
    event.preventDefault();

    const params = new URLSearchParams(window.location.search);
    const eventId = params.get("event_id");

    const files = document.getElementById("photoFiles").files;
    const message = document.getElementById("message");

    if (!eventId) {
        message.textContent = "Event ID is missing!";
        return;
    }

    if (files.length === 0) {
        message.textContent = "Please select photos!";
        return;
    }

    const formData = new FormData();

    formData.append("event_id", eventId);

    for (let i = 0; i < files.length; i++) {
        formData.append("photos", files[i]);
    }

    fetch("/api/upload-photos", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            message.textContent = data.message;
        } else {
            message.textContent = data.error;
        }
    })
    .catch(error => {
        console.error("Upload Error:", error);
        message.textContent = "Upload failed!";
    });
});