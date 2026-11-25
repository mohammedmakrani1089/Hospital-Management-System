
document.addEventListener("DOMContentLoaded", function () {

    // ==========================================
    // 1. GET HTML ELEMENTS
    // ==========================================

    const bookingCard = document.getElementById("bookingCard");

    if (!bookingCard) return;

    const dateInput = document.getElementById("appointmentDate");
    const slotsContainer = document.getElementById("slotsContainer");
    const message = document.getElementById("availabilityMessage");

    const selectedSlotLabel = document.getElementById("selectedSlotLabel");
    const continueButton = document.getElementById("continueBookingBtn");

    // Patient Details Elements
    const patientSection = document.getElementById("patientDetailsSection");

    const bookForSelf = document.getElementById("bookForSelf");
    const bookForOther = document.getElementById("bookForOther");

    const patientName = document.getElementById("patientName");
    const patientAge = document.getElementById("patientAge");
    const patientGender = document.getElementById("patientGender");
    const patientDetailsForm = document.getElementById("patientDetailsForm");

    // Hidden Booking Details
    const bookingDate = document.getElementById("bookingDate");
    const bookingStartTime = document.getElementById("bookingStartTime");
    const bookingEndTime = document.getElementById("bookingEndTime");

    const patientConfirmBtn = document.getElementById("patientConfirmBtn");

    // Patient Modal Elements
    const closePatientModalButton = document.getElementById("closePatientModal");
    const cancelPatientModalButton = document.getElementById("cancelPatientModal");

    const modalAppointmentDate = document.getElementById("modalAppointmentDate");
    const modalAppointmentTime = document.getElementById("modalAppointmentTime");

    
// Custom Calendar Elements
const customDatePicker = document.getElementById("customDatePicker");
const customDateTrigger = document.getElementById("customDateTrigger");
const selectedDateText = document.getElementById("selectedDateText");

const customCalendar = document.getElementById("customCalendar");
const calendarMonthLabel = document.getElementById("calendarMonthLabel");
const calendarDays = document.getElementById("calendarDays");

const calendarPrevMonth = document.getElementById("calendarPrevMonth");
const calendarNextMonth = document.getElementById("calendarNextMonth");
const calendarTodayButton = document.getElementById("calendarTodayButton");



    // Check required HTML elements
    if (
        !dateInput ||
        !slotsContainer ||
        !message ||
        !selectedSlotLabel ||
        !continueButton ||
        !patientSection ||
        !bookForSelf ||
        !bookForOther ||
        !patientName ||
        !patientAge ||
        !patientGender ||
        !bookingDate ||
        !bookingStartTime ||
        !bookingEndTime ||
        !closePatientModalButton ||
        !cancelPatientModalButton ||
        !modalAppointmentDate ||
        !modalAppointmentTime ||
        !customDatePicker ||
        !customDateTrigger ||
        !selectedDateText ||
        !customCalendar ||
        !calendarMonthLabel ||
        !calendarDays ||
        !calendarPrevMonth ||
        !calendarNextMonth ||
        !calendarTodayButton ||
        !patientDetailsForm ||
        !patientConfirmBtn 
        
    ) {
        console.error("Some booking HTML elements are missing!");
        return;
    }


    // ==========================================
    // 2. GET DOCTOR SCHEDULES FROM FLASK
    // ==========================================

    let schedules = [];

    try {

        schedules = JSON.parse(
            bookingCard.dataset.schedules || "[]"
        );

    } catch (error) {

        console.error("Unable to load doctor schedules:", error);

        message.textContent = "Unable to load doctor availability.";

        return;

    }


    // ==========================================
    // 3. GET LOGGED-IN USER DETAILS
    // ==========================================

    const userName = bookingCard.dataset.userName || "";
    const userAge = bookingCard.dataset.userAge || "";
    const userGender = bookingCard.dataset.userGender || "";



// ==========================================
// 4. SET APPOINTMENT DATE RANGE & CUSTOM CALENDAR
// ==========================================

// Today's date
const today = new Date();

const todayDate = new Date(
    today.getFullYear(),
    today.getMonth(),
    today.getDate()
);


// Maximum booking date: Next 30 days
const maxBookingDate = new Date(todayDate);

maxBookingDate.setDate(maxBookingDate.getDate() + 30);


// Convert date into YYYY-MM-DD
function toLocalDateString(date) {

    const year = date.getFullYear();

    const month = String(date.getMonth() + 1).padStart(2, "0");

    const day = String(date.getDate()).padStart(2, "0");

    return `${year}-${month}-${day}`;

}


const localToday = toLocalDateString(todayDate);

const localMaxDate = toLocalDateString(maxBookingDate);


// Keep date range on hidden input also
dateInput.min = localToday;
dateInput.max = localMaxDate;


// Clear invalid previously selected date
if (
    dateInput.value &&
    (dateInput.value < localToday || dateInput.value > localMaxDate)
) {

    dateInput.value = "";

}


// Display date in readable format
function formatDisplayDate(dateString) {

    const [year, month, day] = dateString.split("-").map(Number);

    return new Date(year, month - 1, day).toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric"
    });

}


