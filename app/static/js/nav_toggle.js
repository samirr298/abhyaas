(function () {
  function setOpen(open) {
    const shell = document.querySelector('.app-shell');
    const sidebar = document.querySelector('.app-sidebar');
    if (!sidebar) return;

    if (open) sidebar.classList.add('sidebar-open');
    else sidebar.classList.remove('sidebar-open');

    if (shell) shell.dataset.navOpen = open ? '1' : '0';
  }

  function isMobile() {
    return window.matchMedia('(max-width: 700px)').matches;
  }

  window.addEventListener('click', function (e) {
    const toggleBtn = e.target && e.target.closest && e.target.closest('#navToggleBtn');
    if (toggleBtn) {
      // Toggle ONLY on mobile
      if (!isMobile()) return;
      e.preventDefault();
      e.stopPropagation();

      const sidebar = document.querySelector('.app-sidebar');
      const open = !(sidebar && sidebar.classList.contains('sidebar-open'));
      setOpen(open);
      return;
    }

    // Click outside closes on mobile
    if (isMobile()) {
      const sidebar = document.querySelector('.app-sidebar');
      const nav = document.querySelector('.sidebar-nav');
      const clickedInSidebar = sidebar && (e.target === sidebar || sidebar.contains(e.target));
      if (!clickedInSidebar && nav && sidebar && sidebar.classList.contains('sidebar-open')) {
        setOpen(false);
      }
    }
  });

  window.addEventListener('resize', function () {
    if (!isMobile()) setOpen(false);
  });
})();

