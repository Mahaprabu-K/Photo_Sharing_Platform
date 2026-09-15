document.addEventListener("DOMContentLoaded", function () {

    fetch("/api/user")
        .then(response => response.json())
        .then(data => {
            console.log(data);

            document.getElementById("userName").textContent = "welcome," + data.fullname;
            document.getElementById("userRole").textContent = "Role:" + data.role;
        })
.catch(error => {
    console.error("Error:",error);
});
});