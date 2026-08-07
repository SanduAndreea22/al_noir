document.addEventListener('DOMContentLoaded', () => {
    const items = document.querySelectorAll('.reveal');
    if (!items.length) {
        return;
    }

    if (!('IntersectionObserver' in window)) {
        items.forEach((el) => el.classList.add('in-view'));
        return;
    }

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add('in-view');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.15, rootMargin: '0px 0px -60px 0px' });

    items.forEach((el) => observer.observe(el));
});
