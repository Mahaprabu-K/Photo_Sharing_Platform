from flask import Flask,render_template,request,redirect,session,jsonify
import pyodbc
import os
import cloudinary
import cloudinary.uploader
from werkzeug.utils import secure_filename

from config import (
    DB_CONNECTION,
    CLOUDINARY_CLOUD_NAME,
    CLOUDINARY_API_KEY,
    CLOUDINARY_API_SECRET
)
cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET
)
from werkzeug.security import generate_password_hash,check_password_hash



app=Flask(__name__)
app.secret_key="photo-secret-key"


conn = pyodbc.connect(DB_CONNECTION)

def get_db_connection():
    return pyodbc.connect(DB_CONNECTION)

@app.route("/")
def home():
    return render_template("index.html")

    

@app.route("/api/user")
def get_user():

    if "user_id" not in session:
        return jsonify({
            "error": "Not logged in"
        }), 401

    cursor = conn.cursor()

    cursor.execute("""
        SELECT FullName, Role
        FROM Users
        WHERE UserID = ?
    """, (session["user_id"],))

    user = cursor.fetchone()

    if user is None:
        return jsonify({
            "error": "User not found"
        }), 404

    return jsonify({
        "fullname": user[0],
        "role": user[1]
    })


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        FullName = request.form["fullname"]
        Email = request.form["email"]
        PasswordHash = generate_password_hash(request.form["password"])
        Role = request.form["role"]

        cursor = conn.cursor()

        try:
            # Check email already exists
            cursor.execute(
                "SELECT UserID FROM Users WHERE Email = ?",
                (Email,)
            )

            existing_user = cursor.fetchone()

            if existing_user:
                return "Email already exists!"

            # Insert new user
            cursor.execute(
                """
                INSERT INTO Users
                (FullName, Email, PasswordHash, Role)
                VALUES (?, ?, ?, ?)
                """,
                (FullName, Email, PasswordHash, Role)
            )

            conn.commit()

            return "Registration Successful"

        except pyodbc.IntegrityError:
            conn.rollback()
            return "Email already exists!"

    return render_template("register.html")



@app.route("/login",methods=["GET","POST"])
def login():
    
    if request.method == "POST":

        Email = request.form["email"]
        PasswordHash = request.form["password"]

        cursor = conn.cursor()

        cursor.execute(
            """SELECT UserID, FullName, Role, PasswordHash
               FROM Users
               WHERE Email = ?""",
            (Email,)
        )
        user = cursor.fetchone()

        if user and check_password_hash(user[3], PasswordHash):
            session["user_id"]=user[0]
            session["fullname"]=user[1]
            session["role"]=user[2]

            if user[2] == "Admin":
                return redirect("/admin")

            elif user[2] == "Team Member":
                return redirect("/team")    

            return "invalid role"

        return "invalid email or password"
    return render_template("login.html")        


@app.route("/admin")
def admin():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "Admin":
        return "Access Denied!"

    return render_template(
        "admin.html",
        fullname=session.get("fullname"),
        role=session.get("role")
    ) 

@app.route("/create-event", methods=["GET", "POST"])
def create_event():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "Admin":
        return "Access Denied!", 403

    if request.method == "POST":

        event_name = request.form.get("event_name", "").strip()
        description = request.form.get("description", "").strip()
        created_by = session["user_id"]

        if not event_name:
            return jsonify({
                "success": False,
                "error": "Event name is required!"
            }), 400

        try:
            cursor = conn.cursor()

            # Check duplicate event name
            cursor.execute("""
                SELECT EventID
                FROM Events
                WHERE EventName = ?
                AND CreatedBy = ?
            """, (event_name, created_by))

            existing_event = cursor.fetchone()

            if existing_event:
                return jsonify({
                    "success": False,
                    "error": "An event with this name already exists!"
                }), 400

            # Create new event
            cursor.execute("""
                INSERT INTO Events
                (EventName, Description, CreatedBy)
                VALUES (?, ?, ?)
            """, (event_name, description, created_by))

            conn.commit()

            return jsonify({
                "success": True,
                "message": "Event Created Successfully!"
            })

        except Exception as e:

            conn.rollback()

            print("CREATE EVENT ERROR:", e)

            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    return render_template("create_event.html")
