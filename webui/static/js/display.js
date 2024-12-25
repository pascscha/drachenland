// Get the form and image container elements
const form = document.getElementById("sliderForm");
const imageContainer = document.getElementById("imageContainer");
const displayedImage = document.getElementById("displayedImage");
const imageName = document.getElementById("imageName");

// Get all slider input elements
const sliders = document.querySelectorAll("input[type='range']");
const checkboxes = document.querySelectorAll("input[type='checkbox']");

// Function to handle slider change event
function handleSliderChange() {
    // Get form data
    const formData = new FormData(form);

    for (const pair of formData.entries()) {
        const [name, value] = pair;
    }

    if(!isPlaying){
        // Send AJAX request
        fetch("/marionette/set", {
            method: "POST",
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                // Update the displayed image source
                displayedImage.src = data.image_path;
                imageName.innerHTML = data.image_path;

                // Show the image container
                imageContainer.style.display = "block";
            })
            .catch(error => {
                console.error("Error:", error);
            });
    }
}

// Attach event listener to each slider input element
sliders.forEach(slider => {
    slider.addEventListener("input", handleSliderChange);
});

checkboxes.forEach(checkbox => {
    checkbox.addEventListener("input", handleSliderChange);
});


handleSliderChange()
