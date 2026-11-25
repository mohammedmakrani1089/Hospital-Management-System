import os
import uuid
from flask import Blueprint, render_template, redirect , flash , current_app , url_for , session , request

from werkzeug.security import generate_password_hash , check_password_hash
from werkzeug.utils import secure_filename

from app.login_form import LoginForm
from app.signup_form import SignUpForm
from app.database.db import get_connection

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/signup", methods = ["GET" , "POST" ])

def signup():
    
    form = SignUpForm()
    
    if form.validate_on_submit():
        
        full_name = form.full_name.data
        email = form.email.data.strip().lower()
        phone_no = "+91" + form.phone_no.data.strip()
        gender = form.gender.data
        date_of_birth = form.date_of_birth.data
        
        hash_password = generate_password_hash(form.password.data)
        
        profile_image = "default_profile.png"

        conn = None
        cursor = None
        
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            
            # Check existing email
            cursor.execute(
                "SELECT user_id FROM users WHERE email = %s",
                (email,)
            )

            if cursor.fetchone():
                flash("Email already registered!", "error")
                return redirect(url_for("auth.signup"))


            # Check existing phone number
            cursor.execute(
                "SELECT user_id FROM users WHERE phone = %s",
                (phone_no,)
            )

            if cursor.fetchone():
                flash("Mobile number already registered!", "error")
                return redirect(url_for("auth.signup"))
            
            # Profile image upload
            image = form.profile_image.data

            if image and image.filename:

                filename = secure_filename(image.filename)
                extension = os.path.splitext(filename)[1].lower()

                profile_image = f"{uuid.uuid4().hex}{extension}"

                upload_folder = os.path.join(
                    current_app.static_folder,
                    "images",
                    "profile"
                )

                os.makedirs(upload_folder, exist_ok=True)

                image.save(
                    os.path.join(upload_folder, profile_image)
                )
            print("Phone:", repr(phone_no))
            print("Phone Length:", len(phone_no))
            # Insert user into MySQL
            cursor.execute("""
                INSERT INTO users (
                    full_name,
                    email,
                    phone,
                    gender,
                    date_of_birth,
                    password_hash,
                    profile_image
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                full_name,
                email,
                phone_no,
                gender,
                date_of_birth,
                hash_password,
                profile_image
            ))
            
            conn.commit()

            doctor_id = request.form.get("doctor_id", type=int)

            flash("Account Created Successfully!", "success")

            if doctor_id:
                return redirect(
                    url_for("auth.login", doctor_id=doctor_id)
                )

            return redirect(url_for("auth.login"))

        except Exception:
            if conn:
                conn.rollback()

            current_app.logger.exception("Signup failed")
            flash("Something went wrong. Please try again.", "error")

        finally:
            if cursor:
                cursor.close()

            if conn:
                conn.close()

    return render_template("signup.html", form=form)
    

@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    form = LoginForm()

    if form.validate_on_submit():

        login_input = form.email_or_phone.data.strip()
        password = form.password.data

        email = login_input.lower()
        phone = None

        # Identify email or mobile number
        mobile = login_input.replace(" ", "").replace("-", "")

        if mobile.startswith("+91") and mobile[3:].isdigit() and len(mobile[3:]) == 10:
            phone = mobile

        elif mobile.isdigit() and len(mobile) == 10:
            phone = "+91" + mobile

        conn = None
        cursor = None

        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT *
                FROM users
                WHERE email = %s OR phone = %s
                LIMIT 1
            """, (email, phone))

            user = cursor.fetchone()

            if user and check_password_hash(
                user["password_hash"], password
            ):

                session.clear()
                
                session.permanent = True

                session["user_id"] = user["user_id"]
                session["full_name"] = user["full_name"]
                session["role"] = user["role"]
                session["profile_image"] = user["profile_image"]

                flash("Login Successful!", "success")

                doctor_id = request.form.get("doctor_id", type=int)

                if doctor_id:
                    return redirect(
                        url_for("home.doctor_details", doctor_id=doctor_id)
                    )

                return redirect(url_for("home.doctors"))

            flash("Invalid Email/Mobile Number or Password!", "error")

        except Exception:
            current_app.logger.exception("Login failed")
            flash("Something went wrong. Please try again.", "error")

        finally:
            if cursor:
                cursor.close()

            if conn:
                conn.close()

    return render_template("login.html", form=form)


@auth_bp.route("/logout", methods=["POST"])
def logout():

    session.clear()

    flash("Logout Successfully!", "success")

    return redirect(url_for("auth.login"))


    

        
        
        
        