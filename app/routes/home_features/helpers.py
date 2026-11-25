
from datetime import datetime, time as datetime_time, timedelta


# ==========================================
# HELPER: CONVERT TIME INTO MINUTES
# ==========================================

def time_to_minutes(value):

    if isinstance(value, timedelta):
        return int(value.total_seconds() // 60)

    if isinstance(value, datetime_time):
        return value.hour * 60 + value.minute

    parts = str(value).split(":")

    return int(parts[0]) * 60 + int(parts[1])


# ==========================================
# FORMAT DATABASE TIME
# ==========================================

def format_appointment_time(value):

    if isinstance(value, timedelta):

        total_minutes = int(value.total_seconds() // 60)

        hours, minutes = divmod(total_minutes, 60)

        return datetime_time(hours % 24, minutes).strftime("%I:%M %p")

    if hasattr(value, "strftime"):

        return value.strftime("%I:%M %p")

    return str(value)


# ==========================================
# FORMAT APPOINTMENT DATE AND TIME
# ==========================================

def get_appointment_datetime(appointment_date, appointment_time):

    if isinstance(appointment_time, timedelta):

        appointment_datetime = (
            datetime.combine(appointment_date, datetime_time.min)
            + appointment_time
        )

    elif isinstance(appointment_time, datetime_time):

        appointment_datetime = datetime.combine(
            appointment_date,
            appointment_time
        )

    else:

        parsed_time = datetime.strptime(
            str(appointment_time), "%H:%M:%S"
        ).time()

        appointment_datetime = datetime.combine(
            appointment_date,
            parsed_time
        )

    return appointment_datetime
