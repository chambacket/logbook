document.addEventListener('DOMContentLoaded', function() {
    // Smooth scroll function
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const section = document.querySelector(this.getAttribute('href'));
            section.scrollIntoView({
                behavior: 'smooth'
            });
        });
    });

    // Highlight active section in navigation
    const sections = document.querySelectorAll('section');
    const navLinks = document.querySelectorAll('nav a');

    window.addEventListener('scroll', () => {
        let current = '';
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            if (scrollY >= (sectionTop - sectionHeight / 3)) {
                current = section.getAttribute('id');
            }
        });

        navLinks.forEach(link => {
            link.classList.remove('text-yellow-400');
            if (link.getAttribute('href').substring(1) === current) {
                link.classList.add('text-yellow-400');
            }
        });
    });
});