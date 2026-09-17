
document.addEventListener("DOMContentLoaded", function () {

    const pathParts = window.location.pathname.split("/");
    const galleryToken = pathParts[pathParts.length - 1];

    document.getElementById("viewGalleryButton").addEventListener("click", function () {

        const pin = document.getElementById("galleryPin").value;
        const message = document.getElementById("message");

        if (!pin) {
            message.textContent = "Please enter PIN.";
            return;
        }

        fetch("/api/verify-gallery-pin", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                gallery_token: galleryToken,
                pin: pin
            })
        })
        .then(response => response.json())
        .then(data => {

            if (data.message) {

                message.textContent = data.message;

                console.log("Gallery ID:", data.gallery_id);

                loadGalleryPhotos(data.gallery_id);

            } else {

                message.textContent = data.error;

            }

        })
        .catch(error => {

            console.error("PIN Error:", error);

            message.textContent = "Something went wrong.";

        });

    });

});


function loadGalleryPhotos(galleryId) {

    const photoList = document.getElementById("photoList");

    photoList.innerHTML = "<p>Loading photos...</p>";

    fetch("/api/customer-gallery/" + galleryId)
        .then(response => response.json())
        .then(photos => {

            console.log("Customer Photos:", photos);

            photoList.innerHTML = "";

            if (!Array.isArray(photos) || photos.length === 0) {

                photoList.innerHTML =
                    "<p>No photos available in this gallery.</p>";

                return;
            }

            photos.forEach(photo => {

                const photoCard = document.createElement("div");

                photoCard.className = "photo-card";

                photoCard.innerHTML = `
                    <img
                        src="${photo.storage_location}"
                        alt="${photo.filename}"
                        class="gallery-photo"
                    >

                    <p>
                        <strong>${photo.filename}</strong>
                    </p>
                    <button class="download-btn">
    ⬇ Download
</button>
                `;

                // Click photo → open large view
                const image = photoCard.querySelector(".gallery-photo");

                image.addEventListener("click", function () {
                    openPhotoViewer(photo.storage_location, photo.filename);
                });

                photoList.appendChild(photoCard);

            });

        })
        .catch(error => {

            console.error("Gallery Photos Error:", error);

            photoList.innerHTML =
                "<p>Error loading gallery photos.</p>";

        });
}


/* ============================= */
/* PHOTO VIEWER */
/* ============================= */

function openPhotoViewer(imageUrl, filename) {

    const viewer = document.createElement("div");

    viewer.className = "photo-viewer";

    viewer.innerHTML = `
        <div class="viewer-content">

            <button class="close-viewer">
                ✕
            </button>

            <img
                src="${imageUrl}"
                alt="${filename}"
            >

            <p>
                ${filename}
            </p>

        </div>
    `;

    document.body.appendChild(viewer);


    // Close button
    viewer.querySelector(".close-viewer").addEventListener("click", function () {
        viewer.remove();
    });


    // Click outside image → close
    viewer.addEventListener("click", function (event) {

        if (event.target === viewer) {
            viewer.remove();
        }

    });


    // ESC key → close
    document.addEventListener("keydown", function closeWithEscape(event) {

        if (event.key === "Escape") {

            viewer.remove();

            document.removeEventListener(
                "keydown",
                closeWithEscape
            );
        }

    });

}


const downloadButton =
    photoCard.querySelector(".download-btn");

downloadButton.addEventListener("click", function (event) {

    event.stopPropagation();

    window.location.href =
        "/api/download-photo/" + photo.photo_id;

});