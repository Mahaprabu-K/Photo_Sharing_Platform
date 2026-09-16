# PlatformAI Photo Sharing Platform

A secure photo sharing platform designed for photography and event teams.

The platform allows administrators to create events, manage team members, review and select uploaded photos, and publish secure customer galleries protected by a PIN.

Customers can access their gallery using a shareable link and PIN without creating an account.

---

## Project Status

### Completed Core Features

* Admin authentication
* Team member authentication
* Event management
* Team member assignment
* Multiple photo upload
* Photo selection
* Gallery creation
* Gallery publishing
* PIN-protected customer gallery
* Event deletion
* Cloudinary photo storage
* Customer gallery shareable link

---

## Tech Stack

### Frontend

* HTML5
* CSS3
* JavaScript
* Fetch API

### Backend

* Python
* Flask
* Gunicorn

### Database

* PostgreSQL
* psycopg2

### Cloud Storage

* Cloudinary

### Deployment

* Render

### Development Tools

* Visual Studio Code
* Git
* GitHub

---

## Architecture

The application follows a simple client-server architecture.

```text
Customer / Admin / Team Member
            |
            v
      HTML + CSS + JavaScript
            |
        Fetch API
            |
            v
        Flask Backend
          /       \
         /         \
        v           v
 PostgreSQL     Cloudinary
  Database     Photo Storage
```

---

## Database Design

The application uses PostgreSQL to store users, events, team assignments, photo metadata, and gallery information.

### Main Tables

#### Users

* UserID
* FullName
* Email
* PasswordHash
* Role
* CreatedAt

#### Events

* EventID
* EventName
* Description
* CreatedBy
* CreatedAt

#### EventMembers

* EventMemberID
* EventID
* UserID
* AssignedAt

#### Photos

* PhotoID
* EventID
* UploadedBy
* Filename
* StorageLocation
* Filesize
* CreatedAt
* IsSelected
* CloudinaryPublicID

#### Galleries

* GalleryID
* EventID
* GalleryToken
* PIN
* IsPublished
* PublishedAt
* CreatedAt

#### GalleryPhotos

* GalleryPhotoID
* GalleryID
* PhotoID

---

## Local Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Mahaprabu-K/Photo_Sharing_Platform.git
cd Photo_Sharing_Platform
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

### 3. Activate Virtual Environment

On Windows:

```bash
venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

The main dependencies include:

```text
Flask
psycopg2-binary
Cloudinary
Werkzeug
Gunicorn
```

---

## Environment Configuration

The application uses environment variables for database and Cloudinary configuration.

Configure the following values:

```text
DATABASE_URL
CLOUDINARY_CLOUD_NAME
CLOUDINARY_API_KEY
CLOUDINARY_API_SECRET
```

Do not commit passwords, database credentials, API keys, API secrets, or other sensitive information to GitHub.

---

## Run the Application

Start the Flask application:

```bash
python app.py
```

Open the application in your browser:

```text
http://127.0.0.1:5000
```

---

## Security

The application implements authentication, role-based authorization, and PIN-protected customer galleries.

### Authentication

* User passwords are stored using password hashing.
* Login sessions are maintained using Flask sessions.
* Protected pages require authentication.
* Admin and Team Member accounts use role-based access.

### Authorization

* Admin-only features are restricted to Admin users.
* Team Members cannot create or publish customer galleries.
* Team Members can access only events assigned to them.
* Admins can manage events and team members.

### Gallery Security

* Customer galleries do not require an account.
* Each gallery has a unique Gallery Token.
* Published galleries require a PIN.
* Incorrect PIN attempts are rejected.
* Unpublished galleries cannot be accessed through the customer gallery flow.

### File Upload Security

Supported image formats:

* JPG
* JPEG
* PNG
* WEBP

Uploaded photos are stored in Cloudinary, while photo metadata is stored in PostgreSQL.

### Secrets

API keys, passwords, database credentials, Flask secret keys, and other sensitive values must be stored securely as environment variables.

---

## Testing

The following functional scenarios were tested during development.

### Authentication

* Admin login
* Team Member login
* Logout
* Protected page access
* Session-based authentication

### Authorization

* Team Members cannot access Admin features.
* Team Members cannot create customer galleries.
* Team Members can access only their assigned events.

### Photo Management

* Multiple image uploads
* Supported image format validation
* Photo selection by Admin
* Cloudinary photo storage
* Customer can view only selected gallery photos

### Gallery

* Gallery creation
* Gallery publishing
* Gallery token generation
* Incorrect PIN rejection
* Correct PIN verification
* Published gallery photo access
* Customer gallery shareable link

### Event Management

* Event creation
* Event validation
* Event deletion
* Associated photo and gallery records handling

---

## Features

### Admin

* Register and login
* Create photography events
* Delete events
* Manage team members
* Assign team members to events
* View uploaded event photos
* Select photos
* Create customer galleries
* Set gallery PIN
* Publish galleries
* Generate shareable gallery links

### Team Member

* Login securely
* View assigned events
* Upload multiple photos
* Access assigned event uploads

### Customer

* Open gallery using a shareable link
* Enter gallery PIN
* View published photos
* No account required

---

## Deployment

The application is deployed using Render.

### Deployment Components

* Flask Web Service
* PostgreSQL Database
* Cloudinary for photo storage
* Gunicorn production server
* Environment variables for configuration
* HTTPS through Render

### Production Configuration

Before deployment:

1. Configure the Render PostgreSQL database.
2. Configure Cloudinary credentials.
3. Add environment variables to the Render Web Service.
4. Configure a secure Flask secret key.
5. Use Gunicorn as the production WSGI server.
6. Configure the production database connection.
7. Deploy the application through GitHub.

### Render Start Command

```bash
gunicorn app:app
```

---

## Live Demo

Live application:

https://photo-sharing-platform-nkcg.onrender.com

> The live URL may change if the Render service is renamed or recreated.

---

## Repository

GitHub Repository:

https://github.com/Mahaprabu-K/Photo_Sharing_Platform

---

## Known Limitations

* The current application is designed primarily as a demonstration and educational project.
* Cloud deployment configuration may vary depending on the hosting provider.
* Gallery expiration is not currently implemented.
* Advanced CDN optimization is not currently implemented.
* Additional production features such as email notifications and advanced gallery management may be added in future versions.

---

## Demo Credentials

### Admin

```text
Email: demo-admin@example.com
Password: <demo-password>
```

### Team Member

```text
Email: demo-team@example.com
Password: <demo-password>
```

### Customer Gallery

```text
Gallery URL: <demo-gallery-url>
Access PIN: <demo-gallery-pin>
```

> Demo credentials should be used only for testing and demonstration.

> Never commit real passwords, API keys, database credentials, Cloudinary secrets, or other sensitive information to GitHub.

---

## Project Purpose

This project was developed as part of the **TrizenAI Full Stack Internship Challenge**.

The project demonstrates full-stack development using Flask, PostgreSQL, JavaScript Fetch API, Cloudinary, authentication, role-based authorization, photo management, and secure customer gallery sharing.

---

## License

This project is intended for educational and demonstration purposes.
