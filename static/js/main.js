if (window.location.pathname === '/' || window.location.pathname === '/home' || window.location.pathname === '/sprava_poslicci' || window.location.pathname === '/restaurace' || window.location.pathname === '/registrace' || window.location.pathname === '/sprava_restauraci' || window.location.pathname.includes('/sprava_restaurace') || window.location.pathname.includes('/restaurace') || window.location.pathname.includes('/nastaveni') || window.location.pathname === '/sprava_systemu' ||  window.location.pathname === '/prihlaseni' || window.location.pathname === '/domu' || window.location.pathname === '/nastaveni') {
    window.addEventListener('scroll', function() {
        const nav = document.querySelector('nav');
        if (nav) {
            if (window.scrollY > 400) {
                nav.classList.add('scrolled');
            } else {
                nav.classList.remove('scrolled');
            }
        }
    });
} else {
    window.onload = function() {
            const nav = document.querySelector('nav');
            if (nav) {
                nav.classList.add('scrolled');
            }
    };
}