// Default calendar month
let calendarViewDate = new Date(
    todayDate.getFullYear(),
    todayDate.getMonth(),
    1
);


// Show previously selected date, if valid
selectedDateText.textContent = dateInput.value
    ? formatDisplayDate(dateInput.value)
    : "Select appointment date";


// Close calendar
function closeCustomCalendar() {

    customCalendar.hidden = true;

    customDateTrigger.setAttribute("aria-expanded", "false");

}


// Generate calendar
function renderCustomCalendar() {

    calendarDays.innerHTML = "";

    const year = calendarViewDate.getFullYear();

    const month = calendarViewDate.getMonth();

    calendarMonthLabel.textContent = new Date(
        year,
        month,
        1
    ).toLocaleDateString("en-IN", {
        month: "long",
        year: "numeric"
    });


    // Disable month navigation outside booking range
    const currentMonth = new Date(
        todayDate.getFullYear(),
        todayDate.getMonth(),
        1
    );

    const lastMonth = new Date(
        maxBookingDate.getFullYear(),
        maxBookingDate.getMonth(),
        1
    );

    const displayedMonth = new Date(year, month, 1);

    calendarPrevMonth.disabled = displayedMonth <= currentMonth;

    calendarNextMonth.disabled = displayedMonth >= lastMonth;


    // First day of month
    const firstDay = new Date(year, month, 1).getDay();

    // Total days in month
    const totalDays = new Date(year, month + 1, 0).getDate();


    // Empty spaces before first date
    for (let i = 0; i < firstDay; i++) {

        const emptyDay = document.createElement("span");

        emptyDay.className = "calendar-empty";

        calendarDays.appendChild(emptyDay);

    }


    // Create calendar dates
    for (let day = 1; day <= totalDays; day++) {

        const currentDate = new Date(year, month, day);

        const dateValue = toLocalDateString(currentDate);

        const dayButton = document.createElement("button");

        dayButton.type = "button";

        dayButton.className = "calendar-day";

        dayButton.textContent = day;


        // Disable dates outside next 30 days
        if (dateValue < localToday || dateValue > localMaxDate) {

            dayButton.disabled = true;

        }


        // Today's date styling
        if (dateValue === localToday) {

            dayButton.classList.add("today");

        }


        // Selected date styling
        if (dateValue === dateInput.value) {

            dayButton.classList.add("selected");

        }


        // Select date
        dayButton.addEventListener("click", function () {

            dateInput.value = dateValue;

            selectedDateText.textContent = formatDisplayDate(dateValue);

            // Trigger existing appointment slot generation
            dateInput.dispatchEvent(
                new Event("change", { bubbles: true })
            );

            closeCustomCalendar();

        });


        calendarDays.appendChild(dayButton);

    }

}


