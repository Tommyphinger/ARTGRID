from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask_mail import Mail, Message
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
from pathlib import Path
import hashlib
import re
from functools import wraps
import cloudinary
import cloudinary.uploader
from PIL import Image
import io
from sqlalchemy import text
from sqlalchemy import CheckConstraint

# ---------------------------------------------------------------------------
# 1. CORE CONFIG
# ---------------------------------------------------------------------------
app = Flask(__name__, static_folder="Frontend/dist", static_url_path="/")

# Database
BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "db"
DB_DIR.mkdir(parents=True, exist_ok=True)   #If ./db is missing, create it
DB_PATH = DB_DIR / "artgrid.db"

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH.as_posix()}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "jwt-secret-change-me")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=7)
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB

# Email
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")

# Cloudinary
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
)

# ---------------------------------------------------------------------------
# 2. EXTENSIONS
# ---------------------------------------------------------------------------
db = SQLAlchemy(app)
jwt = JWTManager(app)
mail = Mail(app)
CORS(app)
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# ---------------------------------------------------------------------------
# 2.1. DATABASE SETTINGS (SQLite PRAGMAs)
# ---------------------------------------------------------------------------
with app.app_context():
    if db.engine.url.drivername.startswith("sqlite"):
        with db.engine.begin() as conn:
            conn.execute(text("PRAGMA journal_mode=WAL;"))
            conn.execute(text("PRAGMA synchronous=NORMAL;"))
            conn.execute(text("PRAGMA foreign_keys=ON;"))

# ---------------------------------------------------------------------------
# 3. MODELS
# ---------------------------------------------------------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    dob_hash = db.Column(db.String(255), nullable=False)
    student_id = db.Column(db.String(50), unique=True, nullable=False)
    year_of_study = db.Column(db.String(20), nullable=False)
    profile_image_url = db.Column(db.String(255))
    verification_status = db.Column(db.String(20), default="pending")
    role = db.Column(db.String(20), default="student")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.Index("idx_user_role", "role"),
        db.Index("idx_user_verification", "verification_status"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "student_id": self.student_id,
            "year_of_study": self.year_of_study,
            "profile_image_url": self.profile_image_url,
            "verification_status": self.verification_status,
            "role": self.role,
            "created_at": self.created_at.replace(microsecond=0).isoformat() if self.created_at else None
        }

    artworks = db.relationship("Artwork", backref="artist", lazy=True, cascade="all, delete-orphan")
    likes = db.relationship("Like", backref="user", lazy=True, cascade="all, delete-orphan")
    comments = db.relationship("Comment", backref="user", lazy=True, cascade="all, delete-orphan")

