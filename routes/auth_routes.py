from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message
from models import User
from extensions import db, mail
import random
import re
import traceback

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        semester = request.form.get('semester')
        department = request.form.get('department')
        phone = request.form.get('phone')

        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&_#-])[A-Za-z\d@$!%*?&_#-]{8,}$', password):
            flash('Password must be at least 8 characters long, contain at least one uppercase letter, one lowercase letter, one number, and one special character.', 'error')
            return redirect(url_for('auth.register'))

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', 'error')
            return redirect(url_for('auth.register'))
            
        user_by_username = User.query.filter_by(username=username).first()
        if user_by_username:
            flash('Username already exists. Please choose another.', 'error')
            return redirect(url_for('auth.register'))
        
        # Generate 6-digit OTP
        otp = str(random.randint(100000, 999999))
        
        # Store data temporarily in session
        session['registration_data'] = {
            'username': username,
            'email': email,
            'password_hash': generate_password_hash(password),
            'semester': semester,
            'department': department,
            'phone': phone,
            'otp': otp
        }
        
        # Localhost OTP Bypass
        # User is unable to configure SMTP, so we ALWAYS flash the OTP directly
        # to the screen for testing instead of attempting to send an email.
        print(f"Localhost Dev OTP for {email}: {otp}")
        flash(f'Your verification code is: {otp}', 'info')
        
        return redirect(url_for('auth.verify_otp'))
        
    return render_template('auth/register.html')

@auth_bp.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    reg_data = session.get('registration_data')
    if not reg_data:
        flash('Session expired or invalid. Please register again.', 'error')
        return redirect(url_for('auth.register'))
        
    if request.method == 'POST':
        user_otp = request.form.get('otp')
        
        if user_otp == reg_data['otp']:
            # OTP matches, create user
            new_user = User(
                username=reg_data['username'], 
                email=reg_data['email'], 
                password_hash=reg_data['password_hash'],
                semester=reg_data['semester'],
                department=reg_data['department'],
                phone=reg_data['phone']
            )
            try:
                db.session.add(new_user)
                db.session.commit()
                # Clear session data
                session.pop('registration_data', None)
                flash('Account created successfully! Please login.', 'success')
                return redirect(url_for('auth.login'))
            except Exception as e:
                db.session.rollback()
                flash(f'An error occurred: {str(e)}', 'error')
                print(f"Registration Error: {e}")
                return redirect(url_for('auth.register'))
        else:
            flash('Invalid OTP. Please try again.', 'error')
            
    return render_template('auth/verify_otp.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        remember = True if request.form.get('remember') else False
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
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
