from flask import Flask, render_template, request, redirect, session, jsonify
import psycopg2
import psycopg2.errors
import os
import cloudinary
import cloudinary.uploader
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from config import (
    DATABASE_URL ,
    CLOUDINARY_CLOUD_NAME,
    CLOUDINARY_API_KEY,
    CLOUDINARY_API_SECRET
)

# --------------------------------------------------
# CLOUDINARY CONFIG
# --------------------------------------------------

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET
)


# --------------------------------------------------
# FLASK APP
# --------------------------------------------------

app = Flask(__name__)
app.secret_key = "photo-secret-key"


# --------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)

    print("DATABASE:", conn.info.dbname)
    print("HOST:", conn.info.host)
    print("PORT:", conn.info.port)

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            current_database(),
            current_schema(),
            inet_server_addr(),
            inet_server_port()
    """)

    result = cursor.fetchone()

    print("DB INFO:", result)

    cursor.execute("""
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)

    tables = cursor.fetchall()

    print("TABLES:", tables)

    cursor.close()

    return conn


# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html")


# --------------------------------------------------
# GET LOGGED-IN USER
# --------------------------------------------------

@app.route("/api/user")
def get_user():

    if "user_id" not in session:
        return jsonify({
            "error": "Not logged in"
        }), 401

    db = get_db_connection()
    cursor = db.cursor()

    try:
        cursor.execute("""
            SELECT FullName, Role
            FROM Users
            WHERE UserID = %s
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

    finally:
        cursor.close()
        db.close()


# --------------------------------------------------
# REGISTER
# --------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        FullName = request.form["fullname"]
        Email = request.form["email"]
        PasswordHash = generate_password_hash(
            request.form["password"]
        )
        Role = request.form["role"]

        # Admin Email only for Team Member
        AdminEmail = request.form.get("admin_email")

        db = get_db_connection()
        cursor = db.cursor()

        try:

            # Check existing email
            cursor.execute("""
                SELECT UserID
                FROM Users
                WHERE Email = %s
            """, (Email,))

            existing_user = cursor.fetchone()

            if existing_user:
                return "Email already exists!"


            # Team Member registration
            if Role == "Team Member":

                if not AdminEmail:
                    return "Admin email is required"

                # Find Admin using email
                cursor.execute("""
                    SELECT UserID
                    FROM Users
                    WHERE Email = %s
                    AND Role = 'Admin'
                """, (AdminEmail,))

                admin = cursor.fetchone()

                if not admin:
                    return "Admin email not found"

                AdminID = admin[0]

            else:

                # Admin account
                AdminID = None


            # Insert user
            cursor.execute("""
                INSERT INTO Users
                (
                    FullName,
                    Email,
                    PasswordHash,
                    Role,
                    AdminID
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (
                FullName,
                Email,
                PasswordHash,
                Role,
                AdminID
            ))

            db.commit()

            return "Registration Successful"


        except psycopg2.IntegrityError:

            db.rollback()

            return "Email already exists!"


        except Exception as e:

            db.rollback()

            print("REGISTER ERROR:", e)

            return "Registration failed!"


        finally:

            cursor.close()
            db.close()


    return render_template("register.html")

# --------------------------------------------------
# LOGIN
# --------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        Email = request.form["email"]
        Password = request.form["password"]

        db = get_db_connection()
        cursor = db.cursor()

        try:

            cursor.execute("""
                SELECT
                    UserID,
                    FullName,
                    Role,
                    PasswordHash
                FROM public.users
                WHERE Email = %s
            """, (Email,))

            user = cursor.fetchone()

            if user and check_password_hash(
                user[3],
                Password
            ):

                session["user_id"] = user[0]
                session["fullname"] = user[1]
                session["role"] = user[2]

                if user[2] == "Admin":
                    return redirect("/admin")

                elif user[2] == "Team Member":
                    return redirect("/team")

                return "invalid role"

            return "invalid email or password"

        finally:

            cursor.close()
            db.close()

    return render_template("login.html")


# --------------------------------------------------
# ADMIN DASHBOARD
# --------------------------------------------------

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


# --------------------------------------------------
# CREATE EVENT
# --------------------------------------------------

@app.route("/create-event", methods=["GET", "POST"])
def create_event():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "Admin":
        return "Access Denied!", 403

    if request.method == "POST":

        event_name = request.form.get(
            "event_name",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        created_by = session["user_id"]

        if not event_name:
            return jsonify({
                "success": False,
                "error": "Event name is required!"
            }), 400

        db = get_db_connection()
        cursor = db.cursor()

        try:

            cursor.execute("""
                SELECT EventID
                FROM Events
                WHERE EventName = %s
                AND CreatedBy = %s
            """, (
                event_name,
                created_by
            ))

            existing_event = cursor.fetchone()

            if existing_event:
                return jsonify({
                    "success": False,
                    "error":
                    "An event with this name already exists!"
                }), 400

            cursor.execute("""
                INSERT INTO Events
                (EventName, Description, CreatedBy)
                VALUES (%s, %s, %s)
            """, (
                event_name,
                description,
                created_by
            ))

            db.commit()

            return jsonify({
                "success": True,
                "message":
                "Event Created Successfully!"
            })

        except Exception as e:

            db.rollback()

            print("CREATE EVENT ERROR:", e)

            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

        finally:

            cursor.close()
            db.close()

    return render_template("create_event.html")


# --------------------------------------------------
# GET EVENTS
# --------------------------------------------------

@app.route("/api/events")
def get_events():

    if "user_id" not in session:
        return jsonify({
            "error": "Not logged in"
        }), 401

    if session.get("role") != "Admin":
        return jsonify({
            "error": "Access Denied"
        }), 403

    db = get_db_connection()
    cursor = db.cursor()

    try:

        cursor.execute("""
            SELECT
                EventID,
                EventName,
                Description,
                CreatedAt
            FROM Events
            WHERE CreatedBy = %s
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

    finally:

        cursor.close()
        db.close()


# --------------------------------------------------
# DELETE EVENT
# --------------------------------------------------

@app.route("/api/delete-event", methods=["DELETE"])
def delete_event():

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

    if not event_id:
        return jsonify({
            "error": "Event ID is required"
        }), 400

    db = get_db_connection()
    cursor = db.cursor()

    try:

        cursor.execute("""
            SELECT EventID
            FROM Events
            WHERE EventID = %s
            AND CreatedBy = %s
        """, (
            event_id,
            session["user_id"]
        ))

        event = cursor.fetchone()

        if event is None:
            return jsonify({
                "error":
                "Event not found or access denied"
            }), 403

        # Get Cloudinary public IDs
        cursor.execute("""
            SELECT CloudinaryPublicID
            FROM Photos
            WHERE EventID = %s
            AND CloudinaryPublicID IS NOT NULL
        """, (event_id,))

        photos = cursor.fetchall()

        # Delete photos from Cloudinary
        for photo in photos:

            public_id = photo[0]

            try:

                cloudinary.uploader.destroy(
                    public_id
                )

                print(
                    "Deleted from Cloudinary:",
                    public_id
                )

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
                WHERE EventID = %s
            )
        """, (event_id,))

        # Delete Galleries
        cursor.execute("""
            DELETE FROM Galleries
            WHERE EventID = %s
        """, (event_id,))

        # Delete EventMembers
        cursor.execute("""
            DELETE FROM EventMembers
            WHERE EventID = %s
        """, (event_id,))

        # Delete Photos
        cursor.execute("""
            DELETE FROM Photos
            WHERE EventID = %s
        """, (event_id,))

        # Delete Event
        cursor.execute("""
            DELETE FROM Events
            WHERE EventID = %s
            AND CreatedBy = %s
        """, (
            event_id,
            session["user_id"]
        ))

        db.commit()

        return jsonify({
            "message":
            "Event and its photos deleted successfully!"
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


# --------------------------------------------------
# EVENTS PAGE
# --------------------------------------------------

@app.route("/events")
def events_page():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "Admin":
        return "Access Denied!", 403

    return render_template("events.html")


# --------------------------------------------------
# TEAM MEMBERS
# --------------------------------------------------

@app.route("/api/team-members")
def get_team_members():

    if "user_id" not in session:
        return jsonify({
            "error": "Not logged in"
        }), 401

    if session.get("role") != "Admin":
        return jsonify({
            "error": "Access Denied"
        }), 403

    db = get_db_connection()
    cursor = db.cursor()

    try:

        cursor.execute("""
            SELECT
                UserID,
                FullName,
                Email
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

    finally:

        cursor.close()
        db.close()


# --------------------------------------------------
# ASSIGN TEAM MEMBER
# --------------------------------------------------

@app.route("/api/assign-member", methods=["POST"])
def assign_member():

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
    user_id = data.get("user_id")

    if not event_id or not user_id:
        return jsonify({
            "error":
            "Event and Team Member are required"
        }), 400

    db = get_db_connection()
    cursor = db.cursor()

    try:

        cursor.execute("""
            SELECT EventMemberID
            FROM EventMembers
            WHERE EventID = %s
            AND UserID = %s
        """, (
            event_id,
            user_id
        ))

        existing = cursor.fetchone()

        if existing:

            return jsonify({
                "error":
                "Team member already assigned to this event"
            }), 400

        cursor.execute("""
            INSERT INTO EventMembers
            (EventID, UserID)
            VALUES (%s, %s)
        """, (
            event_id,
            user_id
        ))

        db.commit()

        return jsonify({
            "message":
            "Team member assigned successfully"
        })

    except Exception as e:

        db.rollback()

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        cursor.close()
        db.close()


# --------------------------------------------------
# TEAM DASHBOARD
# --------------------------------------------------

@app.route("/team")
def team_dashboard():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "Team Member":
        return "Access Denied!"

    return render_template(
        "team_dashboard.html"
    )


# --------------------------------------------------
# TEAM MEMBER EVENTS
# --------------------------------------------------

@app.route("/api/my-events")
def get_my_events():

    if "user_id" not in session:
        return jsonify({
            "error": "Not logged in"
        }), 401

    if session.get("role") != "Team Member":
        return jsonify({
            "error": "Access Denied"
        }), 403

    user_id = session["user_id"]

    db = get_db_connection()
    cursor = db.cursor()

    try:

        cursor.execute("""
            SELECT
                E.EventID,
                E.EventName,
                E.Description
            FROM Events E
            INNER JOIN EventMembers EM
                ON E.EventID = EM.EventID
            WHERE EM.UserID = %s
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

        return jsonify(events)

    finally:

        cursor.close()
        db.close()


# --------------------------------------------------
# TEAM MANAGEMENT PAGE
# --------------------------------------------------

@app.route("/team-management")
def team_management():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "Admin":
        return "Access Denied!"

    return render_template(
        "team_management.html"
    )


# --------------------------------------------------
# UPLOAD PHOTOS PAGE
# --------------------------------------------------

@app.route("/upload-photos")
def upload_photos():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "Team Member":
        return "Access Denied!"

    event_id = request.args.get("event_id")

    if not event_id:
        return "Event ID is required!"

    db = get_db_connection()
    cursor = db.cursor()

    try:

        cursor.execute("""
            SELECT
                E.EventID,
                E.EventName
            FROM Events E
            INNER JOIN EventMembers EM
                ON E.EventID = EM.EventID
            WHERE E.EventID = %s
            AND EM.UserID = %s
        """, (
            event_id,
            session["user_id"]
        ))

        event = cursor.fetchone()

        if event is None:
            return "You are not assigned to this event!"

        return render_template(
            "upload_photos.html",
            event_name=event[1]
        )

    finally:

        cursor.close()
        db.close()


# --------------------------------------------------
# GET EVENT
# --------------------------------------------------

@app.route("/api/event/<int:event_id>")
def get_event(event_id):

    if "user_id" not in session:
        return jsonify({
            "error": "Not logged in"
        }), 401

    if session.get("role") != "Team Member":
        return jsonify({
            "error": "Access Denied"
        }), 403

    db = get_db_connection()
    cursor = db.cursor()

    try:

        cursor.execute("""
            SELECT
                E.EventID,
                E.EventName
            FROM Events E
            INNER JOIN EventMembers EM
                ON E.EventID = EM.EventID
            WHERE E.EventID = %s
            AND EM.UserID = %s
        """, (
            event_id,
            session["user_id"]
        ))

        event = cursor.fetchone()

        if event is None:
            return jsonify({
                "error": "Event not found"
            }), 404

        return jsonify({
            "event_id": event[0],
            "event_name": event[1]
        })

    finally:

        cursor.close()
        db.close()


# --------------------------------------------------
# UPLOAD PHOTOS API
# --------------------------------------------------

@app.route("/api/upload-photos", methods=["POST"])
def upload_photos_api():

    if "user_id" not in session:
        return jsonify({
            "error": "Not logged in"
        }), 401

    if session.get("role") != "Team Member":
        return jsonify({
            "error": "Access Denied"
        }), 403

    event_id = request.form.get("event_id")
    files = request.files.getlist("photos")

    if not event_id:
        return jsonify({
            "error": "Event ID is required!"
        }), 400

    if not files:
        return jsonify({
            "error": "Please select photos!"
        }), 400

    db = get_db_connection()
    cursor = db.cursor()

    try:

        cursor.execute("""
            SELECT EventID
            FROM EventMembers
            WHERE EventID = %s
            AND UserID = %s
        """, (
            event_id,
            session["user_id"]
        ))

        assigned_event = cursor.fetchone()

        if assigned_event is None:

            return jsonify({
                "error":
                "You are not assigned to this event!"
            }), 403

        uploaded_count = 0

        allowed_extensions = {
            ".jpg",
            ".jpeg",
            ".png",
            ".webp"
        }

        for file in files:

            if file.filename == "":
                continue

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

            filename = secure_filename(
                file.filename
            )

            # Get file size
            file.seek(0, 2)
            file_size = file.tell()
            file.seek(0)

            cursor.execute("""
                INSERT INTO Photos
                (
                    EventID,
                    UploadedBy,
                    Filename,
                    StorageLocation,
                    Filesize,
                    CloudinaryPublicID
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
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
            "message":
            f"{uploaded_count} photo(s) uploaded successfully!"
        })

    except Exception as e:

        db.rollback()

        print("UPLOAD ERROR:", e)

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        cursor.close()
        db.close()


# --------------------------------------------------
# EVENT PHOTOS
# --------------------------------------------------

@app.route("/api/event-photos/<int:event_id>")
def get_event_photos(event_id):

    if "user_id" not in session:
        return jsonify({
            "error": "Not logged in"
        }), 401

    if session.get("role") != "Admin":
        return jsonify({
            "error": "Access Denied"
        }), 403

    db = get_db_connection()
    cursor = db.cursor()

    try:

        cursor.execute("""
            SELECT
                P.PhotoID,
                P.EventID,
                P.Filename,
                P.StorageLocation,
                P.Filesize,
                P.CreatedAt,
                U.FullName,
                P.IsSelected
            FROM Photos P
            INNER JOIN Users U
                ON P.UploadedBy = U.UserID
            INNER JOIN Events E
                ON P.EventID = E.EventID
            WHERE P.EventID = %s
            AND E.CreatedBy = %s
            ORDER BY P.CreatedAt DESC
        """, (
            event_id,
            session["user_id"]
        ))

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

        return jsonify(photos)

    finally:

        cursor.close()
        db.close()


# --------------------------------------------------
# ADMIN PHOTOS PAGE
# --------------------------------------------------

@app.route("/admin-photos")
def admin_photos():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "Admin":
        return "Access Denied!"

    return render_template(
        "admin_photos.html"
    )


# --------------------------------------------------
# SELECT PHOTOS
# --------------------------------------------------

@app.route("/api/select-photos", methods=["POST"])
def select_photos():

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
    selected_photo_ids = data.get(
        "selected_photo_ids",
        []
    )

    if not event_id:
        return jsonify({
            "error": "Event ID is required!"
        }), 400

    db = get_db_connection()
    cursor = db.cursor()

    try:

        cursor.execute("""
            SELECT EventID
            FROM Events
            WHERE EventID = %s
            AND CreatedBy = %s
        """, (
            event_id,
            session["user_id"]
        ))

        event = cursor.fetchone()

        if event is None:
            return jsonify({
                "error":
                "Event not found or access denied"
            }), 403

        # Unselect all photos
        cursor.execute("""
            UPDATE Photos
            SET IsSelected = FALSE
            WHERE EventID = %s
        """, (event_id,))

        # Select chosen photos
        for photo_id in selected_photo_ids:

            cursor.execute("""
                UPDATE Photos
                SET IsSelected = TRUE
                WHERE PhotoID = %s
                AND EventID = %s
            """, (
                photo_id,
                event_id
            ))

        db.commit()

        return jsonify({
            "message":
            "Photo selection saved successfully!"
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


# --------------------------------------------------
# CREATE GALLERY PAGE
# --------------------------------------------------

@app.route("/create-gallery")
def create_gallery():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "Admin":
        return "Access Denied!"

    return render_template(
        "create_gallery.html"
    )


# --------------------------------------------------
# GALLERY EVENTS
# --------------------------------------------------

@app.route("/api/gallery-events")
def gallery_events():

    if "user_id" not in session:
        return jsonify({
            "error": "Not logged in"
        }), 401

    if session.get("role") != "Admin":
        return jsonify({
            "error": "Access Denied"
        }), 403

    db = get_db_connection()
    cursor = db.cursor()

    try:

        cursor.execute("""
            SELECT
                E.EventID,
                E.EventName,
                COUNT(P.PhotoID) AS TotalPhotos,
                COALESCE(
                    SUM(
                        CASE
                            WHEN P.IsSelected = TRUE
                            THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS SelectedPhotos
            FROM Events E
            LEFT JOIN Photos P
                ON E.EventID = P.EventID
            WHERE E.CreatedBy = %s
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

        print(
            "GALLERY EVENTS ERROR:",
            e
        )

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        cursor.close()
        db.close()


# --------------------------------------------------
# CREATE GALLERY API
# --------------------------------------------------

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

        # Check Event Ownership
        cursor.execute("""
            SELECT EventID
            FROM Events
            WHERE EventID = %s
            AND CreatedBy = %s
        """, (
            event_id,
            session["user_id"]
        ))

        event = cursor.fetchone()

        if event is None:
            return jsonify({
                "error":
                "Event not found or access denied"
            }), 403

        # Check existing published gallery
        cursor.execute("""
            SELECT GalleryID
            FROM Galleries
            WHERE EventID = %s
            AND IsPublished = TRUE
        """, (event_id,))

        existing_gallery = cursor.fetchone()

        if existing_gallery:

            existing_gallery_id = existing_gallery[0]

            cursor.execute("""
                SELECT GalleryToken, PIN
                FROM Galleries
                WHERE GalleryID = %s
            """, (existing_gallery_id,))

            existing_gallery_data = cursor.fetchone()

            if existing_gallery_data is None:
                return jsonify({
                    "error":
                    "Existing gallery details not found"
                }), 500

            return jsonify({
                "success": False,
                "existing_gallery": True,
                "message":
                "Published gallery already exists for this event.",
                "gallery_id":
                existing_gallery_id,
                "gallery_token":
                existing_gallery_data[0],
                "gallery_pin":
                existing_gallery_data[1]
            }), 200

        # Get selected photos
        cursor.execute("""
            SELECT PhotoID
            FROM Photos
            WHERE EventID = %s
            AND IsSelected = TRUE
        """, (event_id,))

        selected_photos = cursor.fetchall()

        if not selected_photos:
            return jsonify({
                "error":
                "No selected photos found"
            }), 400

        # Generate token
        import secrets

        gallery_token = secrets.token_urlsafe(16)

        # Create gallery
        cursor.execute("""
            INSERT INTO Galleries
            (
                EventID,
                GalleryToken,
                PIN,
                IsPublished
            )
            VALUES (%s, %s, %s, FALSE)
            RETURNING GalleryID
        """, (
            event_id,
            gallery_token,
            pin
        ))

        gallery = cursor.fetchone()

        if gallery is None:
            db.rollback()

            return jsonify({
                "error":
                "Gallery was created but ID could not be found"
            }), 500

        gallery_id = gallery[0]

        # Add selected photos
        for photo in selected_photos:

            cursor.execute("""
                INSERT INTO GalleryPhotos
                (
                    GalleryID,
                    PhotoID
                )
                VALUES (%s, %s)
            """, (
                gallery_id,
                photo[0]
            ))

        db.commit()

        return jsonify({
            "success": True,
            "message":
            "Gallery created successfully!",
            "gallery_id":
            gallery_id,
            "gallery_token":
            gallery_token
        })

    except Exception as e:

        db.rollback()

        print(
            "CREATE GALLERY ERROR:",
            e
        )

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        cursor.close()
        db.close()


# --------------------------------------------------
# PUBLISH GALLERY
# --------------------------------------------------

@app.route("/api/publish-gallery", methods=["POST"])
def publish_gallery():

    if "user_id" not in session:
        return jsonify({
            "error": "Not logged in"
        }), 401

    if session.get("role") != "Admin":
        return jsonify({
            "error": "Access Denied"
        }), 403

    data = request.get_json()

    gallery_id = data.get("gallery_id")

    if not gallery_id:
        return jsonify({
            "error": "Gallery ID is required!"
        }), 400

    db = get_db_connection()
    cursor = db.cursor()

    try:

        cursor.execute("""
            SELECT G.GalleryID
            FROM Galleries G
            INNER JOIN Events E
                ON G.EventID = E.EventID
            WHERE G.GalleryID = %s
            AND E.CreatedBy = %s
        """, (
            gallery_id,
            session["user_id"]
        ))

        gallery = cursor.fetchone()

        if gallery is None:
            return jsonify({
                "error":
                "Gallery not found or access denied"
            }), 403

        cursor.execute("""
            UPDATE Galleries
            SET
                IsPublished = TRUE,
                PublishedAt = CURRENT_TIMESTAMP
            WHERE GalleryID = %s
        """, (gallery_id,))

        db.commit()

        return jsonify({
            "message":
            "Gallery published successfully!"
        })

    except Exception as e:

        db.rollback()

        print(
            "PUBLISH GALLERY ERROR:",
            e
        )

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        cursor.close()
        db.close()


# --------------------------------------------------
# CUSTOMER GALLERY PAGE
# --------------------------------------------------

@app.route("/gallery/<gallery_token>")
def customer_gallery(gallery_token):

    return render_template(
        "customer_gallery.html"
    )


# --------------------------------------------------
# VERIFY GALLERY PIN
# --------------------------------------------------

@app.route("/api/verify-gallery-pin", methods=["POST"])
def verify_gallery_pin():

    data = request.get_json()

    gallery_token = data.get(
        "gallery_token"
    )

    pin = data.get("pin")

    if not gallery_token or not pin:
        return jsonify({
            "error":
            "Gallery token and PIN are required!"
        }), 400

    db = get_db_connection()
    cursor = db.cursor()

    try:

        cursor.execute("""
            SELECT
                GalleryID,
                IsPublished
            FROM Galleries
            WHERE GalleryToken = %s
            AND PIN = %s
        """, (
            gallery_token,
            pin
        ))

        gallery = cursor.fetchone()

        if gallery is None:
            return jsonify({
                "error": "Invalid PIN!"
            }), 401

        if gallery[1] is not True:
            return jsonify({
                "error":
                "Gallery is not published!"
            }), 403

        return jsonify({
            "message":
            "PIN verified successfully!",
            "gallery_id":
            gallery[0]
        })

    finally:

        cursor.close()
        db.close()


# --------------------------------------------------
# CUSTOMER GALLERY PHOTOS
# --------------------------------------------------

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
            WHERE GP.GalleryID = %s
            AND G.IsPublished = TRUE
            AND P.IsSelected = TRUE
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

        print(
            "CUSTOMER GALLERY ERROR:",
            e
        )

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        cursor.close()
        db.close()


# --------------------------------------------------
# LOGOUT
# --------------------------------------------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# --------------------------------------------------
# RUN APP
# --------------------------------------------------

if __name__ == "__main__":

    app.run(
        debug=True
    )