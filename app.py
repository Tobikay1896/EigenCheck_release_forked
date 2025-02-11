from flask import Flask, request, jsonify, send_from_directory, render_template
import os
import subprocess
from werkzeug.utils import secure_filename
from flask_cors import CORS

app = Flask(__name__, template_folder="../frontend", static_folder="../static")
CORS(app, supports_credentials=True, origins="*")

UPLOAD_FOLDER = "uploads"
USER_DB = "users.json"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def load_users():
    users = {}
    USER_DB_PATH = os.path.join(os.path.dirname(__file__), USER_DB) #Add user_db relative path.
    if not os.path.exists(USER_DB_PATH):
        print("users.json not found, creating it now...")
        users = {"users": {"admin": "password123"}}  # Default user
        with open(USER_DB, "w") as f:
            json.dump(users, f, indent=4)
        print("Test users created:", users)
        return users["users"]

    try:
        with open(USER_DB, "r") as f:
            users = json.load(f)
            return users["users"]
    except (json.JSONDecodeError, KeyError):
        print("users.json was corrupted. Resetting it...")
        users = {"users": {"admin": "password123"}}  # Reset if corrupt
        with open(USER_DB, "w") as f:
            json.dump(users, f, indent=4)
        return users["users"]

users = load_users()
print("users.json successfully loaded! Current Users:", users)


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    users = load_users()

    if not data or "username" not in data or "password" not in data:
        return jsonify({"message": "Fehlende Anmeldedaten", "status": "error"}), 400

    if data["username"] in users and users[data["username"]] == data["password"]:
        session["logged_in"] = True
        session["username"] = data["username"]
        session.permanent = True
        return jsonify({"message": "Login erfolgreich", "status": "success", "username": data["username"]})
    else:
        return jsonify({"message": "Falscher Benutzername oder Passwort", "status": "error"}), 401

@app.route("/upload", methods=["POST"])
def upload_file():
    if "logged_in" not in session or not session["logged_in"]:
        return jsonify({"error": "Nicht eingeloggt"}), 401

    if "file" not in request.files:
        return jsonify({"error": "Keine Datei hochgeladen"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Keine Datei ausgewählt"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    return jsonify({"message": f"Datei {filename} erfolgreich hochgeladen"}), 200

@app.route("/run", methods=["POST"])
def run_c_program():
    if "logged_in" not in session or not session["logged_in"]:
        return jsonify({"error": "Nicht eingeloggt"}), 401

    if "file" not in request.files:
        return jsonify({"error": "Keine Datei hochgeladen"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Keine Datei ausgewählt"}), 400

    filename = secure_filename(file.filename)
    if not filename.endswith(".c"):
        return jsonify({"error": "Nur C-Dateien erlaubt!"}), 400

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)

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

# Route, die die JavaScript Datei bereitstellt
@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory("../static", filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)