#EVENTS

@app.route("/api/events")
def get_events():

    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    if session.get("role") != "Admin":
        return jsonify({"error": "Access Denied"}), 403

    cursor = conn.cursor()

    cursor.execute("""
        SELECT EventID, EventName, Description, CreatedAt
        FROM Events
        WHERE CreatedBy = ?
        ORDER BY CreatedAt DESC
    """, (session["user_id"],))

    rows = cursor.fetchall()

    events = []

    for row in rows:
        events.append({
            "event_id": row[0],
            "event_name": row[1],
            "description": row[2],
            "created_at": str(row[3])
        })

    return jsonify(events)


@app.route("/api/delete-event", methods=["DELETE"])
def delete_event():

    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    if session.get("role") != "Admin":
        return jsonify({"error": "Access Denied"}), 403

    data = request.get_json()
    event_id = data.get("event_id")

    if not event_id:
        return jsonify({"error": "Event ID is required"}), 400

    db = get_db_connection()
    cursor = db.cursor()

    try:

        # Check event belongs to logged-in admin
        cursor.execute("""
            SELECT EventID
            FROM Events
            WHERE EventID = ?
            AND CreatedBy = ?
        """, (event_id, session["user_id"]))

        event = cursor.fetchone()

        if event is None:
            return jsonify({
                "error": "Event not found or access denied"
            }), 403

        # Get Cloudinary public IDs
        cursor.execute("""
            SELECT CloudinaryPublicID
            FROM Photos
            WHERE EventID = ?
            AND CloudinaryPublicID IS NOT NULL
        """, (event_id,))

        photos = cursor.fetchall()

        # Delete photos from Cloudinary
        for photo in photos:

            public_id = photo[0]

            try:
                cloudinary.uploader.destroy(public_id)
                print("Deleted from Cloudinary:", public_id)

            except Exception as cloudinary_error:
                print(
                    "Cloudinary delete error:",
                    cloudinary_error
                )

        # Delete GalleryPhotos
        cursor.execute("""
            DELETE FROM GalleryPhotos
            WHERE GalleryID IN (
                SELECT GalleryID
                FROM Galleries
                WHERE EventID = ?
            )
        """, (event_id,))

        # Delete Galleries
        cursor.execute("""
            DELETE FROM Galleries
            WHERE EventID = ?
        """, (event_id,))

        # Delete EventMembers
        cursor.execute("""
            DELETE FROM EventMembers
            WHERE EventID = ?
        """, (event_id,))

        # Delete Photos
        cursor.execute("""
            DELETE FROM Photos
            WHERE EventID = ?
        """, (event_id,))

        # Delete Event
        cursor.execute("""
            DELETE FROM Events
            WHERE EventID = ?
            AND CreatedBy = ?
        """, (event_id, session["user_id"]))

        db.commit()

        return jsonify({
            "message": "Event and its photos deleted successfully!"
        })

    except Exception as e:

        db.rollback()

        print("DELETE EVENT ERROR:", e)

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        cursor.close()
        db.close()


@app.route("/events")
def events_page():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "Admin":
        return "Access Denied!", 403

    return render_template("events.html")

#team member

@app.route("/api/team-members")
def get_team_members():

    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    if session.get("role") != "Admin":
        return jsonify({"error": "Access Denied"}), 403

    cursor = conn.cursor()

    cursor.execute("""
        SELECT UserID, FullName, Email
        FROM Users
        WHERE Role = 'Team Member'
        ORDER BY FullName
    """)

    rows = cursor.fetchall()

    members = []

    for row in rows:
        members.append({
            "user_id": row[0],
            "fullname": row[1],
            "email": row[2]
        })

    return jsonify(members)


