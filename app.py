from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
import os
from merge_files import merge_modules
from generate_data import generate_project, clear_directory

app = Flask(__name__)
CORS(app)

# Ensure static files are served correctly (if your structure is standard)
app.static_folder = 'static'

UPLOAD_FOLDER = "/Users/tianyiniu/Code/hack3datafiles/Test"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("upload.html")

@app.route("/upload", methods=["POST"])
def upload_files():
    print("entered upload files")
    # Check for text input first
    text_input = request.form.get("text_input") # Get text using the 'name' attribute from HTML

    if text_input:
        print(f"Received text input: {text_input[:50]}...") # Log received text (truncated)
        # TODO Return the received sentence back
        generate_project(text_input, target_dir=UPLOAD_FOLDER)
        merged_code = merge_modules(UPLOAD_FOLDER)
        return jsonify({"result": merged_code})

    # If no text input, check for files
    if 'files' not in request.files:
        print("No text input or files key found in request.")
        return jsonify({"result": "No input provided (neither text nor files key found)."})

    files = request.files.getlist("files")

    # Filter out empty file inputs (if the user selected files then switched to text)
    valid_files = [f for f in files if f and f.filename]

    if not valid_files:
         print("Files key present, but no actual files were uploaded or selected.")
         return jsonify({"result": "No input provided (no text or files selected)."})

    uploaded_filenames = []
    errors = []

    for file in valid_files:
        if file.filename.endswith(".py"):
            try:
                # Sanitize filename (optional but recommended)
                # from werkzeug.utils import secure_filename
                # filename = secure_filename(file.filename)
                filename = file.filename # Using original for simplicity now
                save_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(save_path)
                uploaded_filenames.append(filename)
            except Exception as e:
                errors.append(f"Could not save {file.filename}: {e}")
        elif file.filename: # Check if filename exists but is not .py
             errors.append(f"File skipped (not .py): {file.filename}")


    if uploaded_filenames:
        print(f"Uploaded {len(uploaded_filenames)} file(s): {', '.join(uploaded_filenames)}")
        if errors:
            print(f"Errors occurred: {'; '.join(errors)}")

        print("Pre merge!!")
        result = merge_modules(UPLOAD_FOLDER)
        print(result)

        if errors:
            result += f"\n\n# Errors during upload:\n# {'\n# '.join(errors)}"
        return jsonify({"result": result})
    else:
        # No valid .py files were uploaded
        print(f"No valid .py files uploaded. Errors/Skipped: {'; '.join(errors)}")
        error_message = "No valid Python (.py) files were uploaded."
        if errors:
            error_message += f" Details: {'; '.join(errors)}"
        return jsonify({"result": error_message})


if __name__ == "__main__":
    app.run(host="localhost", port="8000", debug=True)