from datetime import date, datetime, timedelta
from decimal import Decimal

import razorpay
from flask import (
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.database.db import get_connection
from app.routes.home import home_bp
from .helpers import time_to_minutes


# ==========================================
# PAYMENT ROUTE
# ==========================================

@home_bp.route("/payment/<int:doctor_id>", methods=["GET", "POST"])
def payment(doctor_id):

    # Login Check
    if not session.get("user_id"):
        return redirect(url_for("auth.login", doctor_id=doctor_id))

    db = None
    cursor = None

    try:

        db = get_connection()
        cursor = db.cursor(dictionary=True)

        # ==========================================
        # 1. FETCH DOCTOR DETAILS
        # ==========================================

        cursor.execute("""
            SELECT *
            FROM doctors
            WHERE doctor_id = %s
            AND status = 'active'
        """, (doctor_id,))

        doctor = cursor.fetchone()

        if not doctor:

            flash("Doctor not found!", "error")

            return redirect(url_for("home.doctors"))


        # ==========================================
        # 2. HANDLE PATIENT DETAILS FORM
        # ==========================================

        if request.method == "POST":

            # Clear any previous draft
            session.pop("payment_booking", None)

            patient_name = request.form.get(
                "patient_name", ""
            ).strip()

            patient_age = request.form.get(
                "patient_age", ""
            ).strip()

            patient_gender = request.form.get(
                "patient_gender", ""
            )

            appointment_date = request.form.get(
                "appointment_date", ""
            )

            start_time = request.form.get(
                "start_time", ""
            )

            end_time = request.form.get(
                "end_time", ""
            )


            # ==========================================
            # 3. VALIDATE PATIENT DETAILS
            # ==========================================

            if not patient_name or len(patient_name) > 100:

                flash("Please enter a valid patient name.", "error")

                return redirect(
                    url_for("home.doctor_details", doctor_id=doctor_id)
                )


            if not patient_age.isdigit():

                flash("Please enter a valid patient age.", "error")

                return redirect(
                    url_for("home.doctor_details", doctor_id=doctor_id)
                )


            patient_age = int(patient_age)

            if patient_age < 0 or patient_age > 120:

                flash("Patient age must be between 0 and 120.", "error")

                return redirect(
                    url_for("home.doctor_details", doctor_id=doctor_id)
                )


            if patient_gender not in ["Male", "Female", "Other"]:

                flash("Please select a valid gender.", "error")

                return redirect(
                    url_for("home.doctor_details", doctor_id=doctor_id)
                )


            # ==========================================
            # 4. VALIDATE APPOINTMENT DATE AND TIME
            # ==========================================

            try:

                selected_date = date.fromisoformat(appointment_date)

                selected_start = datetime.strptime(
                    start_time, "%H:%M:%S"
                ).time()

                selected_end = datetime.strptime(
                    end_time, "%H:%M:%S"
                ).time()

            except ValueError:

                flash("Invalid appointment date or time.", "error")

                return redirect(
                    url_for("home.doctor_details", doctor_id=doctor_id)
                )


            today = date.today()

            if selected_date < today or selected_date > today + timedelta(days=30):

                flash("Appointments can only be booked within the next 30 days.", "error")

                return redirect(
                    url_for("home.doctor_details", doctor_id=doctor_id)
                )


            if selected_date == today and selected_start <= datetime.now().time():

                flash("This appointment time has already passed.", "error")

                return redirect(
                    url_for("home.doctor_details", doctor_id=doctor_id)
                )


            # ==========================================
            # 5. CHECK DOCTOR WEEKLY SCHEDULE
            # ==========================================

            weekday = selected_date.strftime("%A")

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
            """, (doctor_id, weekday))

            schedules = cursor.fetchall()

            start_minutes = time_to_minutes(selected_start)
            end_minutes = time_to_minutes(selected_end)

            valid_slot = False

            is_holiday = any(
                bool(schedule["is_holiday"])
                for schedule in schedules
            )

            if not is_holiday:

                for schedule in schedules:

                    if (
                        not schedule["is_available"]
                        or schedule["is_holiday"]
                        or not schedule["start_time"]
                        or not schedule["end_time"]
                    ):
                        continue

                    shift_start = time_to_minutes(schedule["start_time"])
                    shift_end = time_to_minutes(schedule["end_time"])

                    duration = int(schedule["slot_duration"])

                    if duration <= 0:
                        continue

                    if (
                        start_minutes >= shift_start
                        and end_minutes <= shift_end
                        and end_minutes - start_minutes == duration
                        and (start_minutes - shift_start) % duration == 0
                    ):

                        valid_slot = True
                        break


            if not valid_slot:

                flash("This appointment slot is not available.", "error")

                return redirect(
                    url_for("home.doctor_details", doctor_id=doctor_id)
                )



            # ==========================================
            # 6. CHECK EXISTING APPOINTMENT
            # ==========================================

            cursor.execute("""
                SELECT appointment_id
                FROM appointments
                WHERE doctor_id = %s
                AND appointment_date = %s
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
                doctor_id,
                selected_date,
                selected_end,
                selected_start
            ))

            existing_appointment = cursor.fetchone()

            if existing_appointment:

                flash("This appointment slot has already been booked.", "error")

                return redirect(
                    url_for("home.doctor_details", doctor_id=doctor_id)
                )



            
            # ==========================================
            # 7. CREATE APPOINTMENT AND PAYMENT RECORD
            # ==========================================

            try:

                # Create appointment
                cursor.execute("""
                    INSERT INTO appointments (
                        booked_by_user_id,
                        doctor_id,
                        patient_name,
                        patient_age,
                        patient_gender,
                        appointment_date,
                        start_time,
                        end_time,
                        status,
                        payment_expires_at
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s,
                        'pending_payment',
                        DATE_ADD(NOW(), INTERVAL 10 MINUTE)
                    )
                """, (
                    session["user_id"],
                    doctor_id,
                    patient_name,
                    patient_age,
                    patient_gender,
                    selected_date,
                    selected_start,
                    selected_end
                ))

                # Get newly created appointment ID
                appointment_id = cursor.lastrowid


                # Create initial payment record
                cursor.execute("""
                    INSERT INTO payments (
                        appointment_id,
                        amount,
                        currency,
                        status
                    )
                    VALUES (%s, %s, 'INR', 'created')
                """, (
                    appointment_id,
                    doctor["consultation_fee"]
                ))


                # Save both records
                db.commit()


            except Exception as error:

                db.rollback()

                print("Appointment creation error:", error)

                flash(
                    "Unable to create appointment. Please try again.",
                    "error"
                )

                return redirect(
                    url_for("home.doctor_details", doctor_id=doctor_id)
                )


            # Save appointment ID for payment page
            session["payment_booking"] = {

                "appointment_id": appointment_id,

                "doctor_id": doctor_id,

                "user_id": session["user_id"],

                "patient_name": patient_name,

                "patient_age": patient_age,

                "patient_gender": patient_gender,

                "appointment_date": selected_date.isoformat(),

                "start_time": selected_start.strftime("%H:%M:%S"),

                "end_time": selected_end.strftime("%H:%M:%S")

            }


            return redirect(
                url_for("home.payment", doctor_id=doctor_id)
            )




        # ==========================================
        # 8. DISPLAY PAYMENT PAGE AND CREATE RAZORPAY ORDER
        # ==========================================

        booking = session.get("payment_booking")

        if not booking or booking.get("doctor_id") != doctor_id:

            flash("Please select an appointment first.", "error")

            return redirect(
                url_for("home.doctor_details", doctor_id=doctor_id)
            )


        if booking.get("user_id") != session["user_id"]:

            session.pop("payment_booking", None)

            flash("Invalid booking session.", "error")

            return redirect(
                url_for("home.doctor_details", doctor_id=doctor_id)
            )


        appointment_id = booking["appointment_id"]


        # ==========================================
        # 8.1 FETCH APPOINTMENT AND PAYMENT RECORD
        # ==========================================

        cursor.execute("""
            SELECT
                a.status AS appointment_status,
                (a.payment_expires_at > NOW()) AS payment_window_active,

                p.payment_id,
                p.gateway_order_id,
                p.amount,
                p.currency,
                p.status AS payment_status

            FROM appointments a

            JOIN payments p
                ON a.appointment_id = p.appointment_id

            WHERE a.appointment_id = %s
            AND a.booked_by_user_id = %s

            ORDER BY p.payment_id DESC

            LIMIT 1
        """, (
            appointment_id,
            session["user_id"]
        ))

        payment_record = cursor.fetchone()


        if not payment_record:

            flash("Payment record not found.", "error")

            return redirect(
                url_for("home.doctor_details", doctor_id=doctor_id)
            )


        # Check appointment status
        if payment_record["appointment_status"] != "pending_payment":

            flash("This appointment is not available for payment.", "error")

            return redirect(
                url_for("home.doctors")
            )


        # Check payment expiry
        if not payment_record["payment_window_active"]:

            cursor.execute("""
                UPDATE appointments
                SET status = 'cancelled'
                WHERE appointment_id = %s
                AND status = 'pending_payment'
            """, (appointment_id,))

            db.commit()

            session.pop("payment_booking", None)

            flash("Payment time expired. Please book again.", "error")

            return redirect(
                url_for("home.doctor_details", doctor_id=doctor_id)
            )


        if payment_record["payment_status"] != "created":

            flash("This payment cannot be processed.", "error")

            return redirect(
                url_for("home.doctors")
            )


        # ==========================================
        # 8.2 GET RAZORPAY CREDENTIALS
        # ==========================================

        razorpay_key_id = current_app.config.get("RAZORPAY_KEY_ID")

        razorpay_key_secret = current_app.config.get("RAZORPAY_KEY_SECRET")


        if not razorpay_key_id or not razorpay_key_secret:

            flash("Payment gateway configuration is missing.", "error")

            return redirect(
                url_for("home.doctor_details", doctor_id=doctor_id)
            )


        # ==========================================
        # 8.3 CREATE RAZORPAY CLIENT
        # ==========================================

        razorpay_client = razorpay.Client(

            auth=(
                razorpay_key_id,
                razorpay_key_secret
            )

        )


        # ==========================================
        # 8.4 CONVERT AMOUNT INTO PAISE
        # ==========================================

        amount = Decimal(str(payment_record["amount"]))

        amount_paise = int(amount * 100)


        # ==========================================
        # 8.5 CREATE RAZORPAY ORDER
        # ==========================================

        razorpay_order_id = payment_record["gateway_order_id"]


        # Create a new Razorpay Order only if one does not exist
        if not razorpay_order_id:

            try:

                order_data = {

                    "amount": amount_paise,

                    "currency": payment_record["currency"],

                    "receipt": f"appt_{appointment_id}",

                    "notes": {

                        "appointment_id": str(appointment_id)

                    }

                }


                razorpay_order = razorpay_client.order.create(
                    data=order_data
                )


                razorpay_order_id = razorpay_order["id"]


                # Save Razorpay Order ID in MySQL
                cursor.execute("""
                    UPDATE payments

                    SET gateway_order_id = %s

                    WHERE payment_id = %s

                    AND status = 'created'
                """, (
                    razorpay_order_id,
                    payment_record["payment_id"]
                ))


                if cursor.rowcount != 1:

                    raise Exception("Unable to save Razorpay Order ID.")


                db.commit()


            except Exception as error:

                db.rollback()

                print("Razorpay Order Creation Error:", error)

                flash(
                    "Unable to create payment order. Please try again.",
                    "error"
                )

                return redirect(
                    url_for("home.doctor_details", doctor_id=doctor_id)
                )


        # ==========================================
        # 8.6 FORMAT APPOINTMENT DETAILS
        # ==========================================

        selected_date = date.fromisoformat(
            booking["appointment_date"]
        )

        start = datetime.strptime(
            booking["start_time"],
            "%H:%M:%S"
        )

        end = datetime.strptime(
            booking["end_time"],
            "%H:%M:%S"
        )


        appointment_time = (
            start.strftime("%I:%M %p")
            + " - "
            + end.strftime("%I:%M %p")
        ).lower()


        # ==========================================
        # 8.7 RENDER PAYMENT PAGE
        # ==========================================

        return render_template(

            "payment.html",

            doctor=doctor,

            appointment_id=appointment_id,

            appointment_date_label=selected_date.strftime("%d %b %Y"),

            appointment_time=appointment_time,

            patient_name=booking["patient_name"],

            patient_age=booking["patient_age"],

            patient_gender=booking["patient_gender"],

            razorpay_key_id=razorpay_key_id,

            razorpay_order_id=razorpay_order_id,

            razorpay_amount=amount_paise

        )



    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()



