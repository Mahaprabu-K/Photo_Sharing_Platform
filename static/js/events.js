document.addEventListener("DOMContentLoaded", function () {

    loadEvents();

});


function loadEvents() {

    const eventList = document.getElementById("eventList");

    fetch("/api/events")
        .then(response => {
            if (!response.ok) {
                throw new Error("Failed to load events");
            }

            return response.json();
        })
        .then(events => {

            eventList.innerHTML = "";

            if (events.length === 0) {

                eventList.innerHTML =
                    "<p>No events found.</p>";

                return;
            }

            events.forEach(event => {

                const eventCard = document.createElement("div");

                eventCard.className = "event-card";

                eventCard.innerHTML = `
                    
                    <h2>${event.event_name}</h2>

                    <p>
                        ${event.description || "No description"}
                    </p>

                    <p>
                        <strong>Created:</strong>
                        ${event.created_at}
                    </p>

                    <button
                        class="delete-btn"
                        onclick="deleteEvent(${event.event_id})">
                        🗑 Delete Event
                    </button>

                `;

                eventList.appendChild(eventCard);

            });

        })
        .catch(error => {

            console.error(error);

            eventList.innerHTML =
                "<p>Unable to load events.</p>";

        });

}


function deleteEvent(eventId) {

    const confirmDelete = confirm(
        "Are you sure you want to delete this event?"
    );

    if (!confirmDelete) {
        return;
    }

    fetch("/api/delete-event", {

        method: "DELETE",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            event_id: eventId
        })

    })
    .then(response => response.json())

    .then(data => {

        if (data.error) {

            alert(data.error);

            return;
        }

        alert(
            data.message || "Event deleted successfully!"
        );

        loadEvents();

    })

    .catch(error => {

        console.error("Delete Event Error:", error);

        alert("Failed to delete event.");

    });

}