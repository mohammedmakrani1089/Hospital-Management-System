
from datetime import date

from flask import (
    redirect,
    render_template,
    url_for,
    flash,
    session
)

from app.database.db import get_connection
from app.routes.home import home_bp


# ==========================================
# FIND DOCTORS PAGE
# ==========================================

@home_bp.route("/")
def doctors():

    db = get_connection()
    cursor = None

    try:

        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM doctors
            WHERE status = 'active'
        """)

        doctors_lists = cursor.fetchall()

    finally:

        if cursor:
            cursor.close()

        db.close()

    return render_template(
        "home.html",
        doctors=doctors_lists
    )


# ==========================================
# DOCTOR DETAILS PAGE
# ==========================================

@home_bp.route("/doctor/<int:doctor_id>")
def doctor_details(doctor_id):

    if not session.get("user_id"):

        return redirect(
            url_for("auth.login", doctor_id=doctor_id)
        )

    db = get_connection()
    cursor = None

    doctor = None
    schedule_data = []
    user = None
    user_age = None

    try:

        cursor = db.cursor(dictionary=True)

        # Fetch Doctor Details
        cursor.execute("""
            SELECT *
            FROM doctors
            WHERE doctor_id = %s
            AND status = 'active'
        """, (doctor_id,))

        doctor = cursor.fetchone()

        if doctor:

            # Fetch Doctor Weekly Schedule
            cursor.execute("""
                SELECT
                    day_of_week,
                    start_time,
                    end_time,
                    slot_duration,
                    is_available,
                    is_holiday
                FROM doctor_schedules
                WHERE doctor_id = %s
                ORDER BY FIELD(
                    day_of_week,
                    'Monday', 'Tuesday', 'Wednesday',
                    'Thursday', 'Friday', 'Saturday', 'Sunday'
                ), start_time
            """, (doctor_id,))

            schedules = cursor.fetchall()

            for schedule in schedules:

                schedule_data.append({
                    "day_of_week": schedule["day_of_week"],
                    "start_time": (
                        str(schedule["start_time"])
                        if schedule["start_time"] else None
                    ),
                    "end_time": (
                        str(schedule["end_time"])
                        if schedule["end_time"] else None
                    ),
                    "slot_duration": int(schedule["slot_duration"]),
                    "is_available": bool(schedule["is_available"]),
                    "is_holiday": bool(schedule["is_holiday"])
                })

            # Fetch Logged-in User Details
            cursor.execute("""
                SELECT
                    full_name,
                    date_of_birth,
                    gender,
                    phone
                FROM users
                WHERE user_id = %s
            """, (session["user_id"],))

            user = cursor.fetchone()

            # Calculate User Age
            if user and user["date_of_birth"]:

                today = date.today()
                dob = user["date_of_birth"]

                user_age = today.year - dob.year - (
                    (today.month, today.day) < (dob.month, dob.day)
                )

    finally:

        if cursor:
            cursor.close()

        db.close()

    if not doctor:

        flash("Doctor not found!", "error")

        return redirect(url_for("home.doctors"))

    return render_template(
        "doctor_details.html",
        doctor=doctor,
        schedule_data=schedule_data,
        user=user,
        user_age=user_age
    )
