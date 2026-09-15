document.addEventListener("DOMContentLoaded", function () {

    loadEvents();

    document.getElementById("viewButton").addEventListener("click", function () {

        const eventId =
            document.getElementById("eventSelect").value;

        if (!eventId) {

            document.getElementById("photoList").innerHTML =
                `<div class="empty-state">
                    <p>Please select an event.</p>
                </div>`;

            return;
        }

        loadPhotos(eventId);
    });

});


function loadEvents() {

    fetch("/api/events")

        .then(response => response.json())

        .then(events => {

            const select =
                document.getElementById("eventSelect");

            select.innerHTML =
                '<option value="">Select Event</option>';

            if (!Array.isArray(events)) {

                select.innerHTML =
                    '<option value="">Error loading events</option>';

                return;
            }

            events.forEach(event => {

                const option =
                    document.createElement("option");

                option.value = event.event_id;

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


function loadPhotos(eventId) {

    const photoList =
        document.getElementById("photoList");

    photoList.innerHTML = `
        <div class="empty-state">
            <p>Loading photos...</p>
        </div>
    `;


    fetch("/api/event-photos/" + eventId)

        .then(response => response.json())

        .then(photos => {

            photoList.innerHTML = "";

            if (!Array.isArray(photos) || photos.length === 0) {

                photoList.innerHTML = `
                    <div class="empty-state">
                        <p>No photos uploaded for this event.</p>
                    </div>
                `;

                return;
            }


            photos.forEach(photo => {

                const photoCard =
                    document.createElement("div");

                photoCard.className =
                    "photo-card";


                photoCard.innerHTML = `

                    <img
                        src="${photo.storage_location}"
                        alt="${photo.filename}"
                    >

                    <div class="photo-info">

                        <p>
                            <strong>File:</strong>
                            ${photo.filename}
                        </p>

                        <p>
                            <strong>Uploaded By:</strong>
                            ${photo.uploaded_by}
                        </p>

                        <p>
                            <strong>File Size:</strong>
                            ${photo.file_size} bytes
                        </p>

                    </div>


                    <div class="photo-select">

                        <label>

                            <input
                                type="checkbox"
                                class="photo-checkbox"
                                value="${photo.photo_id}"
                                ${photo.is_selected ? "checked" : ""}
                            >

                            Select Photo

                        </label>

                    </div>

                `;


                photoList.appendChild(photoCard);

            });

        })

        .catch(error => {

            console.error("Photo Error:", error);

            photoList.innerHTML = `
                <div class="empty-state">
                    <p>Error loading photos.</p>
                </div>
            `;

        });

}


document
    .getElementById("saveSelectionButton")
    .addEventListener("click", function () {


        const eventId =
            document.getElementById("eventSelect").value;


        if (!eventId) {

            alert("Please select an event.");

            return;
        }


        const checkboxes =
            document.querySelectorAll(
                ".photo-checkbox:checked"
            );


        const selectedPhotoIds = [];


        checkboxes.forEach(function (checkbox) {

            selectedPhotoIds.push(
                parseInt(checkbox.value)
            );

        });


        // No photo selected
        if (selectedPhotoIds.length === 0) {

            alert("Please select at least one photo.");

            return;
        }


        fetch("/api/select-photos", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({

                event_id: eventId,

                selected_photo_ids:
                    selectedPhotoIds

            })

        })

        .then(response => response.json())

        .then(data => {

            if (data.message) {

                alert(data.message);

            } else {

                alert(
                    data.error ||
                    "Failed to save photo selection."
                );

            }

        })

        .catch(error => {

            console.error(
                "Selection Error:",
                error
            );

            alert(
                "Failed to save photo selection."
            );

        });

    });