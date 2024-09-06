from flask import Flask, request, jsonify
from pymongo import MongoClient
from flask_cors import CORS  # Import Flask-CORS
from bson import ObjectId  # To work with MongoDB ObjectIds

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
    # Fetch the first worker from the 'worker.info' collection
    worker = workers_collection.find_one()
    
    if worker:
        # Convert MongoDB ObjectId to string and return the worker info as JSON
        worker['_id'] = str(worker['_id'])
        return jsonify(worker), 200
    else:
        return jsonify({"message": "No workers found in the database"}), 404
    
@app.route('/worker/<username>', methods=['GET'])
def get_worker_info(username):
    # Find the worker by username
    worker = workers_collection.find_one({"username": username})

    if worker:
        # Convert MongoDB ObjectId to string and return the worker info as JSON
        worker['_id'] = str(worker['_id'])
        return jsonify(worker), 200
    else:
        return jsonify({"message": "Worker not found"}), 404

# Route to get the current count from the emergency collection
@app.route('/emergency', methods=['GET'])
def get_emergency_count():
    emergency_doc = emergency_collection.find_one()  # Retrieve the first document
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
        machine['_id'] = str(machine['_id'])  # Convert ObjectId to string for JSON serialization
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
        medical_info['_id'] = str(medical_info['_id'])  # Convert ObjectId to string for JSON serialization
        return jsonify(medical_info), 200
    else:
        return jsonify({"message": "No medical info found"}), 404

# Route to update medical info for a worker
@app.route('/medical/<username>', methods=['PUT'])
def update_medical_info(username):
    updated_data = request.get_json()  # Get the updated medical info from the request body
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
    data = request.get_json()  # Get feedback data from the request body
    feedback = {
        "name": data.get("name"),
        "phn_no": data.get("phn_no"),
        "Q1": data.get("Q1"),
        "Q2": data.get("Q2"),
        "Q3": data.get("Q3"),
        "Q4": data.get("Q4")
    }

    # Insert feedback into the feedback collection
    feedback_collection.insert_one(feedback)
    return jsonify({"message": "Feedback submitted successfully"}), 200

if __name__ == '__main__':
    app.run(debug=True)
