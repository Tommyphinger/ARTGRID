from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask_mail import Mail, Message
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import hashlib
import re
from functools import wraps
import cloudinary
import cloudinary.uploader
from PIL import Image
import io

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'artgrid-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///artgrid.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')

# Cloudinary configuration
cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET')
)

# Initialize extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)
mail = Mail(app)
CORS(app)

# Create upload directory
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    dob_hash = db.Column(db.String(255), nullable=False)
    student_id = db.Column(db.String(50), unique=True, nullable=False)
    year_of_study = db.Column(db.String(20), nullable=False)
    profile_image_url = db.Column(db.String(255))
    verification_status = db.Column(db.String(20), default='pending')
    role = db.Column(db.String(20), default='student')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    artworks = db.relationship('Artwork', backref='artist', lazy=True, cascade='all, delete-orphan')
    likes = db.relationship('Like', backref='user', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='user', lazy=True, cascade='all, delete-orphan')

class Artwork(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    medium = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    file_url = db.Column(db.String(255), nullable=False)
    thumbnail_url = db.Column(db.String(255))
    tags = db.Column(db.String(255))
    creation_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='pending')
    submission_date = db.Column(db.DateTime, default=datetime.utcnow)
    approval_date = db.Column(db.DateTime)
    likes_count = db.Column(db.Integer, default=0)
    views_count = db.Column(db.Integer, default=0)
    is_featured = db.Column(db.Boolean, default=False)
    
    # Relationships
    likes = db.relationship('Like', backref='artwork', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='artwork', lazy=True, cascade='all, delete-orphan')
    moderations = db.relationship('Moderation', backref='artwork', lazy=True, cascade='all, delete-orphan')

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    artwork_id = db.Column(db.Integer, db.ForeignKey('artwork.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'artwork_id'),)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    artwork_id = db.Column(db.Integer, db.ForeignKey('artwork.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_flagged = db.Column(db.Boolean, default=False)

class Moderation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    artwork_id = db.Column(db.Integer, db.ForeignKey('artwork.id'), nullable=False)
    moderator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(20), nullable=False)  # approved, rejected
    feedback = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    moderator = db.relationship('User', foreign_keys=[moderator_id])

# Utility Functions
def validate_uopeople_email(email):
    """Validate UoPeople email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@my\.uopeople\.edu$'
    return re.match(pattern, email) is not None

def hash_dob(dob):
    """Hash date of birth for privacy"""
    return hashlib.sha256(dob.encode()).hexdigest()

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_to_cloudinary(file):
    """Upload file to Cloudinary"""
    try:
        result = cloudinary.uploader.upload(file)
        return result['secure_url']
    except Exception as e:
        print(f"Cloudinary upload error: {e}")
        return None

def send_email(to, subject, body):
    """Send email notification"""
    try:
        msg = Message(subject, recipients=[to], body=body, sender=app.config['MAIL_USERNAME'])
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

def moderator_required(f):
    """Decorator to require moderator role"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user or user.role not in ['moderator', 'admin']:
            return jsonify({'error': 'Moderator access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# Authentication Routes
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['full_name', 'email', 'password', 'dob', 'student_id', 'year_of_study']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    # Validate UoPeople email
    if not validate_uopeople_email(data['email']):
        return jsonify({'error': 'Must use UoPeople email (@my.uopeople.edu)'}), 400
    
    # Check if user already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400
    
    if User.query.filter_by(student_id=data['student_id']).first():
        return jsonify({'error': 'Student ID already registered'}), 400
    
    # Create new user
    user = User(
        full_name=data['full_name'],
        email=data['email'],
        password_hash=generate_password_hash(data['password']),
        dob_hash=hash_dob(data['dob']),
        student_id=data['student_id'],
        year_of_study=data['year_of_study'],
        verification_status='verified' if validate_uopeople_email(data['email']) else 'pending'
    )
    
    db.session.add(user)
    db.session.commit()
    
    # Send welcome email
    send_email(
        user.email,
        'Welcome to ARTGRID - UoPeople Art Community',
        f'Hello {user.full_name},\n\nWelcome to ARTGRID! Your account has been created successfully.\n\nStart showcasing your artwork today!\n\nBest regards,\nARTGRID Team'
    )
    
    return jsonify({'message': 'Registration successful', 'user_id': user.id}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if user and check_password_hash(user.password_hash, data['password']):
        access_token = create_access_token(identity=user.id)
        return jsonify({
            'access_token': access_token,
            'user': {
                'id': user.id,
                'full_name': user.full_name,
                'email': user.email,
                'role': user.role,
                'verification_status': user.verification_status
            }
        }), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'id': user.id,
        'full_name': user.full_name,
        'email': user.email,
        'student_id': user.student_id,
        'year_of_study': user.year_of_study,
        'profile_image_url': user.profile_image_url,
        'verification_status': user.verification_status,
        'role': user.role,
        'created_at': user.created_at.isoformat()
    }), 200

@app.route('/api/auth/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    # Update allowed fields
    if data.get('full_name'):
        user.full_name = data['full_name']
    if data.get('year_of_study'):
        user.year_of_study = data['year_of_study']
    
    db.session.commit()
    
    return jsonify({'message': 'Profile updated successfully'}), 200

# Artwork Routes
@app.route('/api/artworks/upload', methods=['POST'])
@jwt_required()
def upload_artwork():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if file is present
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
    
    # Get form data
    title = request.form.get('title')
    description = request.form.get('description', '')
    medium = request.form.get('medium')
    category = request.form.get('category')
    tags = request.form.get('tags', '')
    creation_date = request.form.get('creation_date')
    
    if not all([title, medium, category]):
        return jsonify({'error': 'Title, medium, and category are required'}), 400
    
    # Upload to Cloudinary
    file_url = upload_to_cloudinary(file)
    if not file_url:
        return jsonify({'error': 'File upload failed'}), 500
    
    # Parse creation date
    creation_date_obj = None
    if creation_date:
        try:
            creation_date_obj = datetime.strptime(creation_date, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    # Create artwork
    artwork = Artwork(
        user_id=current_user_id,
        title=title,
        description=description,
        medium=medium,
        category=category,
        file_url=file_url,
        thumbnail_url=file_url,  # Cloudinary handles thumbnails
        tags=tags,
        creation_date=creation_date_obj,
        status='approved' if user.verification_status == 'verified' else 'pending'
    )
    
    db.session.add(artwork)
    db.session.commit()
    
    # Send confirmation email
    send_email(
        user.email,
        'Artwork Submitted - ARTGRID',
        f'Hello {user.full_name},\n\nYour artwork "{title}" has been submitted successfully.\n\nStatus: {artwork.status}\n\nThank you for contributing to the UoPeople art community!\n\nBest regards,\nARTGRID Team'
    )
    
    return jsonify({
        'message': 'Artwork uploaded successfully',
        'artwork_id': artwork.id,
        'status': artwork.status
    }), 201

@app.route('/api/artworks', methods=['GET'])
def get_artworks():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    category = request.args.get('category')
    medium = request.args.get('medium')
    featured = request.args.get('featured', type=bool)
    
    query = Artwork.query.filter_by(status='approved')
    
    if category:
        query = query.filter_by(category=category)
    if medium:
        query = query.filter_by(medium=medium)
    if featured:
        query = query.filter_by(is_featured=True)
    
    artworks = query.order_by(Artwork.submission_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'artworks': [{
            'id': artwork.id,
            'title': artwork.title,
            'description': artwork.description,
            'medium': artwork.medium,
            'category': artwork.category,
            'file_url': artwork.file_url,
            'thumbnail_url': artwork.thumbnail_url,
            'tags': artwork.tags,
            'creation_date': artwork.creation_date.isoformat() if artwork.creation_date else None,
            'submission_date': artwork.submission_date.isoformat(),
            'likes_count': artwork.likes_count,
            'views_count': artwork.views_count,
            'is_featured': artwork.is_featured,
            'artist': {
                'id': artwork.artist.id,
                'full_name': artwork.artist.full_name,
                'year_of_study': artwork.artist.year_of_study
            }
        } for artwork in artworks.items],
        'pagination': {
            'page': artworks.page,
            'pages': artworks.pages,
            'per_page': artworks.per_page,
            'total': artworks.total,
            'has_next': artworks.has_next,
            'has_prev': artworks.has_prev
        }
    }), 200

@app.route('/api/artworks/<int:artwork_id>', methods=['GET'])
def get_artwork(artwork_id):
    artwork = Artwork.query.get_or_404(artwork_id)
    
    if artwork.status != 'approved':
        return jsonify({'error': 'Artwork not found'}), 404
    
    # Increment view count
    artwork.views_count += 1
    db.session.commit()
    
    return jsonify({
        'id': artwork.id,
        'title': artwork.title,
        'description': artwork.description,
        'medium': artwork.medium,
        'category': artwork.category,
        'file_url': artwork.file_url,
        'thumbnail_url': artwork.thumbnail_url,
        'tags': artwork.tags,
        'creation_date': artwork.creation_date.isoformat() if artwork.creation_date else None,
        'submission_date': artwork.submission_date.isoformat(),
        'likes_count': artwork.likes_count,
        'views_count': artwork.views_count,
        'is_featured': artwork.is_featured,
        'artist': {
            'id': artwork.artist.id,
            'full_name': artwork.artist.full_name,
            'year_of_study': artwork.artist.year_of_study,
            'profile_image_url': artwork.artist.profile_image_url
        }
    }), 200

@app.route('/api/artworks/<int:artwork_id>/like', methods=['POST'])
@jwt_required()
def toggle_like(artwork_id):
    current_user_id = get_jwt_identity()
    artwork = Artwork.query.get_or_404(artwork_id)
    
    if artwork.status != 'approved':
        return jsonify({'error': 'Artwork not found'}), 404
    
    existing_like = Like.query.filter_by(user_id=current_user_id, artwork_id=artwork_id).first()
    
    if existing_like:
        # Unlike
        db.session.delete(existing_like)
        artwork.likes_count = max(0, artwork.likes_count - 1)
        liked = False
    else:
        # Like
        like = Like(user_id=current_user_id, artwork_id=artwork_id)
        db.session.add(like)
        artwork.likes_count += 1
        liked = True
    
    db.session.commit()
    
    return jsonify({
        'liked': liked,
        'likes_count': artwork.likes_count
    }), 200

@app.route('/api/artworks/categories', methods=['GET'])
def get_categories():
    categories = [
        'Digital Art',
        'Painting',
        'Drawing',
        'Photography',
        'Sculpture',
        'Printmaking',
        'Mixed Media',
        'Other'
    ]
    
    mediums = [
        'Digital Art',
        'Oil Paint',
        'Acrylic Paint',
        'Watercolor',
        'Pencil',
        'Charcoal',
        'Photography',
        'Clay',
        'Mixed Media',
        'Other'
    ]
    
    return jsonify({
        'categories': categories,
        'mediums': mediums
    }), 200

# Moderation Routes
@app.route('/api/admin/queue', methods=['GET'])
@moderator_required
def get_moderation_queue():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    pending_artworks = Artwork.query.filter_by(status='pending').order_by(
        Artwork.submission_date.asc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'artworks': [{
            'id': artwork.id,
            'title': artwork.title,
            'description': artwork.description,
            'medium': artwork.medium,
            'category': artwork.category,
            'file_url': artwork.file_url,
            'submission_date': artwork.submission_date.isoformat(),
            'artist': {
                'id': artwork.artist.id,
                'full_name': artwork.artist.full_name,
                'email': artwork.artist.email,
                'year_of_study': artwork.artist.year_of_study,
                'verification_status': artwork.artist.verification_status
            }
        } for artwork in pending_artworks.items],
        'pagination': {
            'page': pending_artworks.page,
            'pages': pending_artworks.pages,
            'per_page': pending_artworks.per_page,
            'total': pending_artworks.total
        }
    }), 200

@app.route('/api/admin/approve/<int:artwork_id>', methods=['PUT'])
@moderator_required
def approve_artwork(artwork_id):
    current_user_id = get_jwt_identity()
    artwork = Artwork.query.get_or_404(artwork_id)
    
    if artwork.status != 'pending':
        return jsonify({'error': 'Artwork is not pending approval'}), 400
    
    artwork.status = 'approved'
    artwork.approval_date = datetime.utcnow()
    
    # Create moderation record
    moderation = Moderation(
        artwork_id=artwork_id,
        moderator_id=current_user_id,
        action='approved'
    )
    
    db.session.add(moderation)
    db.session.commit()
    
    # Send approval email
    send_email(
        artwork.artist.email,
        'Artwork Approved - ARTGRID',
        f'Hello {artwork.artist.full_name},\n\nGreat news! Your artwork "{artwork.title}" has been approved and is now live on ARTGRID.\n\nView it here: [Your Frontend URL]/artwork/{artwork.id}\n\nThank you for contributing to the UoPeople art community!\n\nBest regards,\nARTGRID Team'
    )
    
    return jsonify({'message': 'Artwork approved successfully'}), 200

@app.route('/api/admin/reject/<int:artwork_id>', methods=['PUT'])
@moderator_required
def reject_artwork(artwork_id):
    current_user_id = get_jwt_identity()
    data = request.get_json()
    feedback = data.get('feedback', '')
    
    artwork = Artwork.query.get_or_404(artwork_id)
    
    if artwork.status != 'pending':
        return jsonify({'error': 'Artwork is not pending approval'}), 400
    
    artwork.status = 'rejected'
    
    # Create moderation record
    moderation = Moderation(
        artwork_id=artwork_id,
        moderator_id=current_user_id,
        action='rejected',
        feedback=feedback
    )
    
    db.session.add(moderation)
    db.session.commit()
    
    # Send rejection email
    send_email(
        artwork.artist.email,
        'Artwork Submission Update - ARTGRID',
        f'Hello {artwork.artist.full_name},\n\nThank you for your submission "{artwork.title}". After review, we need you to make some adjustments before it can be approved.\n\nFeedback: {feedback}\n\nPlease feel free to resubmit your artwork after making the necessary changes.\n\nBest regards,\nARTGRID Team'
    )
    
    return jsonify({'message': 'Artwork rejected successfully'}), 200

@app.route('/api/admin/feature/<int:artwork_id>', methods=['POST'])
@moderator_required
def feature_artwork(artwork_id):
    artwork = Artwork.query.get_or_404(artwork_id)
    
    if artwork.status != 'approved':
        return jsonify({'error': 'Only approved artworks can be featured'}), 400
    
    artwork.is_featured = not artwork.is_featured
    db.session.commit()
    
    action = 'featured' if artwork.is_featured else 'unfeatured'
    
    return jsonify({
        'message': f'Artwork {action} successfully',
        'is_featured': artwork.is_featured
    }), 200

@app.route('/api/admin/stats', methods=['GET'])
@moderator_required
def get_admin_stats():
    total_users = User.query.count()
    total_artworks = Artwork.query.count()
    pending_artworks = Artwork.query.filter_by(status='pending').count()
    approved_artworks = Artwork.query.filter_by(status='approved').count()
    rejected_artworks = Artwork.query.filter_by(status='rejected').count()
    featured_artworks = Artwork.query.filter_by(is_featured=True).count()
    
    # Stats by year of study
    year_stats = db.session.query(
        User.year_of_study,
        db.func.count(Artwork.id).label('artwork_count')
    ).join(Artwork).filter(Artwork.status == 'approved').group_by(User.year_of_study).all()
    
    # Stats by category
    category_stats = db.session.query(
        Artwork.category,
        db.func.count(Artwork.id).label('count')
    ).filter(Artwork.status == 'approved').group_by(Artwork.category).all()
    
    # Top artworks by likes
    top_artworks = Artwork.query.filter_by(status='approved').order_by(
        Artwork.likes_count.desc()
    ).limit(10).all()
    
    return jsonify({
        'overview': {
            'total_users': total_users,
            'total_artworks': total_artworks,
            'pending_artworks': pending_artworks,
            'approved_artworks': approved_artworks,
            'rejected_artworks': rejected_artworks,
            'featured_artworks': featured_artworks
        },
        'year_stats': [{'year': year, 'count': count} for year, count in year_stats],
        'category_stats': [{'category': cat, 'count': count} for cat, count in category_stats],
        'top_artworks': [{
            'id': artwork.id,
            'title': artwork.title,
            'likes_count': artwork.likes_count,
            'views_count': artwork.views_count,
            'artist_name': artwork.artist.full_name
        } for artwork in top_artworks]
    }), 200

# Comment Routes
@app.route('/api/comments', methods=['POST'])
@jwt_required()
def add_comment():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    artwork_id = data.get('artwork_id')
    content = data.get('content')
    
    if not artwork_id or not content:
        return jsonify({'error': 'Artwork ID and content are required'}), 400
    
    artwork = Artwork.query.get_or_404(artwork_id)
    if artwork.status != 'approved':
        return jsonify({'error': 'Artwork not found'}), 404
    
    # Basic profanity filter
    profane_words = ['spam', 'inappropriate']  # Add more words as needed
    is_flagged = any(word in content.lower() for word in profane_words)
    
    comment = Comment(
        user_id=current_user_id,
        artwork_id=artwork_id,
        content=content,
        is_flagged=is_flagged
    )
    
    db.session.add(comment)
    db.session.commit()
    
    return jsonify({
        'id': comment.id,
        'content': comment.content,
        'timestamp': comment.timestamp.isoformat(),
        'user': {
            'id': comment.user.id,
            'full_name': comment.user.full_name
        }
    }), 201

@app.route('/api/comments/<int:artwork_id>', methods=['GET'])
def get_comments(artwork_id):
    artwork = Artwork.query.get_or_404(artwork_id)
    if artwork.status != 'approved':
        return jsonify({'error': 'Artwork not found'}), 404
    
    comments = Comment.query.filter_by(
        artwork_id=artwork_id, is_flagged=False
    ).order_by(Comment.timestamp.desc()).all()
    
    return jsonify({
        'comments': [{
            'id': comment.id,
            'content': comment.content,
            'timestamp': comment.timestamp.isoformat(),
            'user': {
                'id': comment.user.id,
                'full_name': comment.user.full_name
            }
        } for comment in comments]
    }), 200

# User Gallery Route
@app.route('/api/users/<int:user_id>/gallery', methods=['GET'])
def get_user_gallery(user_id):
    user = User.query.get_or_404(user_id)
    
    artworks = Artwork.query.filter_by(
        user_id=user_id, status='approved'
    ).order_by(Artwork.submission_date.desc()).all()
    
    return jsonify({
        'user': {
            'id': user.id,
            'full_name': user.full_name,
            'year_of_study': user.year_of_study,
            'profile_image_url': user.profile_image_url
        },
        'artworks': [{
            'id': artwork.id,
            'title': artwork.title,
            'description': artwork.description,
            'medium': artwork.medium,
            'category': artwork.category,
            'file_url': artwork.file_url,
            'thumbnail_url': artwork.thumbnail_url,
            'submission_date': artwork.submission_date.isoformat(),
            'likes_count': artwork.likes_count,
            'views_count': artwork.views_count,
            'is_featured': artwork.is_featured
        } for artwork in artworks]
    }), 200

# Initialize database
def create_tables():
    db.create_all()
    ...
with app.app_context():
    create_tables()
    
    # Create default admin user if it doesn't exist
    admin = User.query.filter_by(email='admin@my.uopeople.edu').first()
    if not admin:
        admin = User(
            full_name='ARTGRID Admin',
            email='admin@my.uopeople.edu',
            password_hash=generate_password_hash('admin123'),
            dob_hash=hash_dob('1990-01-01'),
            student_id='ADMIN001',
            year_of_study='Graduate',
            role='admin',
            verification_status='verified'
        )
        db.session.add(admin)
        db.session.commit()

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
