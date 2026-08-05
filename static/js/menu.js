document.addEventListener("DOMContentLoaded", function () {
    const buttons = document.querySelectorAll(".menu-btn");
    const categories = document.querySelectorAll(".menu-category");
    const menuContent = document.querySelector(".menu-content-section");

    if (!buttons.length || !categories.length) {
        return;
    }

    buttons.forEach(button => {
        button.addEventListener("click", (event) => {
            event.preventDefault();

            buttons.forEach(btn => btn.classList.remove("active"));
            categories.forEach(cat => cat.classList.remove("active"));

            button.classList.add("active");
            const target = document.getElementById(button.dataset.category);

            if (target) {
                target.classList.add("active");
                history.replaceState(null, "", `#${target.id}`);
            }

            if (menuContent) {
                menuContent.scrollIntoView({
                    behavior: "smooth",
                    block: "start",
                });
            }
        });
    });

});