@app.route("/api/assign-member", methods=["POST"])
def assign_member():

    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    if session.get("role") != "Admin":
        return jsonify({"error": "Access Denied"}), 403

    data = request.get_json()

    event_id = data.get("event_id")
    user_id = data.get("user_id")

    if not event_id or not user_id:
        return jsonify({"error": "Event and Team Member are required"}), 400

    cursor = conn.cursor()

    # Check whether already assigned
    cursor.execute("""
        SELECT EventMemberID
        FROM EventMembers
        WHERE EventID = ? AND UserID = ?
    """, (event_id, user_id))

    existing = cursor.fetchone()

    if existing:
        return jsonify({
            "error": "Team member already assigned to this event"
        }), 400

    # Assign member
    cursor.execute("""
        INSERT INTO EventMembers (EventID, UserID)
        VALUES (?, ?)
    """, (event_id, user_id))

    conn.commit()

    return jsonify({
        "message": "Team member assigned successfully"
    })


@app.route("/team")
def team_dashboard():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "Team Member":
        return "Access Denied!"

    return render_template("team_dashboard.html")


@app.route("/api/my-events")
def get_my_events():

    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    if session.get("role") != "Team Member":
        return jsonify({"error": "Access Denied"}), 403

    user_id = session["user_id"]

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("""
        SELECT E.EventID, E.EventName, E.Description
        FROM Events E
        INNER JOIN EventMembers EM
            ON E.EventID = EM.EventID
        WHERE EM.UserID = ?
        ORDER BY E.CreatedAt DESC
    """, (user_id,))

    rows = cursor.fetchall()

    events = []

    for row in rows:
        events.append({
            "event_id": row[0],
            "event_name": row[1],
            "description": row[2]
        })

    cursor.close()
    db.close()

    return jsonify(events)

    

@app.route("/team-management")
def team_management():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "Admin":
        return "Access Denied!"

    return render_template("team_management.html") 


@app.route("/upload-photos")
def upload_photos():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "Team Member":
        return "Access Denied!"

    event_id = request.args.get("event_id")

    if not event_id:
        return "Event ID is required!"

    # Check whether this team member is assigned to this event
    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("""
        SELECT E.EventID, E.EventName
        FROM Events E
        INNER JOIN EventMembers EM
            ON E.EventID = EM.EventID
        WHERE E.EventID = ?
        AND EM.UserID = ?
    """, (event_id, session["user_id"]))

    event = cursor.fetchone()

    cursor.close()
    db.close()

    if event is None:
        return "You are not assigned to this event!"

    return render_template(
    "upload_photos.html",
    event_name=event[1]
)


@app.route("/api/event/<int:event_id>")
def get_event(event_id):

    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    if session.get("role") != "Team Member":
        return jsonify({"error": "Access Denied"}), 403

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("""
        SELECT E.EventID, E.EventName
        FROM Events E
        INNER JOIN EventMembers EM
            ON E.EventID = EM.EventID
        WHERE E.EventID = ?
        AND EM.UserID = ?
    """, (event_id, session["user_id"]))

    event = cursor.fetchone()

    cursor.close()
    db.close()

    if event is None:
        return jsonify({"error": "Event not found"}), 404

    return jsonify({
        "event_id": event[0],
        "event_name": event[1]
    })



@app.route("/api/upload-photos", methods=["POST"])
def upload_photos_api():

    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    if session.get("role") != "Team Member":
        return jsonify({"error": "Access Denied"}), 403

    event_id = request.form.get("event_id")
    files = request.files.getlist("photos")

    if not event_id:
        return jsonify({"error": "Event ID is required!"}), 400

    if not files:
        return jsonify({"error": "Please select photos!"}), 400

    # Check whether team member is assigned to this event
    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("""
        SELECT EventID
        FROM EventMembers
        WHERE EventID = ?
        AND UserID = ?
    """, (event_id, session["user_id"]))

    assigned_event = cursor.fetchone()

    if assigned_event is None:
        cursor.close()
        db.close()
        return jsonify({
            "error": "You are not assigned to this event!"
        }), 403

    uploaded_count = 0

    try:

        for file in files:

            if file.filename == "":
                continue

            # Allow only image files
            allowed_extensions = {
                ".jpg",
                ".jpeg",
                ".png",
                ".webp"
            }

            extension = os.path.splitext(
                file.filename
            )[1].lower()

            if extension not in allowed_extensions:
                continue

            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                file,
                folder=f"platformai/events/{event_id}"
            )

            storage_location = result["secure_url"]
            cloudinary_public_id = result["public_id"]

            filename = secure_filename(file.filename)

            # Get file size
            file.seek(0, 2)
            file_size = file.tell()
            file.seek(0)

            # Save metadata in SQL Server
            cursor.execute("""
                INSERT INTO Photos
                (
                   EventID,
                   UploadedBy,
                     Filename,
                    StorageLocation,
                     FileSize,
                      CloudinaryPublicID
                    )
                VALUES (?, ?, ?, ?, ?, ?)""", 
                (
                event_id,
                session["user_id"],
                filename,
                storage_location,
                 file_size,
                cloudinary_public_id
                ))

            uploaded_count += 1

        db.commit()

        return jsonify({
            "message": f"{uploaded_count} photo(s) uploaded successfully!"
        })

    except Exception as e:

        db.rollback()

        print("UPLOAD ERROR:", e)

        return jsonify({
        "error": str(e)
    }), 5000

    finally:

        cursor.close()
        db.close()


