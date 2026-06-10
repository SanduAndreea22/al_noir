document.addEventListener("DOMContentLoaded", function () {
    const revealElements = document.querySelectorAll(".reveal");

    function handleReveal() {
        const triggerBottom = window.innerHeight - 100;

        revealElements.forEach((element) => {
            const elementTop = element.getBoundingClientRect().top;

            if (elementTop < triggerBottom) {
                element.classList.add("active");
            }
        });
    }

    window.addEventListener("scroll", handleReveal);
    handleReveal();
});

document.addEventListener("DOMContentLoaded", function () {
    /* =========================
       REVEAL ON SCROLL
    ========================= */
    const revealElements = document.querySelectorAll(".reveal");

    function handleReveal() {
        const triggerBottom = window.innerHeight - 100;

        revealElements.forEach((element) => {
            const elementTop = element.getBoundingClientRect().top;

            if (elementTop < triggerBottom) {
                element.classList.add("active");
            }
        });
    }

    window.addEventListener("scroll", handleReveal);
    handleReveal();

    /* =========================
       CONTACT FORM AJAX
    ========================= */
    const contactForm = document.getElementById("contact-form");

    if (contactForm) {
        const messageBox = document.getElementById("form-message");
        const submitBtn = document.getElementById("submit-btn");
        const btnText = submitBtn.querySelector(".btn-text");
        const btnLoading = submitBtn.querySelector(".btn-loading");

        const fields = ["name", "email", "phone", "subject", "message"];

        function clearErrors() {
            fields.forEach((field) => {
                const input = document.getElementById(`id_${field}`);
                const errorBox = document.getElementById(`error-${field}`);

                if (input) {
                    input.classList.remove("input-error");
                }

                if (errorBox) {
                    errorBox.textContent = "";
                }
            });
        }

        function showMessage(type, text) {
            messageBox.className = `contact-message-box ${type}`;
            messageBox.textContent = text;
            messageBox.style.display = "block";
            messageBox.style.opacity = "1";
        }

        function setLoading(isLoading) {
            if (isLoading) {
                submitBtn.classList.add("is-loading");
                btnText.style.display = "none";
                btnLoading.style.display = "inline";
            } else {
                submitBtn.classList.remove("is-loading");
                btnText.style.display = "inline";
                btnLoading.style.display = "none";
            }
        }

        contactForm.addEventListener("submit", function (e) {
            e.preventDefault();

            clearErrors();
            messageBox.style.display = "none";
            setLoading(true);

            const formData = new FormData(contactForm);

            fetch("", {
                method: "POST",
                body: formData,
                headers: {
                    "X-Requested-With": "XMLHttpRequest"
                }
            })
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        throw data;
                    }
                    return data;
                })
                .then((data) => {
                    contactForm.reset();
                    showMessage("success", data.message || "Your message has been sent successfully.");
                    setLoading(false);

                    setTimeout(() => {
                        messageBox.style.opacity = "0";
                        setTimeout(() => {
                            messageBox.style.display = "none";
                            messageBox.style.opacity = "1";
                        }, 300);
                    }, 3500);
                })
                .catch((data) => {
                    setLoading(false);

                    if (data.errors) {
                        showMessage("error", "Please correct the highlighted fields.");

                        Object.keys(data.errors).forEach((field) => {
                            const input = document.getElementById(`id_${field}`);
                            const errorBox = document.getElementById(`error-${field}`);

                            if (input) {
                                input.classList.add("input-error");
                            }

                            if (errorBox) {
                                errorBox.textContent = data.errors[field][0].message || data.errors[field][0];
                            }
                        });
                    } else {
                        showMessage("error", "Something went wrong. Please try again.");
                    }
                });
        });
    }
});

/* =========================
   REVIEWS FORM AJAX
========================= */
const reviewForm = document.getElementById("review-form");

if (reviewForm) {
    const messageBox = document.getElementById("review-message");
    const submitBtn = document.getElementById("review-submit-btn");
    const btnText = submitBtn.querySelector(".btn-text");
    const btnLoading = submitBtn.querySelector(".btn-loading");

    const fields = ["name", "email", "review_text", "rating"];

    function clearReviewErrors() {
        fields.forEach((field) => {
            const input = document.getElementById(`id_${field}`);
            const errorBox = document.getElementById(`error-${field}`);

            if (input) {
                input.classList.remove("input-error");
            }

            if (errorBox) {
                errorBox.textContent = "";
            }
        });
    }

    function showReviewMessage(type, text) {
        messageBox.className = `contact-message-box ${type}`;
        messageBox.textContent = text;
        messageBox.style.display = "block";
        messageBox.style.opacity = "1";
    }

    function setReviewLoading(isLoading) {
        if (isLoading) {
            submitBtn.classList.add("is-loading");
            btnText.style.display = "none";
            btnLoading.style.display = "inline";
        } else {
            submitBtn.classList.remove("is-loading");
            btnText.style.display = "inline";
            btnLoading.style.display = "none";
        }
    }

    reviewForm.addEventListener("submit", function (e) {
        e.preventDefault();

        clearReviewErrors();
        messageBox.style.display = "none";
        setReviewLoading(true);

        const formData = new FormData(reviewForm);

        fetch("", {
            method: "POST",
            body: formData,
            headers: {
                "X-Requested-With": "XMLHttpRequest"
            }
        })
            .then(async (response) => {
                const data = await response.json();
                if (!response.ok) {
                    throw data;
                }
                return data;
            })
            .then((data) => {
                reviewForm.reset();
                showReviewMessage("success", data.message || "Thank you! Your review will be visible after approval.");
                setReviewLoading(false);

                setTimeout(() => {
                    messageBox.style.opacity = "0";
                    setTimeout(() => {
                        messageBox.style.display = "none";
                        messageBox.style.opacity = "1";
                    }, 300);
                }, 3500);
            })
            .catch((data) => {
                setReviewLoading(false);

                if (data.errors) {
                    showReviewMessage("error", "Please correct the highlighted fields.");

                    Object.keys(data.errors).forEach((field) => {
                        const input = document.getElementById(`id_${field}`);
                        const errorBox = document.getElementById(`error-${field}`);

                        if (input) {
                            input.classList.add("input-error");
                        }

                        if (errorBox) {
                            errorBox.textContent = data.errors[field][0].message || data.errors[field][0];
                        }
                    });
                } else {
                    showReviewMessage("error", "Something went wrong. Please try again.");
                }
            });
    });
}

