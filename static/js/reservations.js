document.addEventListener('DOMContentLoaded', function () {

    const form = document.getElementById(
        'reservation-form'
    );

    const messageBox = document.getElementById(
        'reservation-message'
    );

    form.addEventListener(
        'submit',
        function (e) {

            e.preventDefault();

            const formData = new FormData(
                form
            );

            fetch(
                window.location.href,
                {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                }
            )

            .then(response => response.json())

            .then(data => {

                if (data.success) {

                    messageBox.innerHTML = `
                        <div class="success-message">
                            ${data.message}
                        </div>
                    `;

                    form.reset();

                    window.scrollTo({
                        top: 0,
                        behavior: 'smooth'
                    });

                } else {

                    let errors = '';

                    for (const field in data.errors) {

                        errors += `
                            <p>${data.errors[field]}</p>
                        `;
                    }

                    messageBox.innerHTML = `
                        <div class="error-message">
                            ${errors}
                        </div>
                    `;
                }

            })

            .catch(error => {

                messageBox.innerHTML = `
                    <div class="error-message">
                        Something went wrong.
                        Please try again.
                    </div>
                `;

            });

        }
    );

});