@app.route("/api/event-photos/<int:event_id>")
def get_event_photos(event_id):

    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    if session.get("role") != "Admin":
        return jsonify({"error": "Access Denied"}), 403

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("""
        SELECT
            P.PhotoID,
            P.EventID,
            P.Filename,
            P.StorageLocation,
            P.FileSize,
            P.CreatedAt,
            U.FullName,
            P.IsSelected
        FROM Photos P
        INNER JOIN Users U
            ON P.UploadedBy = U.UserID
        INNER JOIN Events E
            ON P.EventID = E.EventID
        WHERE P.EventID = ?
        AND E.CreatedBy = ?
        ORDER BY P.CreatedAt DESC
    """, (event_id, session["user_id"]))

    rows = cursor.fetchall()

    photos = []

    for row in rows:
        photos.append({
            "photo_id": row[0],
            "event_id": row[1],
            "filename": row[2],
            "storage_location": row[3],
            "file_size": row[4],
            "created_at": str(row[5]),
            "uploaded_by": row[6],
            "is_selected": bool(row[7])
        })

    cursor.close()
    db.close()

    return jsonify(photos)

@app.route("/admin-photos")
def admin_photos():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "Admin":
        return "Access Denied!"

    return render_template("admin_photos.html") 


#selected photos

@app.route("/api/select-photos", methods=["POST"])
def select_photos():

    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    if session.get("role") != "Admin":
        return jsonify({"error": "Access Denied"}), 403

    data = request.get_json()

    event_id = data.get("event_id")
    selected_photo_ids = data.get("selected_photo_ids", [])

    if not event_id:
        return jsonify({"error": "Event ID is required!"}), 400

    db = get_db_connection()
    cursor = db.cursor()

    try:

        # Check whether admin owns this event
        cursor.execute("""
            SELECT EventID
            FROM Events
            WHERE EventID = ?
            AND CreatedBy = ?
        """, (event_id, session["user_id"]))

        event = cursor.fetchone()

        if event is None:
            return jsonify({"error": "Event not found or access denied"}), 403

        # First unselect all photos in this event
        cursor.execute("""
            UPDATE Photos
            SET IsSelected = 0
            WHERE EventID = ?
        """, (event_id,))

        # Select chosen photos
        for photo_id in selected_photo_ids:

            cursor.execute("""
                UPDATE Photos
                SET IsSelected = 1
                WHERE PhotoID = ?
                AND EventID = ?
            """, (photo_id, event_id))

        db.commit()

        return jsonify({
            "message": "Photo selection saved successfully!"
        })

    except Exception as e:

        db.rollback()

        print("SELECT PHOTO ERROR:", e)

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        cursor.close()
        db.close()


#gallery creation 

@app.route("/create-gallery")
def create_gallery():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "Admin":
        return "Access Denied!"

    return render_template("create_gallery.html")


