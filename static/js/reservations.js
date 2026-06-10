document.addEventListener('DOMContentLoaded', function() {

    const form = document.getElementById('reservation-form');

    if (!form) return;

    form.addEventListener('submit', async function(e) {

        e.preventDefault();

        const formData = new FormData(form);

        const response = await fetch('', {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        const data = await response.json();

        const messageBox = document.getElementById(
            'reservation-message'
        );

        if (data.success) {

            messageBox.style.display = 'block';

            messageBox.className =
                'contact-message-box success-message';

            messageBox.innerHTML =
                '✨ Your reservation has been submitted successfully. We look forward to welcoming you.';

            form.reset();

            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });

        } else {

            messageBox.style.display = 'block';

            messageBox.className =
                'contact-message-box error-message';

            messageBox.innerHTML =
                'Please check your reservation details and try again.';

        }

    });

});