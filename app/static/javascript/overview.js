
document.addEventListener("DOMContentLoaded", function () {

    // ==========================================
    // 1. GET DOCTOR SLIDER ELEMENTS
    // ==========================================

    const doctorTrack = document.getElementById("doctorSliderTrack");

    const previousButton = document.getElementById("doctorSliderPrev");

    const nextButton = document.getElementById("doctorSliderNext");


    // Stop if slider elements are unavailable
    if (!doctorTrack || !previousButton || !nextButton) {

        return;

    }


    // ==========================================
    // 2. GET SLIDER CARD WIDTH
    // ==========================================

    function getScrollAmount() {

        const firstCard = doctorTrack.querySelector(".doctor-slide-card");

        if (!firstCard) {

            return 280;

        }

        const cardWidth = firstCard.getBoundingClientRect().width;

        return cardWidth + 17;

    }


    // ==========================================
    // 3. UPDATE SLIDER BUTTONS
    // ==========================================

    function updateSliderButtons() {

        const maxScroll =
            doctorTrack.scrollWidth - doctorTrack.clientWidth;

        previousButton.disabled =
            doctorTrack.scrollLeft <= 2;

        nextButton.disabled =
            doctorTrack.scrollLeft >= maxScroll - 2;


        // Hide arrows when all cards fit on screen
        if (maxScroll <= 2) {

            previousButton.style.display = "none";

            nextButton.style.display = "none";

        } else {

            previousButton.style.display = "flex";

            nextButton.style.display = "flex";

        }

    }


    // ==========================================
    // 4. PREVIOUS DOCTORS
    // ==========================================

    previousButton.addEventListener("click", function () {

        doctorTrack.scrollBy({

            left: -getScrollAmount(),

            behavior: "smooth"

        });

    });


    // ==========================================
    // 5. NEXT DOCTORS
    // ==========================================

    nextButton.addEventListener("click", function () {

        doctorTrack.scrollBy({

            left: getScrollAmount(),

            behavior: "smooth"

        });

    });


    // ==========================================
    // 6. UPDATE BUTTONS ON SCROLL
    // ==========================================

    doctorTrack.addEventListener("scroll", updateSliderButtons);


    // ==========================================
    // 7. UPDATE BUTTONS ON WINDOW RESIZE
    // ==========================================

    window.addEventListener("resize", updateSliderButtons);


    // Initial button state
    updateSliderButtons();


});
