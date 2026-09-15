document.addEventListener("DOMContentLoaded", function () {

    loadEvents();
    loadTeamMembers();

});




function loadTeamMembers() {

    fetch("/api/team-members")
        .then(response => response.json())
        .then(members => {

            console.log("Team Members:", members);

            const select = document.getElementById("memberSelect");

            select.innerHTML = '<option value="">Select Team Member</option>';

            members.forEach(member => {

                const option = document.createElement("option");

                option.value = member.user_id;
                option.textContent =
                    member.fullname + " - " + member.email;

                select.appendChild(option);
            });

        })
        .catch(error => {

            console.error("Team Member Error:", error);

            document.getElementById("memberSelect").innerHTML =
                '<option value="">Error Loading Team Members</option>';
        });
}

function loadEvents() {

    fetch("/api/events")
        .then(response => response.json())
        .then(events => {

            console.log("Events:", events);

            const select = document.getElementById("eventSelect");

            select.innerHTML = '<option value="">Select Event</option>';

            events.forEach(event => {

                const option = document.createElement("option");

                option.value = event.event_id;
                option.textContent = event.event_name;

                select.appendChild(option);
            });

        })
        .catch(error => {
            console.error("Event Error:", error);
        });
}

loadEvents();
loadTeamMembers();






document.getElementById("assignButton").addEventListener("click", function () {

    const eventId = document.getElementById("eventSelect").value;
    const userId = document.getElementById("memberSelect").value;
    const message = document.getElementById("message");

    if (!eventId || !userId) {
        message.textContent = "Please select Event and Team Member";
        return;
    }

    fetch("/api/assign-member", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            event_id: eventId,
            user_id: userId
        })
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
        console.error("Assign Error:", error);
        message.textContent = "Something went wrong";
    });

});