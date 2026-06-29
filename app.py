from flask import Flask, render_template, request, redirect, session, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
import bcrypt
import traceback
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import tensorflow as tf
import cv2
import numpy as np
from predict import predict
from rewards import get_badge
from firebase_admin import storage
import uuid


# =====================================

# FLASK SETUP

# =====================================
app = Flask(__name__)

app.secret_key = "civic_ai_secret_key"

CORS(app)

# =====================================

# FIREBASE SETUP

# =====================================

cred = credentials.Certificate(
"civical-admin.json"
)

firebase_admin.initialize_app(cred, {
    "storageBucket": "civical-565ff.firebasestorage.app"
})

bucket = storage.bucket()

db = firestore.client()

# =====================================

# HOME

# =====================================
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/register")
def register_page():
    return render_template("register.html")

# DASHBOARD

@app.route("/dashboard")
def dashboard():

    if "user_email" not in session:
        return redirect("/login")

    # =====================
    # USER DATA
    # =====================
    user_docs = list(
        db.collection("users")
        .where("email", "==", session["user_email"])
        .stream()
    )

    points = 0
    badge = "Beginner"

    if user_docs:
        user = user_docs[0].to_dict()
        points = user.get("points", 0)
        badge = user.get("badge", "Beginner")

    # =====================
    # COMPLAINT STATS
    # =====================
    docs = db.collection("complaints").stream()

    total = 0
    pending = 0
    resolved = 0

    for doc in docs:
        data = doc.to_dict()
        total += 1

        status = (data.get("status") or "").lower()

        if status == "resolved":
            resolved += 1
        else:
            pending += 1   # default bucket

    return render_template(
        "dashboard.html",
        name=session.get("user_name"),
        role=session.get("role"),
        total=total,
        pending=pending,
        resolved=resolved,
        points=points,
        badge=badge
    )
@app.route("/register-complaint")
def register_complaint():

    if "user_email" not in session:
        return redirect("/login")

    return render_template("register_complaint.html")

UPLOAD_FOLDER="static/uploads"

app.config["UPLOAD_FOLDER"]=UPLOAD_FOLDER

@app.route("/api/register-complaint", methods=["POST"])
def save_complaint():

    if "user_email" not in session:
        return redirect("/login")

    title = request.form.get("title")
    description = request.form.get("description")

    latitude = request.form.get("latitude")
    longitude = request.form.get("longitude")

    latitude = float(latitude) if latitude else None
    longitude = float(longitude) if longitude else None 

    image = request.files["image"]

    filename = secure_filename(image.filename)

    image_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )

    # Save temporarily for AI prediction
    temp_path = "temp.jpg"
    image.save(temp_path)

    # AI Prediction
    category, confidence = predict(temp_path)
    
    image.stream.seek(0)
    # Upload to Firebase Storage
    image_url = upload_to_firebase(image)

    # Save Complaint
    db.collection("complaints").add({

        "title": title,
        "description": description,

        "category": category,
        "ai_confidence": round(confidence * 100, 2),

    # ☁️ CLOUD IMAGE (IMPORTANT CHANGE)
    "image_url": image_url,

    "latitude": latitude,
    "longitude": longitude,

    "status": "Pending",
    "priority": "Normal",

    "user_email": session["user_email"],
    "user_name": session["user_name"],

    "created_at": datetime.utcnow()
})

def upload_to_firebase(file):

    if not file:
        return None

    filename = str(uuid.uuid4()) + ".jpg"

    blob = bucket.blob("complaints/" + filename)

    blob.upload_from_file(file, content_type=file.content_type)

    blob.make_public()

    return blob.public_url

    # ===============================
    # ADD 10 REWARD POINTS
    # ===============================

    user_docs = list(
    db.collection("users")
    .where("email", "==", session["user_email"])
    .stream()
)

    if user_docs:
     doc = user_docs[0]
     data = doc.to_dict()

     new_points = data.get("points", 0) + 10

     badge = get_badge(new_points)

     db.collection("users").document(doc.id).update({
        "points": new_points,
        "badge": badge
    })

    return """
    <script>
    alert("Complaint Submitted Successfully!");
    window.location="/nearby";
    </script>
    """

