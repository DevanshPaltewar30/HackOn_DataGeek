// Fade-in animation on page load
document.addEventListener("DOMContentLoaded", function () {
    document.body.classList.add("loaded");

    // Load dark mode state from local storage
    if (localStorage.getItem("dark-mode") === "enabled") {
        document.body.classList.add("dark-mode");
        darkModeBtn.classList.add("active");
        darkModeBtn.innerHTML = "☀️";
    }
});

// Dark Mode Toggle
const darkModeBtn = document.getElementById('dark-mode-btn');

darkModeBtn.addEventListener('click', function() {
    document.body.classList.toggle('dark-mode');
    this.classList.toggle('active');

    if (document.body.classList.contains('dark-mode')) {
        localStorage.setItem("dark-mode", "enabled");
        darkModeBtn.innerHTML = "☀️";
    } else {
        localStorage.setItem("dark-mode", "disabled");
        darkModeBtn.innerHTML = "🌙";
    }
});

// File Upload Button
document.getElementById('upload-btn').addEventListener('click', function() {
    document.getElementById('fileInput').click();
});

// Show selected file name
document.getElementById('fileInput').addEventListener('change', function() {
    let file = this.files[0];

    if (file) {
        document.getElementById('file-name').textContent = file.name;
        uploadFile(file);
    } else {
        document.getElementById('file-name').textContent = "No file selected";
    }
});

// Drag & Drop Upload
const dropArea = document.getElementById('drop-area');

// Prevent default behaviors
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

// Highlight drop area on drag over
['dragenter', 'dragover'].forEach(eventName => {
    dropArea.addEventListener(eventName, () => dropArea.classList.add('drag-over'), false);
});

// Remove highlight on drag leave
['dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, () => dropArea.classList.remove('drag-over'), false);
});

// Handle dropped files
dropArea.addEventListener('drop', function(e) {
    let files = e.dataTransfer.files;
    if (files.length > 0) {
        document.getElementById('file-name').textContent = files[0].name;
        uploadFile(files[0]);
    }
});

// Upload file to Flask backend
function uploadFile(file) {
    let formData = new FormData();
    formData.append("file", file);

    fetch("/upload", {
        method: "POST",
        body: formData
    })
    .then(response => response.text())
    .then(data => {
        alert(data); // Show success message
    })
    .catch(error => {
        console.error("Error uploading file:", error);
        alert("File upload failed.");
    });
}

// Function to download the processed ZIP file
document.getElementById('download-btn')?.addEventListener('click', function() {
    window.location.href = "/download";
});
