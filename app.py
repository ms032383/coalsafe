from flask import Flask, request, jsonify
from pymongo import MongoClient
from flask_cors import CORS
from bson import ObjectId
from datetime import datetime
from werkzeug.utils import secure_filename  # Correct import for securing filenames
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# MongoDB connection using the provided connection string
client = MongoClient("mongodb+srv://rachitchauhanjsp78:RxPSxegBzp7xZZIF@coalmine.lc54i.mongodb.net/coalmine?retryWrites=true&w=majority")
db = client['coalmine']  # Accessing the 'coalmine' database
workers_collection = db['worker.info']  # Accessing the 'worker.info' collection
emergency_collection = db['emergency']  # Accessing the 'emergency' collection
machines_collection = db['Machine_info']  # Accessing the 'Machine_info' collection
medical_collection = db['medical.info']  # Accessing the 'medical.info' collection
feedback_collection = db['feedback']
logs_collection = db['logs']
voice_notes_collection = db['voice_notes']  # Collection to store voice notes info

# Define the directory to save uploaded voice notes
UPLOAD_FOLDER = 'uploads/voice_notes'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Ensure the upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Allowed extensions for voice notes
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'm4a'}


# Route to handle login
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # Find the worker by username
    worker = workers_collection.find_one({"username": username})

    if worker:
        # Check if the password matches
        if password == worker['password']:  # In production, store hashed passwords
            return jsonify({
                "message": "Login successful",
                "name": worker['name'],
                "username": worker['username']
            }), 200
        else:
            return jsonify({"message": "Invalid password"}), 401
    else:
        return jsonify({"message": "Invalid username"}), 404

# Route to test MongoDB connection
@app.route('/test_mongo', methods=['GET'])
def test_mongo():
    worker = workers_collection.find_one()  # Fetch the first worker
    if worker:
        worker['_id'] = str(worker['_id'])  # Convert ObjectId to string
        return jsonify(worker), 200
    else:
        return jsonify({"message": "No workers found in the database"}), 404

@app.route('/worker/<username>', methods=['GET'])
def get_worker_info(username):
    worker = workers_collection.find_one({"username": username})
    if worker:
        worker['_id'] = str(worker['_id'])
        return jsonify(worker), 200
    else:
        return jsonify({"message": "Worker not found"}), 404

# Route to get the current count from the emergency collection
@app.route('/emergency', methods=['GET'])
def get_emergency_count():
    emergency_doc = emergency_collection.find_one()
    if emergency_doc:
        return jsonify({"count": emergency_doc['count']}), 200
    else:
        return jsonify({"message": "Emergency data not found"}), 404

# Route to increment the count in the emergency collection
@app.route('/emergency', methods=['PUT'])
def update_emergency_count():
    emergency_doc = emergency_collection.find_one()
    if emergency_doc:
        new_count = emergency_doc['count'] + 1
        emergency_collection.update_one(
            {"_id": emergency_doc["_id"]},
            {"$set": {"count": new_count}}
        )
        return jsonify({"count": new_count}), 200
    else:
        return jsonify({"message": "Emergency data not found"}), 404

# Route to get all machines from the Machine_info collection
@app.route('/machines', methods=['GET'])
def get_machines():
    machines = list(machines_collection.find())
    for machine in machines:
        machine['_id'] = str(machine['_id'])
    return jsonify(machines), 200

# Route to update the status of a machine in the Machine_info collection
@app.route('/machines/<machine_id>', methods=['PUT'])
def update_machine_status(machine_id):
    new_status = request.json.get('status')
    result = machines_collection.update_one(
        {"_id": ObjectId(machine_id)},
        {"$set": {"Machine.Status": new_status}}
    )
    if result.matched_count > 0:
        return jsonify({"message": "Status updated successfully"}), 200
    else:
        return jsonify({"message": "Machine not found"}), 404

# Route to get medical info for a worker
@app.route('/medical/<username>', methods=['GET'])
def get_medical_info(username):
    medical_info = medical_collection.find_one({"username": username})
    if medical_info:
        medical_info['_id'] = str(medical_info['_id'])
        return jsonify(medical_info), 200
    else:
        return jsonify({"message": "No medical info found"}), 404

# Route to update medical info for a worker
@app.route('/medical/<username>', methods=['PUT'])
def update_medical_info(username):
    updated_data = request.get_json()
    result = medical_collection.update_one(
        {"username": username},
        {"$set": updated_data}
    )
    if result.matched_count > 0:
        return jsonify({"message": "Medical info updated successfully"}), 200
    else:
        return jsonify({"message": "Medical info not found for user"}), 404

# Route to submit feedback
@app.route('/feedback', methods=['POST'])
def submit_feedback():
    data = request.get_json()
    feedback = {
        "name": data.get("name"),
        "phn_no": data.get("phn_no"),
        "Q1": data.get("Q1"),
        "Q2": data.get("Q2"),
        "Q3": data.get("Q3"),
        "Q4": data.get("Q4")
    }
    feedback_collection.insert_one(feedback)
    return jsonify({"message": "Feedback submitted successfully"}), 200

@app.route('/tasks/<username>', methods=['GET'])
def get_user_tasks(username):
    tasks = list(db['task'].find({"Username": username}))
    for task in tasks:
        task['_id'] = str(task['_id'])
    return jsonify(tasks), 200

@app.route('/notice', methods=['GET'])
def get_notice():
    notice = db['notice'].find_one()
    if notice:
        notice['_id'] = str(notice['_id'])
        return jsonify(notice), 200
    return jsonify({"message": "No notices available"}), 404

# Route to add log entry
@app.route('/add_log', methods=['POST'])
def add_log():
    data = request.get_json()
    username = data.get('username')
    date = datetime.utcnow().strftime('%Y-%m-%d')
    time = datetime.utcnow().strftime('%H:%M:%S')
    work = data.get('work', 'Logged in')

    sno = logs_collection.count_documents({}) + 1

    log_entry = {
        "sno": sno,
        "username": username,
        "date": date,
        "time": time,
        "work": work
    }

    logs_collection.insert_one(log_entry)
    return jsonify({"message": "Log added successfully"}), 200

# Route to update subtask status
@app.route('/update_subtask_status', methods=['PUT'])
def update_subtask_status():
    data = request.get_json()
    username = data.get('username')
    subtask = data.get('subtask')
    status = data.get('status')

    result = db['task'].update_one(
        {"Username": username},
        {"$set": {subtask: status}}
    )
    if result.modified_count > 0:
        return jsonify({"message": "Subtask status updated successfully"}), 200
    else:
        return jsonify({"message": "Failed to update subtask status"}), 404

# Check if the uploaded file is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route to upload voice notes
@app.route('/upload_voice_note', methods=['POST'])
def upload_voice_note():
    # Check if the POST request has the file part
    if 'audio' not in request.files:
        return jsonify({"message": "No audio file uploaded"}), 400

    file = request.files['audio']
    if file and allowed_file(file.filename):
        # Secure the filename and save it to the uploads folder
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Save voice note metadata to MongoDB
        voice_note_entry = {
            "username": request.form.get("username"),
            "timestamp": datetime.utcnow(),
            "filename": filename,
            "file_path": file_path  # Storing the file path
        }
        voice_notes_collection.insert_one(voice_note_entry)

        return jsonify({"message": "Voice note uploaded successfully", "filename": filename}), 200

    return jsonify({"message": "Invalid audio file type"}), 400


if __name__ == '__main__':
    app.run(debug=True)
