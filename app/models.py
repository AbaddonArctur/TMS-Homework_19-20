from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    recipes = db.relationship("Recipe", back_populates="author", cascade="all, delete-orphan")
    comments = db.relationship("Comment", back_populates="author", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Recipe(db.Model):
    __tablename__ = "recipes"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(80))
    description = db.Column(db.Text)
    cooking_time = db.Column(db.String(50))
    ingredients = db.Column(db.Text)
    instructions = db.Column(db.Text)
    image_filename = db.Column(db.String(256))
    thumb_filename = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = db.relationship("User", back_populates="recipes")

    comments = db.relationship("Comment", back_populates="recipe", cascade="all, delete-orphan")

class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    author = db.relationship("User", back_populates="comments")

    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id"), nullable=False)
    recipe = db.relationship("Recipe", back_populates="comments")

    parent_id = db.Column(db.Integer, db.ForeignKey("comments.id"), nullable=True)
    replies = db.relationship("Comment", backref=db.backref("parent", remote_side=[id]), cascade="all, delete-orphan")