from datetime import date, datetime, time as datetime_time, timedelta
from decimal import Decimal, ROUND_HALF_UP

from flask import (
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.database.db import get_connection
from app.routes.home import home_bp

from .helpers import (
    format_appointment_time,
    get_appointment_datetime,
    time_to_minutes,
)


@home_bp.route("/my-appointments")
def my_appointments():

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
        # 1. FETCH USER APPOINTMENTS
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
                a.status AS appointment_status,

                d.doctor_name,
                d.specialization,
                d.qualification,
                d.profile_image,

                p.payment_id,
                p.amount,
                p.status AS payment_status,
                p.payment_method,
                p.gateway_payment_id,
                p.refund_amount,
                p.refund_status,
                (
                    SELECT COUNT(*)
                    FROM appointment_reschedule_history rh
                    WHERE rh.appointment_id = a.appointment_id
                ) AS reschedule_count

            FROM appointments a

            JOIN doctors d
                ON a.doctor_id = d.doctor_id

            LEFT JOIN payments p
                ON p.payment_id = (
                    SELECT MAX(p2.payment_id)
                    FROM payments p2
                    WHERE p2.appointment_id = a.appointment_id
                )

            WHERE a.booked_by_user_id = %s

            ORDER BY
                a.appointment_date DESC,
                a.start_time DESC,
                a.appointment_id DESC

        """, (user_id,))

        appointments = cursor.fetchall()


        # ==========================================
        # 2. PREPARE APPOINTMENT DATA
        # ==========================================

        today = date.today()
        now = datetime.now()

        appointment_counts = {
            "total": len(appointments),
            "upcoming": 0,
            "pending": 0,
            "completed": 0
        }


        for appointment in appointments:

            status = appointment["appointment_status"]

            payment_status = (
                appointment["payment_status"] or "not_applicable"
            )


            # ==========================================
            # 3. ASSIGN APPOINTMENT CATEGORY
            # ==========================================

            if status == "completed":

                category = "completed"

                appointment_counts["completed"] += 1


            elif status in ("cancelled", "rejected"):

                category = "cancelled"


            elif status in ("pending_payment", "pending_approval"):

                category = "pending"

                appointment_counts["pending"] += 1


            elif status == "confirmed":

                category = "upcoming"

                appointment_counts["upcoming"] += 1


            else:

                category = "pending"

                appointment_counts["pending"] += 1


            appointment["category"] = category

            appointment["status_label"] = (
                status.replace("_", " ").title()
            )


            # ==========================================
            # 4. FORMAT APPOINTMENT DATE AND TIME
            # ==========================================

            appointment["date_label"] = (
                appointment["appointment_date"].strftime("%d %B %Y")
            )

            start_label = format_appointment_time(
                appointment["start_time"]
            )

            end_label = format_appointment_time(
                appointment["end_time"]
            )

            appointment["time_label"] = (
                start_label + " - " + end_label
            )


            # ==========================================
            # 5. PREPARE PAYMENT DETAILS
            # ==========================================

            appointment["payment_status"] = payment_status

            appointment["amount"] = (
                appointment["amount"] or 0
            )

            appointment["refund_amount"] = (
                appointment["refund_amount"] or 0
            )



            # ==========================================
            # 6. CHECK WHETHER USER CAN MODIFY APPOINTMENT
            # ==========================================

            appointment_datetime = get_appointment_datetime(
                appointment["appointment_date"],
                appointment["start_time"]
            )

            # Get reschedule count
            appointment["reschedule_count"] = int(
                appointment.get("reschedule_count") or 0
            )

            # Check whether appointment can be modified
            appointment["can_modify"] = (

                status in ("pending_approval", "confirmed")

                and payment_status == "paid"

                and appointment_datetime > now

            )

            # Allow only ONE reschedule
            appointment["can_reschedule"] = (

                appointment["can_modify"]

                and appointment["reschedule_count"] < 1

            )



        # ==========================================
        # 7. RENDER MY APPOINTMENTS PAGE
        # ==========================================

        return render_template(

            "my_appointments.html",

            appointments=appointments,

            appointment_counts=appointment_counts

        )


    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()


# ==========================================
# RECEIPT DOWNLOAD - PLACEHOLDER
# ==========================================

@home_bp.route("/appointments/<int:appointment_id>/receipt")
def download_receipt(appointment_id):

    if not session.get("user_id"):

        return redirect(url_for("auth.login"))

    flash(
        "Receipt PDF feature is coming in the next step.",
        "info"
    )

    return redirect(url_for("home.my_appointments"))



# ==========================================
# CANCEL APPOINTMENT
# ==========================================

@home_bp.route("/my-appointments/cancel", methods=["POST"])
def cancel_appointment():

    # ==========================================
    # 1. LOGIN CHECK
    # ==========================================

    if not session.get("user_id"):

        return redirect(url_for("auth.login"))


    appointment_id = request.form.get(
        "appointment_id", type=int
    )

    if not appointment_id:

        flash("Invalid appointment request.", "error")

        return redirect(url_for("home.my_appointments"))


    db = None
    cursor = None

    try:

        db = get_connection()
        cursor = db.cursor(dictionary=True)

        db.start_transaction()

        user_id = session["user_id"]


        # ==========================================
        # 2. FETCH AND LOCK USER APPOINTMENT
        # ==========================================

        cursor.execute("""
            SELECT
                appointment_id,
                booked_by_user_id,
                appointment_date,
                start_time,
                status

            FROM appointments

            WHERE appointment_id = %s
            AND booked_by_user_id = %s

            FOR UPDATE
        """, (
            appointment_id,
            user_id
        ))

        appointment = cursor.fetchone()


        if not appointment:

            db.rollback()

            flash("Appointment not found.", "error")

            return redirect(url_for("home.my_appointments"))


        # ==========================================
        # 3. CHECK APPOINTMENT STATUS
        # ==========================================

        if appointment["status"] not in (
            "pending_approval",
            "confirmed"
        ):

            db.rollback()

            flash(
                "This appointment cannot be cancelled.",
                "error"
            )

            return redirect(url_for("home.my_appointments"))


        # ==========================================
        # 4. CHECK APPOINTMENT DATE AND TIME
        # ==========================================

        appointment_datetime = get_appointment_datetime(
            appointment["appointment_date"],
            appointment["start_time"]
        )

        if appointment_datetime <= datetime.now():

            db.rollback()

            flash(
                "Past appointments cannot be cancelled.",
                "error"
            )

            return redirect(url_for("home.my_appointments"))


        # ==========================================
        # 5. FETCH LATEST PAID PAYMENT
        # ==========================================

        cursor.execute("""
            SELECT
                payment_id,
                amount,
                status,
                refund_status

            FROM payments

            WHERE appointment_id = %s
            AND status = 'paid'

            ORDER BY payment_id DESC

            LIMIT 1

            FOR UPDATE
        """, (appointment_id,))

        payment = cursor.fetchone()


        if not payment:

            db.rollback()

            flash(
                "A successful payment record was not found.",
                "error"
            )

            return redirect(url_for("home.my_appointments"))


        if payment["refund_status"] != "not_applicable":

            db.rollback()

            flash(
                "A cancellation or refund request already exists.",
                "error"
            )

            return redirect(url_for("home.my_appointments"))


        # ==========================================
        # 6. CALCULATE REFUND PERCENTAGE
        # ==========================================

        consultation_fee = Decimal(str(payment["amount"]))

        refund_percentage = 0


        if Decimal("100.00") <= consultation_fee <= Decimal("300.00"):

            refund_percentage = 50

        elif Decimal("300.00") < consultation_fee <= Decimal("500.00"):

            refund_percentage = 60

        elif consultation_fee > Decimal("500.00"):

            refund_percentage = 70


        # Calculate estimated refund
        refund_amount = (
            consultation_fee *
            Decimal(refund_percentage) /
            Decimal("100")
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )


        # Fees below ₹100 require manual review
        if refund_percentage == 0:

            refund_status = "manual_review"

        else:

            refund_status = "pending"


        # ==========================================
        # 7. UPDATE APPOINTMENT STATUS
        # ==========================================

        cursor.execute("""
            UPDATE appointments

            SET status = 'cancelled'

            WHERE appointment_id = %s
            AND booked_by_user_id = %s
            AND status IN ('pending_approval', 'confirmed')
        """, (
            appointment_id,
            user_id
        ))

        if cursor.rowcount != 1:

            raise Exception("Appointment cancellation update failed.")


        # ==========================================
        # 8. SAVE REFUND DETAILS
        # ==========================================

        cursor.execute("""
            UPDATE payments

            SET
                refund_amount = %s,
                refund_status = %s,
                refund_requested_at = NOW()

            WHERE payment_id = %s
            AND status = 'paid'
            AND refund_status = 'not_applicable'
        """, (
            refund_amount,
            refund_status,
            payment["payment_id"]
        ))

        if cursor.rowcount != 1:

            raise Exception("Refund record update failed.")


        # ==========================================
        # 9. COMMIT BOTH DATABASE UPDATES
        # ==========================================

        db.commit()


        # ==========================================
        # 10. SHOW RESULT
        # ==========================================

        if refund_percentage == 0:

            flash(
                "Appointment cancelled. Refund requires manual review.",
                "warning"
            )

        else:

            flash(
                f"Appointment cancelled. Estimated refund: ₹{refund_amount:.2f}. Refund status: Pending.",
                "success"
            )


        return redirect(url_for("home.my_appointments"))


    except Exception as error:

        if db:
            db.rollback()

        print("Appointment Cancellation Error:", error)

        flash(
            "Unable to cancel appointment. Please try again.",
            "error"
        )

        return redirect(url_for("home.my_appointments"))


    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()



# ==========================================
# RESCHEDULE APPOINTMENT
# ==========================================

@home_bp.route("/my-appointments/reschedule", methods=["POST"])
def reschedule_appointment():

    # ==========================================
    # 1. LOGIN CHECK
    # ==========================================

    if not session.get("user_id"):

        return redirect(url_for("auth.login"))


    appointment_id = request.form.get(
        "appointment_id", type=int
    )

    new_date_value = request.form.get(
        "new_appointment_date", ""
    )

    new_time_value = request.form.get(
        "new_start_time", ""
    )


    if not appointment_id or not new_date_value or not new_time_value:

        flash("Please provide valid reschedule details.", "error")

        return redirect(url_for("home.my_appointments"))


    db = None
    cursor = None

    try:

        db = get_connection()
        cursor = db.cursor(dictionary=True)

        db.start_transaction()

        user_id = session["user_id"]


        # ==========================================
        # 2. VALIDATE NEW DATE AND TIME
        # ==========================================

        try:

            new_date = date.fromisoformat(new_date_value)

            new_start = datetime.strptime(
                new_time_value, "%H:%M"
            ).time()

        except ValueError:

            db.rollback()

            flash("Invalid appointment date or time.", "error")

            return redirect(url_for("home.my_appointments"))


        today = date.today()

        if new_date < today or new_date > today + timedelta(days=30):

            db.rollback()

            flash(
                "You can reschedule within the next 30 days only.",
                "error"
            )

            return redirect(url_for("home.my_appointments"))


        if new_date == today and new_start <= datetime.now().time():

            db.rollback()

            flash("Please select a future appointment time.", "error")

            return redirect(url_for("home.my_appointments"))


        # ==========================================
        # 3. FETCH AND LOCK APPOINTMENT
        # ==========================================

        cursor.execute("""
            SELECT
                appointment_id,
                doctor_id,
                appointment_date,
                start_time,
                end_time,
                status

            FROM appointments

            WHERE appointment_id = %s
            AND booked_by_user_id = %s

            FOR UPDATE
        """, (
            appointment_id,
            user_id
        ))

        appointment = cursor.fetchone()


        if not appointment:

            db.rollback()

            flash("Appointment not found.", "error")

            return redirect(url_for("home.my_appointments"))


        # ==========================================
        # 3.1 ENFORCE ONE-TIME RESCHEDULE LIMIT
        # ==========================================

        cursor.execute("""
            SELECT COUNT(*) AS total_reschedules
            FROM appointment_reschedule_history
            WHERE appointment_id = %s
        """, (appointment_id,))

        reschedule_history = cursor.fetchone()

        if int(reschedule_history["total_reschedules"] or 0) >= 1:

            db.rollback()

            flash(
                "You can reschedule an appointment only once.",
                "error"
            )

            return redirect(url_for("home.my_appointments"))


        # ==========================================
        # 4. CHECK APPOINTMENT STATUS
        # ==========================================

        if appointment["status"] not in (
            "pending_approval",
            "confirmed"
        ):

            db.rollback()

            flash(
                "This appointment cannot be rescheduled.",
                "error"
            )

            return redirect(url_for("home.my_appointments"))


        # Check old appointment is still in the future
        old_appointment_datetime = get_appointment_datetime(
            appointment["appointment_date"],
            appointment["start_time"]
        )

        if old_appointment_datetime <= datetime.now():

            db.rollback()

            flash(
                "Past appointments cannot be rescheduled.",
                "error"
            )

            return redirect(url_for("home.my_appointments"))


        # ==========================================
        # 5. CHECK SUCCESSFUL PAYMENT
        # ==========================================

        cursor.execute("""
            SELECT
                payment_id,
                status

            FROM payments

            WHERE appointment_id = %s

            ORDER BY payment_id DESC

            LIMIT 1

            FOR UPDATE
        """, (appointment_id,))

        payment = cursor.fetchone()


        if not payment or payment["status"] != "paid":

            db.rollback()

            flash(
                "Only successfully paid appointments can be rescheduled.",
                "error"
            )

            return redirect(url_for("home.my_appointments"))


        # ==========================================
        # 6. CALCULATE ORIGINAL SLOT DURATION
        # ==========================================

        old_start_minutes = time_to_minutes(
            appointment["start_time"]
        )

        old_end_minutes = time_to_minutes(
            appointment["end_time"]
        )

        slot_duration = old_end_minutes - old_start_minutes


        if slot_duration <= 0:

            db.rollback()

            flash("Original appointment duration is invalid.", "error")

            return redirect(url_for("home.my_appointments"))


        new_start_minutes = time_to_minutes(new_start)

        new_end_minutes = new_start_minutes + slot_duration


        # Appointment must end on the same day
        if new_end_minutes > 1439:

            db.rollback()

            flash("Invalid appointment time.", "error")

            return redirect(url_for("home.my_appointments"))


        new_end = datetime_time(
            new_end_minutes // 60,
            new_end_minutes % 60
        )


        # Prevent unnecessary same-slot rescheduling
        if (
            new_date == appointment["appointment_date"]
            and new_start_minutes == old_start_minutes
        ):

            db.rollback()

            flash("Please select a different appointment slot.", "error")

            return redirect(url_for("home.my_appointments"))


        # ==========================================
        # 7. FETCH DOCTOR WEEKLY SCHEDULE
        # ==========================================

        weekday = new_date.strftime("%A")

        cursor.execute("""
            SELECT
                start_time,
                end_time,
                slot_duration,
                is_available,
                is_holiday

            FROM doctor_schedules

            WHERE doctor_id = %s
            AND day_of_week = %s

        """, (
            appointment["doctor_id"],
            weekday
        ))

        schedules = cursor.fetchall()


        is_holiday = any(
            bool(schedule["is_holiday"])
            for schedule in schedules
        )

        valid_slot = False


        if not is_holiday:

            for schedule in schedules:

                if (
                    not schedule["is_available"]
                    or schedule["is_holiday"]
                    or not schedule["start_time"]
                    or not schedule["end_time"]
                ):

                    continue


                shift_start = time_to_minutes(
                    schedule["start_time"]
                )

                shift_end = time_to_minutes(
                    schedule["end_time"]
                )

                configured_duration = int(
                    schedule["slot_duration"]
                )


                if configured_duration <= 0:
                    continue


                if (

                    new_start_minutes >= shift_start

                    and new_end_minutes <= shift_end

                    and slot_duration == configured_duration

                    and (
                        new_start_minutes - shift_start
                    ) % configured_duration == 0

                ):

                    valid_slot = True

                    break


        if not valid_slot:

            db.rollback()

            flash(
                "This doctor is not available at the selected date and time.",
                "error"
            )

            return redirect(url_for("home.my_appointments"))


        # ==========================================
        # 8. CHECK SLOT AVAILABILITY
        # ==========================================

        cursor.execute("""
            SELECT appointment_id

            FROM appointments

            WHERE doctor_id = %s

            AND appointment_date = %s

            AND appointment_id != %s

            AND (
                status IN ('pending_approval', 'confirmed')

                OR (
                    status = 'pending_payment'
                    AND payment_expires_at > NOW()
                )
            )

            AND start_time < %s

            AND end_time > %s

            LIMIT 1

        """, (
            appointment["doctor_id"],
            new_date,
            appointment_id,
            new_end,
            new_start
        ))

        conflicting_appointment = cursor.fetchone()


        if conflicting_appointment:

            db.rollback()

            flash(
                "This time slot has already been booked. Please choose another slot.",
                "error"
            )

            return redirect(url_for("home.my_appointments"))


        # ==========================================
        # 9. SAVE RESCHEDULE HISTORY
        # ==========================================

        cursor.execute("""
            INSERT INTO appointment_reschedule_history (

                appointment_id,
                user_id,

                old_appointment_date,
                old_start_time,
                old_end_time,

                new_appointment_date,
                new_start_time,
                new_end_time

            )

            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)

        """, (

            appointment_id,
            user_id,

            appointment["appointment_date"],
            appointment["start_time"],
            appointment["end_time"],

            new_date,
            new_start,
            new_end

        ))


        # ==========================================
        # 10. UPDATE APPOINTMENT
        # ==========================================

        cursor.execute("""
            UPDATE appointments

            SET
                appointment_date = %s,
                start_time = %s,
                end_time = %s

            WHERE appointment_id = %s

            AND booked_by_user_id = %s

            AND status IN ('pending_approval', 'confirmed')

        """, (

            new_date,
            new_start,
            new_end,

            appointment_id,
            user_id

        ))


        if cursor.rowcount != 1:

            raise Exception("Appointment update failed.")


        # ==========================================
        # 11. COMMIT CHANGES
        # ==========================================

        db.commit()


        flash(
            "Appointment rescheduled successfully! Your previous payment remains valid.",
            "success"
        )

        return redirect(url_for("home.my_appointments"))


    except Exception as error:

        if db:
            db.rollback()

        print("Reschedule Appointment Error:", error)

        flash(
            "Unable to reschedule appointment. Please try again.",
            "error"
        )

        return redirect(url_for("home.my_appointments"))


    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()