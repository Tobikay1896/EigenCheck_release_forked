from flask import Flask, request, jsonify, send_from_directory, render_template
import os
import subprocess
from werkzeug.utils import secure_filename
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app, supports_credentials=True)  # Allow frontend requests

# Configuration
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Ensure necessary directories exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# ========================== SERVE FRONTEND ==========================

@app.route("/")
def index():
    """Serve the main frontend page."""
    return render_template("index.html")


# ========================== FILE UPLOAD & RETRIEVAL ==========================

@app.route("/upload", methods=["POST"])
def upload_file():
    """Handle file uploads."""
    if "file" not in request.files:
        return jsonify({"error": "Keine Datei hochgeladen"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Keine Datei ausgewählt"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    print(f"✅ Datei gespeichert: {filepath}")
    return jsonify({"message": f"Datei {filename} erfolgreich hochgeladen"}), 200


@app.route("/files/<filename>", methods=["GET"])
def get_file(filename):
    """Allow users to download files."""
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# ========================== COMPILATION & EXECUTION ==========================

@app.route("/run", methods=["POST"])
def run_c_program():
    """Compile and execute an uploaded C program."""
    if "file" not in request.files:
        return jsonify({"error": "Keine Datei hochgeladen"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Keine Datei ausgewählt"}), 400

    filename = secure_filename(file.filename)
    if not filename.endswith(".c"):
        return jsonify({"error": "Nur C-Dateien erlaubt!"}), 400

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    executable = filepath.replace(".c", "")
    compile_cmd = ["gcc", filepath, "-o", executable]
    run_cmd = [executable]

    try:
        # Compile the C program
        compile_result = subprocess.run(compile_cmd, capture_output=True, text=True)
        if compile_result.returncode != 0:
            return jsonify({"error": "Kompilierungsfehler", "details": compile_result.stderr})

        # Run the compiled executable
        run_result = subprocess.run(run_cmd, capture_output=True, text=True)
        return jsonify({"message": "Programm erfolgreich ausgeführt", "output": run_result.stdout})

    except Exception as e:
        return jsonify({"error": str(e)})


# ========================== SERVER START ==========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)  # Allow public access