# ==========================================
# PAYMENT VERIFICATION ROUTE
# ==========================================

@home_bp.route("/payment/<int:doctor_id>/verify", methods=["POST"])
def verify_payment(doctor_id):

    # ==========================================
    # 1. CHECK USER SESSION
    # ==========================================

    if not session.get("user_id"):

        flash("Please login to continue.", "error")

        return redirect(url_for("auth.login"))


    booking = session.get("payment_booking")

    if (
        not booking
        or booking.get("doctor_id") != doctor_id
        or booking.get("user_id") != session["user_id"]
    ):

        flash("Invalid payment session.", "error")

        return redirect(url_for("home.doctor_details", doctor_id=doctor_id))


    # Get details returned by Razorpay Checkout
    razorpay_payment_id = request.form.get("razorpay_payment_id", "").strip()

    submitted_order_id = request.form.get("razorpay_order_id", "").strip()

    razorpay_signature = request.form.get("razorpay_signature", "").strip()


    if not all([
        razorpay_payment_id,
        submitted_order_id,
        razorpay_signature
    ]):

        flash("Incomplete payment information.", "error")

        return redirect(url_for("home.payment", doctor_id=doctor_id))


    db = None
    cursor = None

    try:

        db = get_connection()

        cursor = db.cursor(dictionary=True)


        # ==========================================
        # 2. FETCH TRUSTED PAYMENT DETAILS FROM MYSQL
        # ==========================================

        appointment_id = booking["appointment_id"]

        cursor.execute("""
            SELECT
                a.appointment_id,
                a.doctor_id,
                a.status AS appointment_status,

                p.payment_id,
                p.gateway_order_id,
                p.gateway_payment_id,
                p.amount,
                p.currency,
                p.status AS payment_status

            FROM appointments a

            JOIN payments p
                ON a.appointment_id = p.appointment_id

            WHERE a.appointment_id = %s
            AND a.booked_by_user_id = %s
            AND a.doctor_id = %s

            ORDER BY p.payment_id DESC
            LIMIT 1
        """, (
            appointment_id,
            session["user_id"],
            doctor_id
        ))

        payment_record = cursor.fetchone()


        if not payment_record or not payment_record["gateway_order_id"]:

            flash("Payment order not found.", "error")

            return redirect(url_for("home.doctor_details", doctor_id=doctor_id))


        # Always compare against the Order ID saved in MySQL
        saved_order_id = payment_record["gateway_order_id"]


        if submitted_order_id != saved_order_id:

            flash("Invalid Razorpay Order ID.", "error")

            return redirect(url_for("home.payment", doctor_id=doctor_id))


        # Already processed payment: allow safe repeat callback
        if (
            payment_record["payment_status"] == "paid"
            and payment_record["gateway_payment_id"] == razorpay_payment_id
        ):

            session.pop("payment_booking", None)

            flash(
                "Payment already verified. Your appointment is awaiting doctor approval.",
                "success"
            )

            return redirect(url_for("home.overview"))


        if (
            payment_record["payment_status"] != "created"
            or payment_record["appointment_status"] != "pending_payment"
        ):

            flash("This payment has already been processed.", "error")

            return redirect(url_for("home.doctors"))


        # ==========================================
        # 3. CREATE RAZORPAY CLIENT
        # ==========================================

        razorpay_client = razorpay.Client(
            auth=(
                current_app.config["RAZORPAY_KEY_ID"],
                current_app.config["RAZORPAY_KEY_SECRET"]
            )
        )


        # ==========================================
        # 4. VERIFY PAYMENT SIGNATURE
        # ==========================================

        try:

            razorpay_client.utility.verify_payment_signature({

                "razorpay_order_id": saved_order_id,

                "razorpay_payment_id": razorpay_payment_id,

                "razorpay_signature": razorpay_signature

            })

        except Exception as error:

            print("Signature Verification Error:", error)

            flash("Payment signature verification failed.", "error")

            return redirect(url_for("home.payment", doctor_id=doctor_id))


        # ==========================================
        # 5. FETCH PAYMENT DETAILS FROM RAZORPAY
        # ==========================================

        gateway_payment = razorpay_client.payment.fetch(
            razorpay_payment_id
        )


        expected_amount = int(
            Decimal(str(payment_record["amount"])) * 100
        )

        expected_currency = payment_record["currency"]


        # Verify order, amount and currency
        if (
            gateway_payment["order_id"] != saved_order_id
            or int(gateway_payment["amount"]) != expected_amount
            or gateway_payment["currency"] != expected_currency
        ):

            flash("Payment details do not match our order.", "error")

            return redirect(url_for("home.payment", doctor_id=doctor_id))


        # ==========================================
        # 6. CAPTURE AUTHORIZED PAYMENT
        # ==========================================

        if gateway_payment["status"] == "authorized":

            gateway_payment = razorpay_client.payment.capture(

                razorpay_payment_id,

                {
                    "amount": expected_amount,
                    "currency": expected_currency
                }

            )


        # Only captured payments are accepted
        if gateway_payment["status"] != "captured":

            flash(
                "Payment is not captured yet. Please contact support.",
                "error"
            )

            return redirect(url_for("home.payment", doctor_id=doctor_id))


        # ==========================================
        # 7. UPDATE MYSQL RECORDS
        # ==========================================

        # End the earlier read transaction
        db.commit()

        # Start a fresh transaction
        db.start_transaction()


        # Lock appointment and payment records
        cursor.execute("""
            SELECT
                a.status AS appointment_status,
                p.status AS payment_status,
                p.gateway_payment_id

            FROM appointments a

            JOIN payments p
                ON a.appointment_id = p.appointment_id

            WHERE a.appointment_id = %s
            AND p.payment_id = %s

            FOR UPDATE
        """, (
            appointment_id,
            payment_record["payment_id"]
        ))

        locked_record = cursor.fetchone()


        if not locked_record:

            raise Exception("Appointment or payment record not found.")


        # Check whether another callback already processed it
        if (
            locked_record["payment_status"] == "paid"
            and locked_record["gateway_payment_id"] == razorpay_payment_id
        ):

            db.commit()

            session.pop("payment_booking", None)

            flash("Payment already verified successfully.", "success")

            return redirect(url_for("home.overview"))


        if (
            locked_record["payment_status"] != "created"
            or locked_record["appointment_status"] != "pending_payment"
        ):

            raise Exception("Appointment or payment status has changed.")


        # Update payment record
        cursor.execute("""
            UPDATE payments

            SET
                gateway_payment_id = %s,
                payment_method = %s,
                status = 'paid',
                paid_at = NOW()

            WHERE payment_id = %s
            AND status = 'created'
        """, (
            razorpay_payment_id,
            gateway_payment.get("method"),
            payment_record["payment_id"]
        ))

        if cursor.rowcount != 1:

            raise Exception("Unable to update payment record.")


        # Update appointment status
        cursor.execute("""
            UPDATE appointments

            SET status = 'pending_approval'

            WHERE appointment_id = %s
            AND status = 'pending_payment'
        """, (appointment_id,))

        if cursor.rowcount != 1:

            raise Exception("Unable to update appointment status.")


        # Save both updates
        db.commit()


        # ==========================================
        # 8. PAYMENT SUCCESS
        # ==========================================

        session.pop("payment_booking", None)

        flash(
            "Payment successful! Your appointment is awaiting doctor approval.",
            "success"
        )

        return redirect(url_for("home.overview"))


    except Exception as error:

        if db:
            db.rollback()

        print("Payment Verification Error:", error)

        flash(
            "Unable to complete payment verification. Please contact support if money was deducted.",
            "error"
        )

        return redirect(url_for("home.doctors"))


    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()
