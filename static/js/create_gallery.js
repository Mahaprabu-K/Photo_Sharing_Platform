let eventData = [];


document.addEventListener("DOMContentLoaded", function () {

    loadEvents();

    document
        .getElementById("createGalleryButton")
        .addEventListener("click", createGallery);

    document
        .getElementById("copyLinkButton")
        .addEventListener("click", copyGalleryLink);

    document
        .getElementById("publishGalleryButton")
        .addEventListener("click", publishGallery);
});


/* =========================
   Load Events
========================= */

function loadEvents() {

    fetch("/api/gallery-events")
        .then(response => response.json())
        .then(events => {

            const select =
                document.getElementById("eventSelect");

            select.innerHTML =
                '<option value="">Select Event</option>';

            if (!Array.isArray(events)) {

                select.innerHTML =
                    '<option value="">No events available</option>';

                return;
            }

            eventData = events;

            events.forEach(event => {

                const option =
                    document.createElement("option");

                option.value =
                    event.event_id;

                option.textContent =
                    event.event_name;

                select.appendChild(option);
            });

        })
        .catch(error => {

            console.error("Event Error:", error);

            document.getElementById("eventSelect").innerHTML =
                '<option value="">Error loading events</option>';
        });
}


/* =========================
   Create Gallery
========================= */

function createGallery() {

    const eventId =
        document.getElementById("eventSelect").value;

    const pin =
        document.getElementById("pinInput").value.trim();

    const message =
        document.getElementById("message");


    /* Validation */

    if (!eventId) {

        message.textContent =
            "Please select an event.";

        return;
    }


    if (!pin) {

        message.textContent =
            "Please enter a gallery PIN.";

        return;
    }


    message.textContent =
        "Creating gallery...";


    /* Find Event */

    const selectedEvent =
        eventData.find(
            event =>
                event.event_id == parseInt(eventId)
        );


    /* API Request */

    fetch("/api/create-gallery", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({

            event_id: parseInt(eventId),

            pin: pin

        })
    })
    .then(response => response.json())
    .then(data => {

        console.log(
            "CREATE GALLERY RESPONSE:",
            data
        );


        /* Error */

        if (data.error) {

            message.textContent =
                data.error;

            return;
        }


        message.textContent =
            data.message ||
            "Gallery created successfully!";


        /* =========================
           Show Operational State
        ========================= */

        document
            .getElementById("operationalState")
            .style.display = "block";


        /* Event Name */

        document
            .getElementById("stateEventName")
            .textContent =
                selectedEvent
                    ? selectedEvent.event_name
                    : "-";


        /* Total Uploaded Photos */

        document
            .getElementById("totalPhotos")
            .textContent =
                selectedEvent
                    ? selectedEvent.total_photos
                    : "0";


        /* Selected Photos */

        document
            .getElementById("selectedPhotos")
            .textContent =
                selectedEvent
                    ? selectedEvent.selected_photos
                    : "0";


        /* Gallery ID */

        document
            .getElementById("galleryId")
            .textContent =
                data.gallery_id;


        /* Access PIN */

       document.getElementById("accessPin").textContent =
    data.existing_gallery
        ? data.gallery_pin
        : pin;


        /* Gallery Link */

        const galleryLink =
            window.location.origin +
            "/gallery/" +
            data.gallery_token;


        document
            .getElementById("galleryLink")
            .value =
                galleryLink;


        /* Store Gallery ID */

        document
            .getElementById("publishGalleryButton")
            .dataset.galleryId =
                data.gallery_id;


        /* =========================
           Gallery Status
        ========================= */

        const status =
            document.getElementById("galleryStatus");


        const publishButton =
            document.getElementById(
                "publishGalleryButton"
            );


        /* Already Published */

        if (data.existing_gallery) {

            status.textContent =
                "Published";

            status.classList.add(
                "published"
            );


            publishButton.textContent =
                "Gallery Published";

            publishButton.disabled =
                true;

        }

        /* New Gallery */

        else {

            status.textContent =
                "Not Published";

            status.classList.remove(
                "published"
            );


            publishButton.textContent =
                "Publish Gallery";

            publishButton.disabled =
                false;
        }

    })
    .catch(error => {

        console.error(
            "Gallery Error:",
            error
        );

        message.textContent =
            "Failed to create gallery.";
    });
}


/* =========================
   Copy Gallery Link
========================= */

function copyGalleryLink() {

    const link =
        document.getElementById(
            "galleryLink"
        );


    navigator.clipboard
        .writeText(link.value)

        .then(() => {

            alert(
                "Gallery link copied!"
            );

        })

        .catch(error => {

            console.error(
                "Copy Error:",
                error
            );

            alert(
                "Failed to copy link."
            );
        });
}


/* =========================
   Publish Gallery
========================= */

function publishGallery() {

    const publishButton =
        document.getElementById(
            "publishGalleryButton"
        );


    const galleryId =
        publishButton.dataset.galleryId;


    const message =
        document.getElementById(
            "message"
        );


    /* Validation */

    if (!galleryId) {

        alert(
            "Gallery ID not found."
        );

        return;
    }


    /* API Request */

    fetch("/api/publish-gallery", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({

            gallery_id:
                parseInt(galleryId)

        })
    })
    .then(response => response.json())
    .then(data => {

        console.log(
            "PUBLISH GALLERY RESPONSE:",
            data
        );


        /* Error */

        if (data.error) {

            message.textContent =
                data.error;

            return;
        }


        /* Success Message */

        message.textContent =
            data.message ||
            "Gallery published successfully!";


        /* =========================
           Update Status
        ========================= */

        const status =
            document.getElementById(
                "galleryStatus"
            );


        status.textContent =
            "Published";


        status.classList.add(
            "published"
        );


        /* =========================
           Update Button
        ========================= */

        publishButton.textContent =
            "Gallery Published";


        publishButton.disabled =
            true;


        alert(
            data.message ||
            "Gallery published successfully!"
        );

    })
    .catch(error => {

        console.error(
            "Publish Error:",
            error
        );

        message.textContent =
            "Failed to publish gallery.";
    });
}