document.addEventListener("DOMContentLoaded", function () {
    /* 1. Sliding Navigation Pill */
    const nav = document.getElementById("mainNav");
    const slider = document.getElementById("navSliderPill");

    if (nav && slider) {
        const links = Array.from(nav.querySelectorAll("a"));
        const activeLink = nav.querySelector("a.active") || links[0];

        function moveSliderTo(target) {
            if (!target) {
                slider.style.opacity = "0";
                return;
            }
            slider.style.opacity = "1";
            slider.style.width = `${target.offsetWidth}px`;
            slider.style.transform = `translateX(${target.offsetLeft}px)`;
        }

        const prevTransition = slider.style.transition;
        slider.style.transition = "none";
        moveSliderTo(activeLink);
        slider.offsetHeight;
        slider.style.transition = prevTransition;

        links.forEach((link) => {
            link.addEventListener("mouseenter", () => moveSliderTo(link));
            link.addEventListener("focus", () => moveSliderTo(link));
        });

        nav.addEventListener("mouseleave", () => moveSliderTo(activeLink));
        window.addEventListener("resize", () => {
            const currentHovered = links.find((el) => el.matches(":hover"));
            moveSliderTo(currentHovered || activeLink);
        });
    }

    /* 2. Light / Dark Mode Toggle */
    const themeToggleBtn = document.getElementById("themeToggleBtn");
    const themeIcon = document.getElementById("themeIcon");
    const savedTheme = localStorage.getItem("hms_theme");

    function applyTheme(isDark) {
        document.body.classList.toggle("dark-mode", isDark);
        if (themeIcon) {
            themeIcon.className = isDark ? "fa-regular fa-sun" : "fa-regular fa-moon";
        }
        localStorage.setItem("hms_theme", isDark ? "dark" : "light");
    }

    if (savedTheme === "dark") {
        applyTheme(true);
    }

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener("click", function () {
            const isCurrentlyDark = document.body.classList.contains("dark-mode");
            applyTheme(!isCurrentlyDark);
        });
    }

    /* 3. Sliding Filter Tags Pill (Same Pattern as Navbar) */
    const tagsContainer = document.getElementById("doctorTagsContainer");
    const tagSlider = document.getElementById("tagSliderPill");

    if (tagsContainer && tagSlider) {
        const tags = Array.from(tagsContainer.querySelectorAll(".tag"));
        let activeTag = tagsContainer.querySelector(".tag.active") || tags[0];

        function moveTagSliderTo(target) {
            if (!target) {
                tagSlider.style.opacity = "0";
                return;
            }
            tagSlider.style.opacity = "1";
            tagSlider.style.width = `${target.offsetWidth}px`;
            tagSlider.style.transform = `translateX(${target.offsetLeft}px)`;
        }

        const prevTagTransition = tagSlider.style.transition;
        tagSlider.style.transition = "none";
        moveTagSliderTo(activeTag);
        tagSlider.offsetHeight;
        tagSlider.style.transition = prevTagTransition;

        tags.forEach((tag) => {
            tag.addEventListener("mouseenter", () => moveTagSliderTo(tag));
            tag.addEventListener("focus", () => moveTagSliderTo(tag));
            tag.addEventListener("click", () => {
                tags.forEach((t) => t.classList.remove("active"));
                tag.classList.add("active");
                activeTag = tag;
                moveTagSliderTo(activeTag);
            });
        });

        tagsContainer.addEventListener("mouseleave", () => moveTagSliderTo(activeTag));
        window.addEventListener("resize", () => {
            const hoveredTag = tags.find((el) => el.matches(":hover"));
            moveTagSliderTo(hoveredTag || activeTag);
        });
    }
});