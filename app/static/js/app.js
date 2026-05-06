/* Core UI Logic — AutoEval */

document.addEventListener('DOMContentLoaded', () => {
    // Auto-dismiss flash messages after 5 seconds
    document.querySelectorAll('.flash-message').forEach(msg => {
        setTimeout(() => {
            msg.style.opacity = '0';
            msg.style.transform = 'translateY(-10px)';
            setTimeout(() => msg.remove(), 300);
        }, 5000);
    });

    // Animate score bars on scroll
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const fill = entry.target;
                const width = fill.style.width;
                fill.style.width = '0%';
                requestAnimationFrame(() => {
                    requestAnimationFrame(() => {
                        fill.style.width = width;
                    });
                });
                observer.unobserve(fill);
            }
        });
    }, { threshold: 0.2 });

    document.querySelectorAll('.score-bar-fill').forEach(fill => observer.observe(fill));

    // Mobile sidebar close on link click
    document.querySelectorAll('.sidebar .nav-link').forEach(link => {
        link.addEventListener('click', () => {
            if (window.innerWidth <= 768) {
                document.querySelector('.sidebar').classList.remove('open');
            }
        });
    });
});
