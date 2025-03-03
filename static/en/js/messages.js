document.addEventListener("DOMContentLoaded", function () {
    let flashContainer = document.getElementById("flash-message-container");
    if (flashContainer) {
        flashContainer.style.right = "20px"; // Slide in

        setTimeout(function () {
            flashContainer.style.right = "-300px"; // Slide out
        }, 3000);
    }
});
