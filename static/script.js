document.addEventListener('DOMContentLoaded', () => { // Ensure DOM is loaded
    const uploadForm = document.getElementById("upload-form");
    const textInput = document.getElementById("text-input");
    const fileInput = document.getElementById("files");
    const resultBox = document.getElementById("result-box");
    const downloadBtn = document.getElementById("download-btn");
    const submitBtn = document.getElementById("submit-btn");
    const textInputGroup = textInput.closest('.input-option-group');
    const fileInputGroup = fileInput.closest('.input-option-group');
  
    // Function to update button and input states
    function updateState() {
      const hasText = textInput.value.trim().length > 0;
      const hasFiles = fileInput.files.length > 0;
  
      // Enable submit only if exactly one input method has data
      submitBtn.disabled = !(hasText ^ hasFiles); // XOR: true if one is true, but not both
  
      // Disable the inactive input group visually
      textInputGroup.classList.toggle('disabled', hasFiles);
      textInput.disabled = hasFiles; // Also set disabled attribute for form submission
  
      fileInputGroup.classList.toggle('disabled', hasText);
      fileInput.disabled = hasText; // Also set disabled attribute
  
      // Enable download button only if there's result text
      downloadBtn.disabled = resultBox.value.trim().length === 0;
    }
  
    // Event listeners for inputs
    textInput.addEventListener("input", () => {
        if (textInput.value.trim().length > 0) {
            fileInput.value = ''; // Clear file input if text is entered
            // Manually trigger change event for file input if needed by other listeners (optional)
            // fileInput.dispatchEvent(new Event('change'));
        }
        updateState();
    });
  
    fileInput.addEventListener("change", () => {
        if (fileInput.files.length > 0) {
            textInput.value = ''; // Clear text input if files are selected
             // Manually trigger input event for text input if needed (optional)
            // textInput.dispatchEvent(new Event('input'));
        }
        updateState();
    });
  
    // Form submission logic
    uploadForm.addEventListener("submit", async function (e) {
      e.preventDefault();
      submitBtn.disabled = true; // Disable submit during processing
      submitBtn.textContent = 'Processing...'; // Provide feedback
      resultBox.value = 'Processing request...'; // Placeholder during fetch
      downloadBtn.disabled = true;
  
  
      // FormData will only include non-disabled inputs
      const formData = new FormData(this);
  
      try {
          const response = await fetch("/upload", {
              method: "POST",
              body: formData,
          });
  
          if (!response.ok) {
               throw new Error(`HTTP error! status: ${response.status}`);
          }
  
          const data = await response.json();
          resultBox.value = data.result || "No result returned from server.";
  
      } catch (error) {
          console.error("Error during upload:", error);
          resultBox.value = `Error: ${error.message}\nCould not process the request. Please check the console.`;
      } finally {
         // Re-enable submit button and reset text after processing
         submitBtn.disabled = false; // Re-enable generally, updateState will refine
         submitBtn.textContent = 'Process Input';
         updateState(); // Re-evaluate button/input states based on current values and result
      }
    });
  
    // Download button logic (remains the same, but initial state and updateState handle enabling)
    downloadBtn.addEventListener("click", function () {
      if (resultBox.value.trim().length === 0) return; // Prevent downloading empty file
  
      const text = resultBox.value;
      const blob = new Blob([text], { type: "text/x-python" }); // Keep as python type for now
      const url = URL.createObjectURL(blob);
  
      const link = document.createElement("a");
      link.href = url;
      link.download = "result.py"; // Keep default name, could be dynamic later
      document.body.appendChild(link); // Required for Firefox
      link.click();
      document.body.removeChild(link); // Clean up
  
      URL.revokeObjectURL(url);
    });
  
    // Initial state check
    updateState();
  });