class Artwork(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    status = db.Column(db.String(20), default="pending", nullable=False)  # pending / approved / rejected
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    medium = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    file_url = db.Column(db.String(255), nullable=False)
    thumbnail_url = db.Column(db.String(255))
    tags = db.Column(db.String(255))
    creation_date = db.Column(db.Date)
    submission_date = db.Column(db.DateTime, default=datetime.utcnow)
    approval_date = db.Column(db.DateTime)
    likes_count = db.Column(db.Integer, default=0)
    views_count = db.Column(db.Integer, default=0)
    is_featured = db.Column(db.Boolean, default=False)

    __table_args__ = (
        db.Index('idx_artwork_status', "status"),
        db.Index('idx_artwork_user', "user_id"),
        
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')",
            name="ck_artwork_status_valid"
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "description": self.description,
            "medium": self.medium,
            "category": self.category,
            "file_url": self.file_url,
            "thumbnail_url": self.thumbnail_url,
            "tags": self.tags,
            "creation_date": self.creation_date.replace(microsecond=0).isoformat() if self.creation_date else None,
            "status": self.status,
            "submission_date": self.submission_date.isoformat() if self.submission_date else None,
            "approval_date": self.approval_date.isoformat() if self.approval_date else None,
            "likes_count": self.likes_count,
            "views_count": self.views_count,
            "is_featured": self.is_featured
        }

    likes = db.relationship("Like", backref="artwork", lazy=True, cascade="all, delete-orphan")
    comments = db.relationship("Comment", backref="artwork", lazy=True, cascade="all, delete-orphan")
    moderations = db.relationship("Moderation", backref="artwork", lazy=True, cascade="all, delete-orphan")

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    artwork_id = db.Column(db.Integer, db.ForeignKey("artwork.id"), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint("user_id", "artwork_id"),)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "artwork_id": self.artwork_id,
            "timestamp": self.timestamp.replace(microsecond=0).isoformat() if self.timestamp else None
        }

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    artwork_id = db.Column(db.Integer, db.ForeignKey("artwork.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_flagged = db.Column(db.Boolean, default=False)

    __table_args__ = (
        db.Index('idx_comment_artwork', "artwork_id"),
        db.Index('idx_comment_user', "user_id"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "artwork_id": self.artwork_id,
            "content": self.content,
            "timestamp": self.timestamp.replace(microsecond=0).isoformat() if self.timestamp else None,
            "is_flagged": self.is_flagged
        }

class Moderation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    artwork_id = db.Column(db.Integer, db.ForeignKey("artwork.id"), nullable=False)
    moderator_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    action = db.Column(db.String(20), nullable=False)  # approved / rejected
    feedback = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    moderator = db.relationship("User", foreign_keys=[moderator_id])

    __table_args__ = (
        db.Index("idx_moderation_artwork", "artwork_id"),
        db.Index("idx_moderation_moderator", "moderator_id"),
        db.Index("idx_moderation_action", "action"),   # opcional
    )

    def to_dict(self):
        return {
            "id": self.id,
            "artwork_id": self.artwork_id,
            "moderator_id": self.moderator_id,
            "action": self.action,
            "feedback": self.feedback,
            "timestamp": self.timestamp.replace(microsecond=0).isoformat() if self.timestamp else None
        }

# ---------------------------------------------------------------------------
# 4. UTILITIES
# ---------------------------------------------------------------------------
def validate_uopeople_email(email):
    return bool(re.match(r"^[a-zA-Z0-9._%+-]+@my\.uopeople\.edu$", email))

def hash_dob(dob):
    return hashlib.sha256(dob.encode()).hexdigest()

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in {"png", "jpg", "jpeg", "gif", "mp4"}

def upload_to_cloudinary(file):
    try:
        return cloudinary.uploader.upload(file)["secure_url"]
    except Exception as e:
        print("Cloudinary upload error:", e)
        return None

def send_email(to, subject, body):
    try:
        msg = Message(subject, recipients=[to], body=body, sender=app.config["MAIL_USERNAME"])
        mail.send(msg)
        return True
    except Exception as e:
        print("Email error:", e)
        return False

def moderator_required(f):
    @wraps(f)
    @jwt_required()
    def decorated(*args, **kwargs):
        user = User.query.get(get_jwt_identity())
        if not user or user.role not in {"moderator", "admin"}:
            return jsonify({"error": "Moderator access required"}), 403
        return f(*args, **kwargs)
    return decorated

# ---------------------------------------------------------------------------
# 5. SERVE FRONT-END (SPA catch-all)
# ---------------------------------------------------------------------------
@app.route("/api/", defaults={"path": ""})  # Mute /api 404 noise
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def spa(path):
    if path.startswith("api/"):
        return jsonify({"error": "Not found"}), 404
    full_path = os.path.join(app.static_folder, path)
    if path and os.path.isfile(full_path):
        response = send_from_directory(app.static_folder, path)
        if ".cache." in path or "-Czx" in path or path.endswith((".js", ".css")):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return response
    return send_from_directory(app.static_folder, "index.html")

# ---------------------------------------------------------------------------
# 6. HEALTH CHECK
# ---------------------------------------------------------------------------
@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "utc": datetime.utcnow().isoformat()})

# ---------------------------------------------------------------------------
# 6.1 DATASET SUMMARY (Admin Health)
# ---------------------------------------------------------------------------
@app.get("/api/admin/dataset/summary")
def dataset_summary():
    total = db.session.query(db.func.count(Artwork.id)).scalar()

    approved = db.session.query(db.func.count(Artwork.id))\
        .filter(Artwork.status == "approved").scalar()

    pending = db.session.query(db.func.count(Artwork.id))\
        .filter(Artwork.status == "pending").scalar()

    rejected = db.session.query(db.func.count(Artwork.id))\
        .filter(Artwork.status == "rejected").scalar()

    return jsonify({
        "total": total,
        "approved": approved,
        "pending": pending,
        "rejected": rejected
    })

# ---------------------------------------------------------------------------
# 7. AUTH ROUTES
# ---------------------------------------------------------------------------
@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json()
    required = {"full_name", "email", "password", "dob", "student_id", "year_of_study"}
    missing = required - set(data.keys())
    if missing:
        return jsonify({"error": f"{', '.join(missing)} required"}), 400
    if not validate_uopeople_email(data["email"]):
        return jsonify({"error": "Must use UoPeople email"}), 400
    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already registered"}), 400
    if User.query.filter_by(student_id=data["student_id"]).first():
        return jsonify({"error": "Student ID already registered"}), 400

    user = User(
        full_name=data["full_name"],
        email=data["email"],
        password_hash=generate_password_hash(data["password"]),
        dob_hash=hash_dob(data["dob"]),
        student_id=data["student_id"],
        year_of_study=data["year_of_study"],
        verification_status="verified" if validate_uopeople_email(data["email"]) else "pending",
    )
    db.session.add(user)
    db.session.commit()
    send_email(
        user.email,
        "Welcome to ARTGRID",
        f"Hello {user.full_name},\n\nYour account is ready – start showcasing your art!\n\n– ARTGRID Team",
    )
    return jsonify({"message": "Registration successful", "user_id": user.id}), 201

@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email and password required"}), 400
    user = User.query.filter_by(email=data["email"]).first()
    if user and check_password_hash(user.password_hash, data["password"]):
        token = create_access_token(identity=user.id)
        return jsonify(
            access_token=token,
            user={
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "role": user.role,
                "verification_status": user.verification_status,
            }
        )
    return jsonify({"error": "Invalid credentials"}), 401

@app.route("/api/auth/profile", methods=["GET"])
@jwt_required()
def get_profile():
    user = User.query.get_or_404(get_jwt_identity())
    return jsonify(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        student_id=user.student_id,
        year_of_study=user.year_of_study,
        profile_image_url=user.profile_image_url,
        verification_status=user.verification_status,
        role=user.role,
        created_at=user.created_at.isoformat(),
    )

@app.route("/api/auth/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    user = User.query.get_or_404(get_jwt_identity())
    data = request.get_json()
    if "full_name" in data:
        user.full_name = data["full_name"]
    if "year_of_study" in data:
        user.year_of_study = data["year_of_study"]
    db.session.commit()
    return jsonify({"message": "Profile updated"}), 200

# ---------------------------------------------------------------------------
# 8. ARTWORK ROUTES
# ---------------------------------------------------------------------------
@app.route("/api/artworks", methods=["GET"])
def list_artworks():
    try:
        page     = int(request.args.get("page", 1))
        per_page = min(int(request.args.get("per_page", 24)), 100)  # límite máximo
    except ValueError:
        page, per_page = 1, 24

    q = Artwork.query.order_by(Artwork.submission_date.desc())
    items = q.limit(per_page).offset((page-1) * per_page).all()
    total = db.session.query(db.func.count(Artwork.id)).scalar()

    return jsonify({
        "page": page,
        "per_page": per_page,
        "total": total,
        "items": [a.to_dict() for a in items]  # necesitas método to_dict en Artwork
    })

@app.route("/api/artworks/upload", methods=["POST"])
@jwt_required()
def upload_artwork():
    user = User.query.get_or_404(get_jwt_identity())
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed"}), 400

    title = request.form.get("title")
    description = request.form.get("description", "")
    medium = request.form.get("medium")
    category = request.form.get("category")
    tags = request.form.get("tags", "")
    creation_date = request.form.get("creation_date")

    if not all([title, medium, category]):
        return jsonify({"error": "Title, medium, category required"}), 400

    file_url = upload_to_cloudinary(file)
    if not file_url:
        return jsonify({"error": "Upload failed"}), 500

    creation_date_obj = None
    if creation_date:
        try:
            creation_date_obj = datetime.strptime(creation_date, "%Y-%m-%d").date()
        except ValueError:
            pass

    artwork = Artwork(
        user_id=user.id,
        title=title,
        description=description,
        medium=medium,
        category=category,
        file_url=file_url,
        thumbnail_url=file_url,
        tags=tags,
        creation_date=creation_date_obj,
        status="approved" if user.verification_status == "verified" else "pending",
    )
    db.session.add(artwork)
    db.session.commit()

    send_email(
        user.email,
        "Artwork submitted – ARTGRID",
        f'Hello {user.full_name},\n\nYour artwork "{title}" has been submitted and is under review.\n\n– ARTGRID Team',
    )
    return jsonify({"message": "Artwork uploaded", "artwork_id": artwork.id, "status": artwork.status}), 201

@app.route("/api/artworks", methods=["GET"])
def get_artworks():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 12, type=int)
    category = request.args.get("category")
    medium = request.args.get("medium")
    featured = request.args.get("featured", type=bool)

    query = Artwork.query.filter_by(status="approved")
    if category:
        query = query.filter_by(category=category)
    if medium:
        query = query.filter_by(medium=medium)
    if featured:
        query = query.filter_by(is_featured=True)

    arts = query.order_by(Artwork.submission_date.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify(
        artworks=[
            {
                "id": art.id,
                "title": art.title,
                "description": art.description,
                "medium": art.medium,
                "category": art.category,
                "file_url": art.file_url,
                "thumbnail_url": art.thumbnail_url,
                "tags": art.tags,
                "creation_date": art.creation_date.isoformat() if art.creation_date else None,
                "submission_date": art.submission_date.isoformat(),
                "likes_count": art.likes_count,
                "views_count": art.views_count,
                "is_featured": art.is_featured,
                "artist": {
                    "id": art.artist.id,
                    "full_name": art.artist.full_name,
                    "year_of_study": art.artist.year_of_study,
                },
            }
            for art in arts.items
        ],
        pagination={
            "page": arts.page,
            "pages": arts.pages,
            "per_page": arts.per_page,
            "total": arts.total,
            "has_next": arts.has_next,
            "has_prev": arts.has_prev,
        },
    )

@app.route("/api/artworks/<int:artwork_id>", methods=["GET"])
def get_artwork(artwork_id):
    artwork = Artwork.query.get_or_404(artwork_id)
    if artwork.status != "approved":
        return jsonify({"error": "Artwork not found"}), 404
    artwork.views_count += 1
    db.session.commit()
    return jsonify(
        id=artwork.id,
        title=artwork.title,
        description=artwork.description,
        medium=artwork.medium,
        category=artwork.category,
        file_url=artwork.file_url,
        thumbnail_url=artwork.thumbnail_url,
        tags=artwork.tags,
        creation_date=artwork.creation_date.isoformat() if artwork.creation_date else None,
        submission_date=artwork.submission_date.isoformat(),
        likes_count=artwork.likes_count,
        views_count=artwork.views_count,
        is_featured=artwork.is_featured,
        artist={
            "id": artwork.artist.id,
            "full_name": artwork.artist.full_name,
            "year_of_study": artwork.artist.year_of_study,
            "profile_image_url": artwork.artist.profile_image_url,
        },
    )

@app.route("/api/artworks/<int:artwork_id>/like", methods=["POST"])
@jwt_required()
def toggle_like(artwork_id):
    user_id = get_jwt_identity()
    artwork = Artwork.query.get_or_404(artwork_id)
    if artwork.status != "approved":
        return jsonify({"error": "Artwork not found"}), 404

    like = Like.query.filter_by(user_id=user_id, artwork_id=artwork_id).first()
    if like:
        db.session.delete(like)
        artwork.likes_count = max(0, artwork.likes_count - 1)
        liked = False
    else:
        db.session.add(Like(user_id=user_id, artwork_id=artwork_id))
        artwork.likes_count += 1
        liked = True
    db.session.commit()
    return jsonify({"liked": liked, "likes_count": artwork.likes_count})

@app.route("/api/artworks/categories", methods=["GET"])
def categories():
    return jsonify(
        categories=[
            "Digital Art",
            "Painting",
            "Drawing",
            "Photography",
            "Sculpture",
            "Printmaking",
            "Mixed Media",
            "Other",
        ],
        mediums=[
            "Digital Art",
            "Oil Paint",
            "Acrylic Paint",
            "Watercolor",
            "Pencil",
            "Charcoal",
            "Photography",
            "Clay",
            "Mixed Media",
            "Other",
        ],
    )




# ---------------------------------------------------------------------------
# 9. COMMENTS
# ---------------------------------------------------------------------------
@app.route("/api/comments/<int:artwork_id>", methods=["GET"])
def get_comments(artwork_id):
    artwork = Artwork.query.get_or_404(artwork_id)
    if artwork.status != "approved":
        return jsonify({"error": "Artwork not found"}), 404
    comments = Comment.query.filter_by(artwork_id=artwork_id, is_flagged=False).order_by(Comment.timestamp.desc()).all()
    return jsonify(
        comments=[
            {
                "id": c.id,
                "content": c.content,
                "timestamp": c.timestamp.isoformat(),
                "user": {"id": c.user.id, "full_name": c.user.full_name},
            }
            for c in comments
        ]
    )

@app.route("/api/comments", methods=["POST"])
@jwt_required()
def add_comment():
    data = request.get_json()
    artwork_id = data.get("artwork_id")
    content = data.get("content")
    if not artwork_id or not content:
        return jsonify({"error": "Artwork ID and content required"}), 400

    artwork = Artwork.query.get_or_404(artwork_id)
    if artwork.status != "approved":
        return jsonify({"error": "Artwork not found"}), 404

    is_flagged = any(w in content.lower() for w in ["spam", "inappropriate"])
    comment = Comment(user_id=get_jwt_identity(), artwork_id=artwork_id, content=content, is_flagged=is_flagged)
    db.session.add(comment)
    db.session.commit()
    return jsonify(
        id=comment.id,
        content=comment.content,
        timestamp=comment.timestamp.isoformat(),
        user={"id": comment.user.id, "full_name": comment.user.full_name},
    ), 201

# ---------------------------------------------------------------------------
# 10. USER GALLERY
# ---------------------------------------------------------------------------
@app.route("/api/users/<int:user_id>/gallery", methods=["GET"])
def user_gallery(user_id):
    user = User.query.get_or_404(user_id)
    arts = Artwork.query.filter_by(user_id=user_id, status="approved").order_by(Artwork.submission_date.desc()).all()
    return jsonify(
        user={
            "id": user.id,
            "full_name": user.full_name,
            "year_of_study": user.year_of_study,
            "profile_image_url": user.profile_image_url,
        },
        artworks=[
            {
                "id": art.id,
                "title": art.title,
                "description": art.description,
                "medium": art.medium,
                "category": art.category,
                "file_url": art.file_url,
                "thumbnail_url": art.thumbnail_url,
                "submission_date": art.submission_date.isoformat(),
                "likes_count": art.likes_count,
                "views_count": art.views_count,
                "is_featured": art.is_featured,
            }
            for art in arts
        ],
    )

# ---------------------------------------------------------------------------
# 11. MODERATION
# ---------------------------------------------------------------------------
@app.route("/api/admin/queue", methods=["GET"])
@moderator_required
def mod_queue():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    pending = Artwork.query.filter_by(status="pending").order_by(Artwork.submission_date.asc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify(
        artworks=[
            {
                "id": art.id,
                "title": art.title,
                "description": art.description,
                "medium": art.medium,
                "category": art.category,
                "file_url": art.file_url,
                "submission_date": art.submission_date.isoformat(),
                "artist": {
                    "id": art.artist.id,
                    "full_name": art.artist.full_name,
                    "email": art.artist.email,
                    "year_of_study": art.artist.year_of_study,
                    "verification_status": art.artist.verification_status,
                },
            }
            for art in pending.items
        ],
        pagination={
            "page": pending.page,
            "pages": pending.pages,
            "per_page": pending.per_page,
            "total": pending.total,
            "has_next": pending.has_next,
            "has_prev": pending.has_prev,
        },
    )

@app.route("/api/admin/approve/<int:artwork_id>", methods=["PUT"])
@moderator_required
def approve(artwork_id):
    mod_id = get_jwt_identity()
    art = Artwork.query.get_or_404(artwork_id)
    if art.status != "pending":
        return jsonify({"error": "Not pending"}), 400
    art.status = "approved"
    art.approval_date = datetime.utcnow()
    db.session.add(Moderation(artwork_id=artwork_id, moderator_id=mod_id, action="approved"))
    db.session.commit()
    send_email(
        art.artist.email,
        "Artwork approved – ARTGRID",
        f'Hello {art.artist.full_name},\n\nYour artwork "{art.title}" is now live!\n\n– ARTGRID Team',
    )
    return jsonify({"message": "Approved"})

@app.route("/api/admin/reject/<int:artwork_id>", methods=["PUT"])
@moderator_required
def reject(artwork_id):
    mod_id = get_jwt_identity()
    art = Artwork.query.get_or_404(artwork_id)
    if art.status != "pending":
        return jsonify({"error": "Not pending"}), 400
    feedback = request.get_json().get("feedback", "")
    art.status = "rejected"
    db.session.add(Moderation(artwork_id=artwork_id, moderator_id=mod_id, action="rejected", feedback=feedback))
    db.session.commit()
    send_email(
        art.artist.email,
        "Artwork update – ARTGRID",
        f'Hello {art.artist.full_name},\n\nYour artwork "{art.title}" needs changes:\n{feedback}\n\n– ARTGRID Team',
    )
    return jsonify({"message": "Rejected"})

@app.route("/api/admin/feature/<int:artwork_id>", methods=["POST"])
@moderator_required
def feature_toggle(artwork_id):
    art = Artwork.query.get_or_404(artwork_id)
    if art.status != "approved":
        return jsonify({"error": "Only approved artworks can be featured"}), 400
    art.is_featured = not art.is_featured
    db.session.commit()
    action = "featured" if art.is_featured else "unfeatured"
    return jsonify({"message": f"Artwork {action}", "is_featured": art.is_featured})

@app.route("/api/admin/stats", methods=["GET"])
@moderator_required
def admin_stats():
    total_users = User.query.count()
    artworks = Artwork.query
    approved = artworks.filter_by(status="approved").count()
    pending = artworks.filter_by(status="pending").count()
    rejected = artworks.filter_by(status="rejected").count()
    featured = artworks.filter_by(is_featured=True).count()

    year_stats = db.session.query(User.year_of_study, db.func.count(Artwork.id).label("count")).join(Artwork).filter(Artwork.status == "approved").group_by(User.year_of_study).all()
    cat_stats = db.session.query(Artwork.category, db.func.count(Artwork.id).label("count")).filter(Artwork.status == "approved").group_by(Artwork.category).all()
    top = artworks.filter_by(status="approved").order_by(Artwork.likes_count.desc()).limit(10).all()

    return jsonify(
        overview={
            "total_users": total_users,
            "total_artworks": artworks.count(),
            "pending_artworks": pending,
            "approved_artworks": approved,
            "rejected_artworks": rejected,
            "featured_artworks": featured,
        },
        year_stats=[{"year": y, "count": c} for y, c in year_stats],
        category_stats=[{"category": cat, "count": c} for cat, c in cat_stats],
        top_artworks=[
            {
                "id": art.id,
                "title": art.title,
                "likes_count": art.likes_count,
                "views_count": art.views_count,
                "artist_name": art.artist.full_name,
            }
            for art in top
        ],
    )

# ---------------------------------------------------------------------------
# 12. DB BOOTSTRAP
# ---------------------------------------------------------------------------
def seed_db():
    """Create tables + default admin if missing."""
    db.create_all()
    if not User.query.filter_by(email="admin@my.uopeople.edu").first():
        admin = User(
            full_name="ARTGRID Admin",
            email="admin@my.uopeople.edu",
            password_hash=generate_password_hash("admin123"),
            dob_hash=hash_dob("1990-01-01"),
            student_id="ADMIN001",
            year_of_study="Graduate",
            role="admin",
            verification_status="verified",
        )
        db.session.add(admin)
        db.session.commit()

with app.app_context():
    seed_db()

# ---------------------------------------------------------------------------
# 13. ERROR HANDLERS
# ---------------------------------------------------------------------------
@app.errorhandler(404)
def not_found(_):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Resource not found"}), 404
    return send_from_directory(app.static_folder, "index.html")

@app.errorhandler(500)
def internal(_):
    return jsonify({"error": "Internal server error"}), 500

# ---------------------------------------------------------------------------
# 14. LOCAL ENTRY-POINT
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))