@app.route("/my-complaints")
def my_complaints():

    if "user_email" not in session:
        return redirect("/login")

    docs = db.collection("complaints") \
             .where("user_email", "==", session["user_email"]) \
             .stream()

    complaints = []

    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        complaints.append(data)

    return render_template(
        "my_complaints.html",
        complaints=complaints
    )
@app.route("/complaint/<id>")
def complaint_details(id):

    if "user_email" not in session:
        return redirect("/login")

    doc = db.collection("complaints").document(id).get()

    if not doc.exists:
        return "Complaint not found"

    complaint = doc.to_dict()

    return render_template(
        "complaint_details.html",
        complaint=complaint
    )

@app.route("/delete-complaint/<id>")
def delete_complaint(id):

    if "user_email" not in session:
        return redirect("/login")

    doc=db.collection("complaints").document(id).get()

    if doc.exists:

        data=doc.to_dict()

        if data["user_email"]==session["user_email"]:

            db.collection("complaints").document(id).delete()

    return redirect("/my-complaints")
@app.route("/edit-complaint/<id>")
def edit_complaint(id):

    return "<h2>Edit Page Coming Next</h2>"

@app.route("/ai-result/<id>")
def ai_result(id):

    return """
    <h2>AI Prediction</h2>

    <h3>Category : Garbage</h3>

    <h3>Confidence : 98%</h3>

    <h3>Priority : High</h3>
    """


@app.route("/officer-dashboard")
def officer_dashboard():

    if "user_email" not in session:
        return redirect("/login")

    if session["role"] != "officer":
        return "Access Denied"

    docs = db.collection("complaints").stream()

    complaints = []

    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        complaints.append(data)

    return render_template(
        "officer_dashboard.html",
        complaints=complaints
    )

@app.route("/nearby")
def nearby():

    if "user_email" not in session:
        return redirect("/login")

    complaints=[]

    docs=db.collection("complaints").stream()

    for doc in docs:
        complaint=doc.to_dict()
        complaints.append(complaint)

    return render_template(
        "nearby.html",
        complaints=complaints
    )


@app.route("/profile")
def profile():

    if "user_email" not in session:
        return redirect("/login")

    docs = list(
        db.collection("users")
        .where("email", "==", session["user_email"])
        .stream()
    )

    if len(docs) == 0:
        return "User not found"

    user = docs[0].to_dict()

    return render_template(
        "profile.html",
        user=user
    )




@app.route("/api/register", methods=["POST"])
def register():
    try:
        print("Register started...")

        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")

        print(name, email, role)

        users_ref = db.collection("users")

        existing = list(users_ref.where("email", "==", email).stream())
        print("Checked existing users")

        if existing:
            return "Email already exists"

        hashed_password = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        )

        print("Password hashed")

        users_ref.add({
             "name": name,
             "email": email,
             "password": hashed_password.decode("utf-8"),
             "role": role,
             "points": 0,
             "badge": "Beginner"
        })

        print("User saved successfully!")

        return "Success"

    except Exception as e:
        traceback.print_exc()
        return f"<pre>{traceback.format_exc()}</pre>"
# =====================================

# =====================================
# LOGIN USER
# =====================================

@app.route("/api/login", methods=["POST"])
def login():

    try:

        email = request.form.get("email")
        password = request.form.get("password")

        docs = list(
            db.collection("users")
            .where("email", "==", email)
            .stream()
        )

        if len(docs) == 0:
            return "User not found"

        user = docs[0].to_dict()

        if bcrypt.checkpw(
            password.encode("utf-8"),
            user["password"].encode("utf-8")
        ):

            session["user_email"] = user["email"]
            session["user_name"] = user["name"]
            session["role"] = user["role"]

            return redirect("/dashboard")

        else:

            return "Wrong Password"

    except Exception as e:

        traceback.print_exc()

        return f"<pre>{traceback.format_exc()}</pre>"
    