// Open and close calendar
customDateTrigger.addEventListener("click", function () {

    customCalendar.hidden = !customCalendar.hidden;

    customDateTrigger.setAttribute(
        "aria-expanded",
        String(!customCalendar.hidden)
    );

    if (!customCalendar.hidden) {

        renderCustomCalendar();

    }

});


// Previous month
calendarPrevMonth.addEventListener("click", function () {

    if (calendarPrevMonth.disabled) return;

    calendarViewDate = new Date(
        calendarViewDate.getFullYear(),
        calendarViewDate.getMonth() - 1,
        1
    );

    renderCustomCalendar();

});


// Next month
calendarNextMonth.addEventListener("click", function () {

    if (calendarNextMonth.disabled) return;

    calendarViewDate = new Date(
        calendarViewDate.getFullYear(),
        calendarViewDate.getMonth() + 1,
        1
    );

    renderCustomCalendar();

});


// Today button
calendarTodayButton.addEventListener("click", function () {

    dateInput.value = localToday;

    selectedDateText.textContent = formatDisplayDate(localToday);

    dateInput.dispatchEvent(
        new Event("change", { bubbles: true })
    );

    closeCustomCalendar();

});


// Close calendar when clicking outside
document.addEventListener("click", function (event) {

    if (!customDatePicker.contains(event.target)) {

        closeCustomCalendar();

    }

});



    // ==========================================
    // 5. CONVERT TIME INTO MINUTES
    // ==========================================

    function toMinutes(time) {

        const parts = time.split(":");

        const hours = Number(parts[0]);
        const minutes = Number(parts[1]);

        return hours * 60 + minutes;

    }


    // ==========================================
    // 6. CONVERT TIME INTO AM/PM FORMAT
    // ==========================================

    function formatTime(minutes) {

        const hours = Math.floor(minutes / 60);
        const mins = minutes % 60;

        const date = new Date();

        date.setHours(hours, mins, 0, 0);

        return date.toLocaleTimeString("en-IN", {

            hour: "2-digit",
            minute: "2-digit",
            hour12: true

        });

    }


    // ==========================================
    // 7. RESET SELECTED SLOT AND PATIENT FORM
    // ==========================================

    let selectedSlot = null;

    function resetSelection() {

        selectedSlot = null;

        selectedSlotLabel.textContent = "Not Selected";

        continueButton.disabled = true;

        patientSection.hidden = true;

    }


    // ==========================================
    // 8. DATE SELECTION EVENT
    // ==========================================

    dateInput.addEventListener("change", function () {

        // Clear previous slots
        slotsContainer.innerHTML = "";

        resetSelection();

        const selectedDate = this.value;
        
// Check appointment date range
if (selectedDate && (
    selectedDate < localToday ||
    selectedDate > localMaxDate
)) {

    this.value = "";

    selectedDateText.textContent = "Select appointment date";

    message.textContent = "Please select a date within the next 30 days.";

    message.className = "availability-message holiday";

    slotsContainer.innerHTML =
        '<p class="no-slots-message">Please select a valid appointment date.</p>';

    return;

}


// Update selected date display
if (selectedDate) {

    selectedDateText.textContent = formatDisplayDate(selectedDate);

}


        if (!selectedDate) {

            message.textContent = "Please select a date.";

            return;

        }


        // Get selected weekday
        const weekday = new Date(
            selectedDate + "T12:00:00"
        ).toLocaleDateString("en-US", {

            weekday: "long"

        });


        // Get schedules for selected weekday
        const daySchedules = schedules.filter(schedule =>

            schedule.day_of_week === weekday

        );


        // ==========================================
        // 9. CHECK DOCTOR HOLIDAY
        // ==========================================

        const holiday = daySchedules.some(schedule =>

            schedule.is_holiday

        );

        if (holiday) {

            message.textContent =
                "Doctor is not available on " + weekday + " (Weekly Holiday).";

            message.className = "availability-message holiday";

            slotsContainer.innerHTML =
                '<p class="no-slots-message">No appointment slots available.</p>';

            return;

        }


        // ==========================================
        // 10. GET AVAILABLE SHIFTS
        // ==========================================

        const availableShifts = daySchedules.filter(schedule =>

            schedule.is_available &&
            !schedule.is_holiday &&
            schedule.start_time &&
            schedule.end_time &&
            Number(schedule.slot_duration) > 0

        );


        if (availableShifts.length === 0) {

            message.textContent =
                "Doctor is not available on the selected date.";

            message.className = "availability-message holiday";

            slotsContainer.innerHTML =
                '<p class="no-slots-message">No appointment slots available.</p>';

            return;

        }


        message.textContent =
            "Available appointment timings for " + weekday + ".";

        message.className = "availability-message available";


        // ==========================================
        // 11. GENERATE TIME SLOTS
        // ==========================================

        availableShifts.forEach((shift, index) => {

            const start = toMinutes(shift.start_time);
            const end = toMinutes(shift.end_time);

            const duration = Number(shift.slot_duration);

            // Skip invalid shifts
            if (end <= start || duration <= 0) return;


            // Create shift section
            const shiftSection = document.createElement("div");

            const heading = document.createElement("h4");

            heading.className = "shift-heading";

            const shiftName = start < 12 * 60
                ? "Morning Shift"
                : start < 17 * 60
                    ? "Afternoon Shift"
                    : "Evening Shift";

            heading.textContent =
                shiftName + " - Shift " + (index + 1);

            shiftSection.appendChild(heading);


            // Create slots grid
            const grid = document.createElement("div");

            grid.className = "time-slots-grid";


            // Generate 30-minute slots
            for (
                let current = start;
                current + duration <= end;
                current += duration
            ) {


                // Hide past slots for today's date
                if (selectedDate === localToday) {

                    const now = new Date();

                    const currentTime =
                        now.getHours() * 60 + now.getMinutes();

                    if (current <= currentTime) continue;

                }


                // Create slot button
                const slotButton = document.createElement("button");

                slotButton.type = "button";

                slotButton.className = "time-slot";

                slotButton.textContent = formatTime(current);


                // Save slot starting time
                slotButton.dataset.start =

                    String(Math.floor(current / 60)).padStart(2, "0") +
                    ":" +
                    String(current % 60).padStart(2, "0") +
                    ":00";


                // Save slot ending time
                const slotEnd = current + duration;

                slotButton.dataset.end =

                    String(Math.floor(slotEnd / 60)).padStart(2, "0") +
                    ":" +
                    String(slotEnd % 60).padStart(2, "0") +
                    ":00";


                // ==========================================
                // 12. SLOT SELECTION EVENT
                // ==========================================

                slotButton.addEventListener("click", function () {

                    // Remove previous selection
                    slotsContainer.querySelectorAll(".time-slot").forEach(slot => {

                        slot.classList.remove("selected");

                    });


                    // Select current slot
                    this.classList.add("selected");


                    // Store selected slot details
                    selectedSlot = {

                        date: selectedDate,

                        start_time: this.dataset.start,

                        end_time: this.dataset.end

                    };


                    // Display selected time
                    selectedSlotLabel.textContent =

                        formatTime(current) +
                        " - " +
                        formatTime(slotEnd);


                    // Enable Continue Button
                    continueButton.disabled = false;


                    // Hide patient form until Continue
                    patientSection.hidden = true;

                });


                grid.appendChild(slotButton);

            }


            // Add shift only if slots exist
            if (grid.children.length > 0) {

                shiftSection.appendChild(grid);

                slotsContainer.appendChild(shiftSection);

            }

        });


        // ==========================================
        // 13. CHECK IF ANY FUTURE SLOTS EXIST
        // ==========================================

        if (!slotsContainer.children.length) {

            message.textContent =
                "No future slots available for the selected date.";

            message.className = "availability-message holiday";

            slotsContainer.innerHTML =
                '<p class="no-slots-message">Please select another date.</p>';

        }

    });



