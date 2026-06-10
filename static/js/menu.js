document.addEventListener("DOMContentLoaded", function () {

    const buttons = document.querySelectorAll(".menu-btn");
    const categories = document.querySelectorAll(".menu-category");

    buttons.forEach(button => {
        button.addEventListener("click", () => {

            // remove active
            buttons.forEach(btn => btn.classList.remove("active"));
            categories.forEach(cat => cat.classList.remove("active"));

            // activate current
            button.classList.add("active");
            const target = document.getElementById(button.dataset.category);

            if (target) {
                target.classList.add("active");
            }
        });
    });

});