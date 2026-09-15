console.log("TEAM DASHBOARD JS LOADED");

document.addEventListener("DOMContentLoaded", function () {

    loadUser();
    loadMyEvents();

});


function loadUser() {

    fetch("/api/user")

        .then(response => response.json())

        .then(data => {

            if (data.error) {

                console.error(data.error);
                return;

            }

            document.getElementById("userName").textContent =
                data.fullname;

            document.getElementById("userRole").textContent =
                data.role;

        })

        .catch(error => {

            console.error("User Error:", error);

        });

}


function loadMyEvents() {

    fetch("/api/my-events")

        .then(response => {

            console.log("API Status:", response.status);

            return response.json();

        })

        .then(events => {

            console.log("My Events:", events);

            const eventList =
                document.getElementById("eventList");

            eventList.innerHTML = "";


            if (!Array.isArray(events) || events.length === 0) {

                eventList.innerHTML = `
                    <div class="loading-card">
                        <p>No events assigned yet.</p>
                    </div>
                `;

                return;

            }


            events.forEach(event => {

                const eventCard =
                    document.createElement("div");

                eventCard.className = "event-card";


                eventCard.innerHTML = `

                    <div class="event-icon">
                        📅
                    </div>

                    <h3>
                        ${event.event_name}
                    </h3>

                    <p>
                        ${event.description || "No description available"}
                    </p>

                    <p>
                        <strong>Event ID:</strong>
                        ${event.event_id}
                    </p>

                    <button
                        class="upload-btn"
                        onclick="openUploadPage(${event.event_id})"
                    >
                        📤 Upload Photos
                    </button>

                `;


                eventList.appendChild(eventCard);

            });

        })

        .catch(error => {

            console.error("Event Error:", error);

            document.getElementById("eventList").innerHTML = `

                <div class="loading-card">

                    <p>
                        Error loading events.
                    </p>

                </div>

            `;

        });

}


function openUploadPage(eventId) {

    window.location.href =
        "/upload-photos?event_id=" + eventId;

}