// ==========================================
// 14. CONTINUE BUTTON - OPEN PATIENT DETAILS
// ==========================================

continueButton.addEventListener("click", function () {

    if (!selectedSlot) return;

    // Save selected appointment details
    bookingDate.value = selectedSlot.date;
    bookingStartTime.value = selectedSlot.start_time;
    bookingEndTime.value = selectedSlot.end_time;

    // Default selection: Myself
    bookForSelf.checked = true;
    bookForOther.checked = false;

    // Automatically fill logged-in user details
    updatePatientDetails();

    // Show appointment summary in modal
    modalAppointmentDate.textContent = selectedSlot.date;

    const startTime = formatTime(toMinutes(selectedSlot.start_time));
    const endTime = formatTime(toMinutes(selectedSlot.end_time));

    modalAppointmentTime.textContent = startTime + " - " + endTime;

    // Open Patient Details Modal
    patientSection.hidden = false;

    document.body.classList.add("modal-open");

});



    // ==========================================
// 15. SELF / SOMEONE ELSE SELECTION
// ==========================================

function updatePatientDetails() {

    const selfOption = bookForSelf.closest(".booking-type-option");
    const otherOption = bookForOther.closest(".booking-type-option");

    // Update selected green color
    selfOption.classList.toggle("selected", bookForSelf.checked);
    otherOption.classList.toggle("selected", bookForOther.checked);

    if (bookForSelf.checked) {

        // Fill logged-in user's information
        patientName.value = userName;
        patientAge.value = userAge;
        patientGender.value = userGender;

    }

    else if (bookForOther.checked) {

        // Clear fields for another patient
        patientName.value = "";
        patientAge.value = "";
        patientGender.value = "";

    }

}

