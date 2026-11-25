
document.addEventListener("DOMContentLoaded", function () {


    // ==========================================
    // 1. APPOINTMENT FILTERS
    // ==========================================

    const filterTabs = document.getElementById("appointmentFilterTabs");

    const appointmentCards = document.querySelectorAll(".appointment-card");

    const emptyMessage = document.getElementById("appointmentFilterEmpty");


    if (filterTabs && emptyMessage) {

        const filterButtons = filterTabs.querySelectorAll(
            ".appointment-filter"
        );


        function filterAppointments(selectedFilter) {

            let visibleCount = 0;

            appointmentCards.forEach(function (card) {

                const category = card.dataset.category;

                const shouldDisplay =
                    selectedFilter === "all" ||
                    category === selectedFilter;

                card.hidden = !shouldDisplay;

                if (shouldDisplay) {

                    visibleCount++;

                }

            });


            // Show empty message
            emptyMessage.hidden = visibleCount > 0;


            // Update active filter
            filterButtons.forEach(function (button) {

                button.classList.toggle(
                    "active",
                    button.dataset.filter === selectedFilter
                );

            });

        }


        // Filter button events
        filterButtons.forEach(function (button) {

            button.addEventListener("click", function () {

                filterAppointments(this.dataset.filter);

            });

        });


        // Default filter
        filterAppointments("all");

    }



    // ==========================================
    // 2. GET CANCELLATION MODAL ELEMENTS
    // ==========================================

    const cancelModal = document.getElementById(
        "cancelAppointmentModal"
    );

    const closeCancelModal = document.getElementById(
        "closeCancelModal"
    );

    const keepAppointmentButton = document.getElementById(
        "keepAppointmentButton"
    );

    const cancelAppointmentId = document.getElementById(
        "cancelAppointmentId"
    );

    const cancelDoctorName = document.getElementById(
        "cancelDoctorName"
    );

    const cancelAppointmentDate = document.getElementById(
        "cancelAppointmentDate"
    );

    const cancelConsultationFee = document.getElementById(
        "cancelConsultationFee"
    );

    const cancelRefundPercentage = document.getElementById(
        "cancelRefundPercentage"
    );

    const cancelEstimatedRefund = document.getElementById(
        "cancelEstimatedRefund"
    );

    const cancelRefundNote = document.getElementById(
        "cancelRefundNote"
    );



    // ==========================================
    // 3. FORMAT CURRENCY
    // ==========================================

    function formatCurrency(amount) {

        return new Intl.NumberFormat("en-IN", {

            style: "currency",

            currency: "INR",

            minimumFractionDigits: 2,

            maximumFractionDigits: 2

        }).format(amount);

    }



    // ==========================================
    // 4. CALCULATE REFUND PREVIEW
    // ==========================================

    function calculateRefund(fee) {

        let percentage = 0;


        if (fee >= 100 && fee <= 300) {

            percentage = 50;

        }

        else if (fee > 300 && fee <= 500) {

            percentage = 60;

        }

        else if (fee > 500) {

            percentage = 70;

        }


        const refund = Math.round(
            (fee * percentage / 100 + Number.EPSILON) * 100
        ) / 100;


        return {

            percentage: percentage,

            refund: refund

        };

    }



    // ==========================================
    // 5. OPEN CANCELLATION MODAL
    // ==========================================

    if (cancelModal) {

        document.querySelectorAll(
            ".appointment-cancel-btn"
        ).forEach(function (button) {

            button.addEventListener("click", function () {

                const appointmentId = this.dataset.appointmentId;

                const doctorName = this.dataset.doctorName;

                const appointmentDate = this.dataset.date;

                const fee = Number(this.dataset.fee);


                // Validate button data
                if (
                    !appointmentId ||
                    !Number.isFinite(fee) ||
                    fee < 0
                ) {

                    console.error("Invalid cancellation details.");

                    return;

                }


                // Calculate refund
                const refundDetails = calculateRefund(fee);


                // Fill modal details
                cancelAppointmentId.value = appointmentId;

                cancelDoctorName.textContent = doctorName || "-";

                cancelAppointmentDate.textContent =
                    appointmentDate || "-";

                cancelConsultationFee.textContent =
                    formatCurrency(fee);


                if (refundDetails.percentage > 0) {

                    cancelRefundPercentage.textContent =
                        refundDetails.percentage + "%";

                    cancelEstimatedRefund.textContent =
                        formatCurrency(refundDetails.refund);

                    cancelRefundNote.textContent =
                        "This is an estimated refund. Its status will remain pending until further processing.";

                }

                else {

                    cancelRefundPercentage.textContent =
                        "Manual Review";

                    cancelEstimatedRefund.textContent =
                        "To be reviewed";

                    cancelRefundNote.textContent =
                        "The refund policy for consultation fees below ₹100 has not been defined. Manual review will be required.";

                }


                // Open modal
                cancelModal.hidden = false;

                document.body.classList.add("cancel-modal-open");

            });

        });



        // ==========================================
        // 6. CLOSE CANCELLATION MODAL
        // ==========================================

        function closeCancellationWindow() {

            cancelModal.hidden = true;

            document.body.classList.remove("cancel-modal-open");

        }


        // Close using X button
        if (closeCancelModal) {

            closeCancelModal.addEventListener(
                "click",
                closeCancellationWindow
            );

        }


        // Close using Keep Appointment
        if (keepAppointmentButton) {

            keepAppointmentButton.addEventListener(
                "click",
                closeCancellationWindow
            );

        }


        // Close outside modal
        cancelModal.addEventListener("click", function (event) {

            if (event.target === cancelModal) {

                closeCancellationWindow();

            }

        });


        // Close using Escape
        document.addEventListener("keydown", function (event) {

            if (
                event.key === "Escape" &&
                !cancelModal.hidden
            ) {

                closeCancellationWindow();

            }

        });

    }



    // ==========================================
    // 7. GET RESCHEDULE MODAL ELEMENTS
    // ==========================================

    const rescheduleModal = document.getElementById(
        "rescheduleAppointmentModal"
    );

    const rescheduleForm = document.getElementById(
        "rescheduleAppointmentForm"
    );

    const rescheduleId = document.getElementById(
        "rescheduleAppointmentId"
    );

    const rescheduleDoctor = document.getElementById(
        "rescheduleDoctorName"
    );

    const rescheduleCurrentDate = document.getElementById(
        "rescheduleCurrentDate"
    );

    const rescheduleDate = document.getElementById(
        "rescheduleDate"
    );

    const rescheduleTime = document.getElementById(
        "rescheduleTime"
    );

    const closeRescheduleModal = document.getElementById(
        "closeRescheduleModal"
    );

    const closeRescheduleButton = document.getElementById(
        "closeRescheduleButton"
    );



    // ==========================================
    // 7.1 CHECK RESCHEDULE ELEMENTS
    // ==========================================

    if (
        rescheduleModal &&
        rescheduleForm &&
        rescheduleId &&
        rescheduleDoctor &&
        rescheduleCurrentDate &&
        rescheduleDate &&
        rescheduleTime
    ) {


        // ==========================================
        // 7.2 SET APPOINTMENT DATE RANGE
        // ==========================================

        const today = new Date();

        const localToday = new Date(

            today.getTime() -
            today.getTimezoneOffset() * 60000

        ).toISOString().split("T")[0];


        // Maximum date: Next 30 days
        const maxDate = new Date(today);

        maxDate.setDate(maxDate.getDate() + 30);


        const localMaxDate = new Date(

            maxDate.getTime() -
            maxDate.getTimezoneOffset() * 60000

        ).toISOString().split("T")[0];


        rescheduleDate.min = localToday;

        rescheduleDate.max = localMaxDate;



        // ==========================================
        // 7.3 OPEN RESCHEDULE MODAL
        // ==========================================

        document.querySelectorAll(
            ".appointment-reschedule-btn"
        ).forEach(function (button) {

            button.addEventListener("click", function () {

                // Get appointment details
                const appointmentId = this.dataset.appointmentId;

                const doctorName = this.dataset.doctorName;

                const currentDate = this.dataset.currentDate;


                if (!appointmentId) {

                    console.error("Appointment ID missing.");

                    return;

                }


                // Fill modal
                rescheduleId.value = appointmentId;

                rescheduleDoctor.textContent =
                    doctorName || "-";

                rescheduleCurrentDate.textContent =
                    currentDate || "-";


                // Clear previous selections
                rescheduleDate.value = "";

                rescheduleTime.value = "";


                // Open modal
                rescheduleModal.hidden = false;

                document.body.classList.add("cancel-modal-open");

            });

        });



        // ==========================================
        // 7.4 CLOSE RESCHEDULE MODAL
        // ==========================================

        function closeRescheduleWindow() {

            rescheduleModal.hidden = true;

            document.body.classList.remove("cancel-modal-open");

        }


        // Close using X button
        if (closeRescheduleModal) {

            closeRescheduleModal.addEventListener(
                "click",
                closeRescheduleWindow
            );

        }


        // Close using Back button
        if (closeRescheduleButton) {

            closeRescheduleButton.addEventListener(
                "click",
                closeRescheduleWindow
            );

        }


        // Close by clicking outside
        rescheduleModal.addEventListener("click", function (event) {

            if (event.target === rescheduleModal) {

                closeRescheduleWindow();

            }

        });


        // Close using Escape
        document.addEventListener("keydown", function (event) {

            if (
                event.key === "Escape" &&
                !rescheduleModal.hidden
            ) {

                closeRescheduleWindow();

            }

        });



        // ==========================================
        // 7.5 VALIDATE RESCHEDULE FORM
        // ==========================================

        rescheduleForm.addEventListener("submit", function (event) {

            const selectedDate = rescheduleDate.value;

            const selectedTime = rescheduleTime.value;


            // Check date and time
            if (!selectedDate || !selectedTime) {

                event.preventDefault();

                alert("Please select a new appointment date and time.");

                return;

            }


            // Check 30-day date range
            if (
                selectedDate < localToday ||
                selectedDate > localMaxDate
            ) {

                event.preventDefault();

                alert(
                    "Please select a date within the next 30 days."
                );

                return;

            }


            // Check appointment ID
            if (!rescheduleId.value) {

                event.preventDefault();

                alert("Invalid appointment. Please try again.");

                return;

            }

        });

    }


});
