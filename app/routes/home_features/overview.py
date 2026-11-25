
from datetime import date

from flask import (
    redirect,
    render_template,
    url_for,
    session
)

from app.database.db import get_connection
from app.routes.home import home_bp

from .helpers import format_appointment_time


# ==========================================
# OVERVIEW PAGE
# ==========================================

@home_bp.route("/overview")
def overview():

    # Login Required
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    db = None
    cursor = None

    try:

        db = get_connection()
        cursor = db.cursor(dictionary=True)

        user_id = session["user_id"]

        # ==========================================
        # 1. APPOINTMENT STATISTICS
        # ==========================================

        cursor.execute("""
            SELECT
                COUNT(*) AS total_appointments,

                SUM(
                    CASE
                        WHEN status = 'completed' THEN 1
                        ELSE 0
                    END
                ) AS completed_appointments,

                SUM(
                    CASE
                        WHEN status = 'pending_approval' THEN 1
                        ELSE 0
                    END
                ) AS pending_appointments

            FROM appointments

            WHERE booked_by_user_id = %s
        """, (user_id,))

        statistics = cursor.fetchone()

        statistics = {
            key: int(value or 0)
            for key, value in statistics.items()
        }

        # ==========================================
        # 2. UPCOMING APPOINTMENT
        # ==========================================

        cursor.execute("""
            SELECT
                a.appointment_id,
                a.patient_name,
                a.patient_age,
                a.patient_gender,
                a.appointment_date,
                a.start_time,
                a.end_time,
                a.status,

                d.doctor_name,
                d.specialization,
                d.profile_image

            FROM appointments a

            JOIN doctors d
                ON a.doctor_id = d.doctor_id

            WHERE a.booked_by_user_id = %s

            AND a.appointment_date >= CURDATE()

            AND a.status IN (
                'pending_approval',
                'confirmed'
            )

            ORDER BY
                a.appointment_date ASC,
                a.start_time ASC

            LIMIT 1
        """, (user_id,))

        upcoming_appointment = cursor.fetchone()

        if upcoming_appointment:

            upcoming_appointment["date_label"] = (
                upcoming_appointment["appointment_date"].strftime(
                    "%d %B %Y"
                )
            )

            upcoming_appointment["start_time_label"] = (
                format_appointment_time(
                    upcoming_appointment["start_time"]
                )
            )

            upcoming_appointment["end_time_label"] = (
                format_appointment_time(
                    upcoming_appointment["end_time"]
                )
            )

            upcoming_appointment["status_label"] = (
                upcoming_appointment["status"]
                .replace("_", " ")
                .title()
            )

        # ==========================================
        # 3. ACTIVE DOCTORS FOR SLIDER
        # ==========================================

        cursor.execute("""
            SELECT
                doctor_id,
                doctor_name,
                specialization,
                qualification,
                experience,
                consultation_fee,
                profile_image,
                about

            FROM doctors

            WHERE status = 'active'

            ORDER BY doctor_id DESC

            LIMIT 8
        """)

        doctors = cursor.fetchall()

        # ==========================================
        # 4. DAILY HEALTH THOUGHTS
        # ==========================================

        daily_thoughts = [

            "An apple a day keeps the doctor away.",
            "A little movement today is better than none.",
            "Drink water regularly throughout your day.",
            "Make room for a variety of fruits and vegetables.",
            "Consistent sleep is an important part of a healthy routine.",
            "Take short breaks from screens whenever possible.",
            "Never ignore persistent symptoms. Seek qualified medical advice.",
            "Regular health check-ups help you stay informed.",
            "Wash your hands often to help prevent the spread of germs.",
            "Healthy habits are built through small daily actions.",
            "Make time to relax and recharge your mind.",
            "Choose balanced meals that nourish your body.",
            "A little fresh air and movement can brighten your day.",
            "Listen to your body and take your health seriously.",
            "Your health deserves attention every single day."

        ]

        # Same thought throughout the day.
        # It changes automatically on the next date.

        thought_index = date.today().toordinal() % len(daily_thoughts)

        daily_thought = daily_thoughts[thought_index]

        # ==========================================
        # 5. RENDER OVERVIEW PAGE
        # ==========================================

        return render_template(
            "overview.html",
            statistics=statistics,
            upcoming_appointment=upcoming_appointment,
            doctors=doctors,
            daily_thought=daily_thought,
            today=date.today(),
            user_name=session.get("full_name", "User"),
            user_profile=session.get(
                "profile_image",
                "default_profile.png"
            )
        )

    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()