bookForSelf.addEventListener("change", updatePatientDetails);
bookForOther.addEventListener("change", updatePatientDetails);



    // ==========================================
    // 16. PATIENT DETAILS VALIDATION
    // ==========================================

    patientDetailsForm.addEventListener("submit", function (event) {


        // Check appointment slot
        if (!selectedSlot) {

            alert("Please select an appointment slot first.");
            event.preventDefault();

            return;

        }


        // Check patient name
        if (!patientName.value.trim()) {

            alert("Please enter patient name.");

            patientName.focus();
            event.preventDefault();

            return;

        }


        // Check patient age
        if (patientAge.value === "") {

            alert("Please enter patient age.");

            patientAge.focus();
            event.preventDefault();

            return;

        }


        const age = Number(patientAge.value);

        if (!Number.isInteger(age) || age < 0 || age > 120) {

            alert("Please enter a valid age between 0 and 120.");

            patientAge.focus();
            event.preventDefault();

            return;

        }


        // Check patient gender
        if (!patientGender.value) {

            alert("Please select patient gender.");

            patientGender.focus();
            event.preventDefault();
            return;

        }


        // ==========================================
        // 17. BOOKING DETAILS VALIDATED
        // ==========================================

        bookingDate.value = selectedSlot.date;

        bookingStartTime.value = selectedSlot.start_time;

        bookingEndTime.value = selectedSlot.end_time;


        alert(
            "Patient details completed successfully!\n\n" +
            "Next step: Appointment booking and payment."
        );

    });

// ==========================================
// 18. CLOSE PATIENT DETAILS MODAL
// ==========================================

function closePatientDetailsModal() {

    patientSection.hidden = true;

    document.body.classList.remove("modal-open");

}


// Close using X button
closePatientModalButton.addEventListener("click", function () {

    closePatientDetailsModal();

});


// Close using Back button
cancelPatientModalButton.addEventListener("click", function () {

    closePatientDetailsModal();

});


// Close when clicking outside the modal
patientSection.addEventListener("click", function (event) {

    if (event.target === patientSection) {

        closePatientDetailsModal();

    }

});


// Close using Escape key
document.addEventListener("keydown", function (event) {

    if (event.key === "Escape" && !patientSection.hidden) {

        closePatientDetailsModal();

    }

});
});
