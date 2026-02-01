from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import User
from extensions import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        branch = request.form.get('branch')
        department = request.form.get('department')
        phone = request.form.get('phone')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', 'error')
            return redirect(url_for('auth.register'))
            
        user_by_username = User.query.filter_by(username=username).first()
        if user_by_username:
            flash('Username already exists. Please choose another.', 'error')
            return redirect(url_for('auth.register'))
        
        new_user = User(
            username=username, 
            email=email, 
            password_hash=generate_password_hash(password),
            branch=branch,
            department=department,
            phone=phone
        )
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Account created! Please login.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'error')
            print(f"Error: {e}")
            return redirect(url_for('auth.register'))
        
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid email or password.', 'error')
            
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