@app.route("/api/gallery-events")
def gallery_events():

    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    if session.get("role") != "Admin":
        return jsonify({"error": "Access Denied"}), 403

    db = get_db_connection()
    cursor = db.cursor()

    try:

        cursor.execute("""
            SELECT
                E.EventID,
                E.EventName,

                COUNT(P.PhotoID) AS TotalPhotos,

                SUM(
                    CASE
                        WHEN P.IsSelected = 1 THEN 1
                        ELSE 0
                    END
                ) AS SelectedPhotos

            FROM Events E

            LEFT JOIN Photos P
                ON E.EventID = P.EventID

            WHERE E.CreatedBy = ?

            GROUP BY
                E.EventID,
                E.EventName,
                E.CreatedAt

            ORDER BY E.CreatedAt DESC
        """, (session["user_id"],))

        rows = cursor.fetchall()

        events = []

        for row in rows:

            events.append({
                "event_id": row[0],
                "event_name": row[1],
                "total_photos": row[2],
                "selected_photos": row[3] or 0
            })

        return jsonify(events)

    except Exception as e:

        print("GALLERY EVENTS ERROR:", e)

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        cursor.close()
        db.close()

@app.route("/api/create-gallery", methods=["POST"])
def create_gallery_api():

    if "user_id" not in session:
        return jsonify({
            "error": "Not logged in"
        }), 401

    if session.get("role") != "Admin":
        return jsonify({
            "error": "Access Denied"
        }), 403

    data = request.get_json()

    event_id = data.get("event_id")
    pin = data.get("pin")

    if not event_id:
        return jsonify({
            "error": "Event ID is required!"
        }), 400

    if not pin:
        return jsonify({
            "error": "PIN is required!"
        }), 400

    db = get_db_connection()
    cursor = db.cursor()

    try:

        # --------------------------------
        # Check Event Ownership
        # --------------------------------

        cursor.execute("""
            SELECT EventID
            FROM Events
            WHERE EventID = ?
            AND CreatedBy = ?
        """, (
            event_id,
            session["user_id"]
        ))

        event = cursor.fetchone()

        if event is None:
            return jsonify({
                "error": "Event not found or access denied"
            }), 403


        # --------------------------------
        # Check Existing Published Gallery
        # --------------------------------

        cursor.execute("""
            SELECT GalleryID
            FROM Galleries
            WHERE EventID = ?
            AND IsPublished = 1
        """, (event_id,))

        existing_gallery = cursor.fetchone()


        if existing_gallery:

            existing_gallery_id = existing_gallery[0]

            cursor.execute("""
                SELECT GalleryToken, PIN
                FROM Galleries
                WHERE GalleryID = ?
            """, (existing_gallery_id,))

            existing_gallery_data = cursor.fetchone()


            if existing_gallery_data is None:
                return jsonify({
                    "error": "Existing gallery details not found"
                }), 500


            return jsonify({
                "success": False,
                "existing_gallery": True,
                "message": "Published gallery already exists for this event.",
                "gallery_id": existing_gallery_id,
                "gallery_token": existing_gallery_data[0],
                "gallery_pin": existing_gallery_data[1]
            }), 200


        # --------------------------------
        # Get Selected Photos
        # --------------------------------

        cursor.execute("""
            SELECT PhotoID
            FROM Photos
            WHERE EventID = ?
            AND IsSelected = 1
        """, (event_id,))

        selected_photos = cursor.fetchall()


        if not selected_photos:
            return jsonify({
                "error": "No selected photos found"
            }), 400


        # --------------------------------
        # Generate Gallery Token
        # --------------------------------

        import secrets

        gallery_token = secrets.token_urlsafe(16)


        # --------------------------------
        # Create Gallery
        # --------------------------------

        cursor.execute("""
            INSERT INTO Galleries
            (
                EventID,
                GalleryToken,
                PIN,
                IsPublished
            )
            VALUES (?, ?, ?, 0)
        """, (
            event_id,
            gallery_token,
            pin
        ))

        db.commit()


        # --------------------------------
        # Get Gallery ID
        # --------------------------------

        cursor.execute("""
            SELECT GalleryID
            FROM Galleries
            WHERE GalleryToken = ?
        """, (gallery_token,))

        gallery = cursor.fetchone()


        if gallery is None:
            return jsonify({
                "error": "Gallery was created but ID could not be found"
            }), 500

        gallery_id = gallery[0]


        # --------------------------------
        # Add Selected Photos
        # --------------------------------

        for photo in selected_photos:

            cursor.execute("""
                INSERT INTO GalleryPhotos
                (
                    GalleryID,
                    PhotoID
                )
                VALUES (?, ?)
            """, (
                gallery_id,
                photo[0]
            ))

        db.commit()


        # --------------------------------
        # Success Response
        # --------------------------------

        return jsonify({
            "success": True,
            "message": "Gallery created successfully!",
            "gallery_id": gallery_id,
            "gallery_token": gallery_token
        })


    except Exception as e:

        db.rollback()

        print("CREATE GALLERY ERROR:", e)

        return jsonify({
            "error": str(e)
        }), 500


    finally:

        cursor.close()
        db.close()