@app.route("/update-status/<id>", methods=["POST"])
def update_status(id):

    status = request.form.get("status")

    complaint_ref = db.collection("complaints").document(id)

    complaint = complaint_ref.get().to_dict()

    complaint_ref.update({
        "status": status
    })

    db.collection("notifications").add({

        "user_email": complaint["user_email"],

        "message": f"Your complaint '{complaint['title']}' status changed to {status}.",

        "created_at": datetime.utcnow(),

        "is_read": False

    })

    return redirect("/officer-dashboard")

# NOTIFICATION
@app.route("/notifications")
def notifications():

    if "user_email" not in session:
        return redirect("/login")

    docs = (
        db.collection("notifications")
        .where("user_email", "==", session["user_email"])
        .stream()
    )

    notifications = []

    for doc in docs:
        notifications.append(doc.to_dict())

    return render_template(
        "notifications.html",
        notifications=notifications
    )

@app.route("/map")
def map_page():
    docs = db.collection("complaints").stream()

    complaints = []
    for doc in docs:
        data = doc.to_dict()

        # safety check (important)
        if "latitude" in data and "longitude" in data:
            complaints.append(data)

    return render_template("map.html", complaints=complaints)

# LOGOUT

# =====================================

@app.route("/logout")
def logout():


 session.clear()

 return redirect("/login")
@app.route("/analytics")
def analytics():

    if "user_email" not in session:
        return redirect("/login")

    if session["role"] != "officer":
        return "Access Denied"

    docs = db.collection("complaints").stream()

    complaints = []

    total = 0
    pending = 0
    resolved = 0
    rejected = 0

    pothole = 0
    garbage = 0
    streetlight = 0
    water = 0

    for doc in docs:

        data = doc.to_dict()

        complaints.append(data)

        total += 1

        status = data.get("status", "").lower()

        if status == "pending":
            pending += 1

        elif status == "resolved":
            resolved += 1

        elif status == "rejected":
            rejected += 1

        category = data.get("category", "").lower()

        if category == "pothole":
            pothole += 1

        elif category == "garbage":
            garbage += 1

        elif category == "streetlight":
            streetlight += 1

        elif category == "water_leakage":
            water += 1

    return render_template(

        "analytics.html",

        total=total,
        pending=pending,
        resolved=resolved,
        rejected=rejected,

        pothole=pothole,
        garbage=garbage,
        streetlight=streetlight,
        water=water
    )


# LEADERBOARD 
@app.route("/leaderboard")
def leaderboard():

    users = []

    docs = db.collection("users").stream()

    for doc in docs:
        users.append(doc.to_dict())

    users.sort(key=lambda x: x.get("points", 0), reverse=True)

    return render_template(
        "leaderboard.html",
        users=users
    )

# =====================================

# CURRENT USER

# =====================================

@app.route("/user")
def user():


 if "user_email" not in session:
    return redirect("/login")

 return {
    "name": session["user_name"],
    "email": session["user_email"],
    "role": session["role"]
}


# =====================================

# TEST FIRESTORE

# =====================================

# @app.route("/test")
# def test():


#  db.collection("test").add({
#     "status": "connected"
# })

#  return "Firestore Connected Successfully"



#  MODEL


@app.route("/predict", methods=["POST"])
def predict_route():

    file = request.files.get("image")

    if file is None:
        return jsonify({"error":"No image uploaded"})

    path = "temp.jpg"

    file.save(path)

    category, confidence = predict(path)

    return jsonify({

        "category": category,

        "confidence": round(confidence * 100, 2)

    })




# =====================================

# RUN APP

# =====================================

if __name__ == "__main__":
    app.run(debug=True)

