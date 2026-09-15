# PlatformAI Photo Sharing Platform

A secure photo sharing platform designed for photography and event teams.

The platform allows administrators to create events, manage team members,
review and select uploaded photos, and publish secure customer galleries
protected by a PIN.

Customers can access their gallery using a shareable link and PIN without
creating an account.

## Project Status

Completed core features:
- Admin authentication
- Team member authentication
- Event management
- Team member assignment
- Photo upload
- Photo selection
- Gallery creation
- Gallery publishing
- PIN protected customer gallery
- Event deletion
- Cloudinary photo storage

## Tech Stack

### Frontend
- HTML5
- CSS3
- JavaScript
- Fetch API

### Backend
- Python
- Flask

### Database
- Microsoft SQL Server
- PyODBC

### Cloud Storage
- Cloudinary

### Development Tools
- Visual Studio Code
- Git / GitHub

## Architecture

The application follows a simple client-server architecture.

Customer / Admin / Team Member
            |
            v
      HTML + CSS + JavaScript
            |
        Fetch API
            |
            v
        Flask Backend
            |
       +----+----+
       |         |
       v         v
 SQL Server   Cloudinary
  Database    Photo Storage



## Database Design

The application uses Microsoft SQL Server for storing user,
event, photo, team assignment, and gallery information.

### Main Tables

- Users
  - UserID
  - FullName
  - Email
  - PasswordHash
  - Role
  - CreatedAt

- Events
  - EventID
  - EventName
  - Description
  - CreatedBy
  - CreatedAt

- EventMembers
  - EventMemberID
  - EventID
  - UserID
  - AssignedAt

- Photos
  - PhotoID
  - EventID
  - UploadedBy
  - Filename
  - StorageLocation
  - FileSize
  - CloudinaryPublicID
  - CreatedAt
  - IsSelected

- Galleries
  - GalleryID
  - EventID
  - GalleryToken
  - PIN
  - IsPublished
  - PublishedAt
  - CreatedAt

- GalleryPhotos
  - GalleryPhotoID
  - GalleryID
  - PhotoID

## Local Setup

### 1. Clone the Repository


git clone <your-github-repository-url>
cd PlatformAI

## Create Virtual Environment 

python -m venv venv

## Activate Virtual Environment

venv\Scripts\activate

## Install Dependencies

pip install flask pyodbc werkzeug cloudinary

## Configure Environment

Configure the following values in the project configuration:

SQL Server connection
Cloudinary Cloud Name
Cloudinary API Key
Cloudinary API Secret

Do not commit passwords, API secrets, or other sensitive credentials to GitHub.

# Run The Application 

python app.py

Open the application in your browser:

http://127.0.0.1:5000

 **Important:** `<your-github-repository-url>` இடத்தில் உங்க actual GitHub URL-ஐ later replace பண்ணலாம்.


 ## Security

The application implements role-based access control and protected
authentication for Admin and Team Member users.

### Authentication
- User passwords are stored using password hashing.
- Login sessions are maintained using Flask sessions.
- Protected pages require authentication.

### Authorization
- Admin-only features are restricted to Admin users.
- Team Members cannot create or publish customer galleries.
- Team Members can access only events assigned to them.
- Admins can manage their own events and team members.

### Gallery Security
- Customer galleries do not require an account.
- Each published gallery is protected by a unique Gallery Token and PIN.
- Incorrect PIN attempts are rejected.
- Unpublished galleries cannot be accessed even with the correct PIN.

### File Upload Security
- Only supported image formats are accepted:
  JPG, JPEG, PNG, and WEBP.
- Uploaded files are stored in Cloudinary rather than directly in the database.
- File metadata is stored in SQL Server.

### Secrets
API keys, passwords, database credentials, and other sensitive values
must not be committed to the source repository.

## Testing

The following functional and security scenarios were tested:

### Authentication
- Admin login tested successfully.
- Team Member login tested successfully.
- Logout tested successfully.
- Protected pages redirect unauthenticated users to the login page.

### Authorization
- Team Members cannot access Admin dashboard.
- Team Members cannot create galleries.
- Team Members cannot access photos from unauthorized events.

### Photo Management
- Multiple image uploads tested successfully.
- Unsupported file types are rejected.
- Admin photo selection tested successfully.
- Customer can view only selected gallery photos.

### Gallery
- Gallery creation tested successfully.
- Gallery publishing tested successfully.
- Incorrect PIN is rejected.
- Unpublished gallery access is blocked.
- Correct PIN allows access to published gallery photos.

### Event Management
- Event creation tested successfully.
- Duplicate event validation tested successfully.
- Event deletion tested successfully.
- Associated Cloudinary photos are deleted when an event is deleted.

## Features

### Admin
- Register and login
- Create and delete photography events
- Manage team members
- Assign team members to events
- View uploaded event photos
- Select photos for publishing
- Create customer galleries
- Set gallery PIN
- Publish galleries
- Generate shareable gallery links

### Team Member
- Login securely
- View assigned events
- Upload multiple photos
- Access only assigned event uploads

### Customer
- Access gallery using a shareable link
- Verify gallery using PIN
- View published photos
- No account required

## Deployment

The application can be deployed to a cloud hosting platform that supports
Python and Flask applications.

### Deployment Requirements

- Python runtime
- Flask application server
- Microsoft SQL Server database
- Cloudinary account for image storage
- Environment variables for sensitive configuration

### Production Configuration

Before deployment:

1. Configure the production SQL Server connection.
2. Configure Cloudinary credentials.
3. Store sensitive credentials securely as environment variables.
4. Set a secure Flask secret key.
5. Use a production WSGI server such as Gunicorn.
6. Configure HTTPS for secure communication.

### Known Limitations

- The current application is designed as a demonstration project.
- Cloud deployment configuration may vary depending on the hosting provider.
- Advanced features such as photo download, gallery expiration, and CDN
  optimization are not currently implemented.