@app.route("/api/publish-gallery", methods=["POST"])
def publish_gallery():

    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    if session.get("role") != "Admin":
        return jsonify({"error": "Access Denied"}), 403

    data = request.get_json()

    gallery_id = data.get("gallery_id")

    if not gallery_id:
        return jsonify({"error": "Gallery ID is required!"}), 400

    db = get_db_connection()
    cursor = db.cursor()

    try:

        cursor.execute("""
            SELECT G.GalleryID
            FROM Galleries G
            INNER JOIN Events E
                ON G.EventID = E.EventID
            WHERE G.GalleryID = ?
            AND E.CreatedBy = ?
        """, (gallery_id, session["user_id"]))

        gallery = cursor.fetchone()

        if gallery is None:
            return jsonify({
                "error": "Gallery not found or access denied"
            }), 403

        cursor.execute("""
            UPDATE Galleries
            SET IsPublished = 1,
                PublishedAt = GETDATE()
            WHERE GalleryID = ?
        """, (gallery_id,))

        db.commit()

        return jsonify({
            "message": "Gallery published successfully!"
        })

    except Exception as e:

        db.rollback()

        print("PUBLISH GALLERY ERROR:", e)

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        cursor.close()
        db.close()


@app.route("/gallery/<gallery_token>")
def customer_gallery(gallery_token):

    return render_template("customer_gallery.html")


@app.route("/api/verify-gallery-pin", methods=["POST"])
def verify_gallery_pin():

    data = request.get_json()

    gallery_token = data.get("gallery_token")
    pin = data.get("pin")

    if not gallery_token or not pin:
        return jsonify({
            "error": "Gallery token and PIN are required!"
        }), 400

    db = get_db_connection()
    cursor = db.cursor()

    try:

        cursor.execute("""
            SELECT GalleryID, IsPublished
            FROM Galleries
            WHERE GalleryToken = ?
            AND PIN = ?
        """, (gallery_token, pin))

        gallery = cursor.fetchone()

        if gallery is None:
            return jsonify({
                "error": "Invalid PIN!"
            }), 401

        if gallery[1] != 1:
            return jsonify({
                "error": "Gallery is not published!"
            }), 403

        return jsonify({
            "message": "PIN verified successfully!",
            "gallery_id": gallery[0]
        })

    finally:

        cursor.close()
        db.close()


@app.route("/api/customer-gallery/<int:gallery_id>")
def get_customer_gallery(gallery_id):

    db = get_db_connection()
    cursor = db.cursor()

    try:

        cursor.execute("""
            SELECT
                P.PhotoID,
                P.Filename,
                P.StorageLocation
            FROM GalleryPhotos GP
            INNER JOIN Photos P
                ON GP.PhotoID = P.PhotoID
            INNER JOIN Galleries G
                ON GP.GalleryID = G.GalleryID
            WHERE GP.GalleryID = ?
            AND G.IsPublished = 1
            AND P.IsSelected = 1
            ORDER BY P.CreatedAt DESC
        """, (gallery_id,))

        rows = cursor.fetchall()

        photos = []

        for row in rows:

            photos.append({
                "photo_id": row[0],
                "filename": row[1],
                "storage_location": row[2]
            })

        return jsonify(photos)

    except Exception as e:

        print("CUSTOMER GALLERY ERROR:", e)

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        cursor.close()
        db.close()



@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)