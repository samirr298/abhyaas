document.addEventListener('DOMContentLoaded', function () {
  // password toggle
  document.querySelectorAll('.pw-toggle').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var row = btn.parentElement;
      var input = row.querySelector('input');
      if (!input) return;
      if (input.type === 'password') { input.type = 'text'; btn.textContent = '🙈'; }
      else { input.type = 'password'; btn.textContent = '👁️'; }
    });
  });

  // simple client-side validation handler
  function attachFormValidation(selector) {
    var form = document.querySelector(selector);
    if (!form) return;
    form.addEventListener('submit', function (e) {
      var valid = true;
      // remove old errors
      form.querySelectorAll('.form-error').forEach(function (el) { el.remove(); });
      form.querySelectorAll('[required]').forEach(function (el) {
        if (!el.value || el.value.trim() === '') {
          valid = false;
          var err = document.createElement('div'); err.className = 'form-error'; err.textContent = 'This field is required';
          el.parentNode.appendChild(err);
        }
      });
      // email format basic check
      var email = form.querySelector('input[type="email"]');
      if (email && email.value) {
        var re = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
        if (!re.test(email.value)) { valid = false; var err = document.createElement('div'); err.className = 'form-error'; err.textContent = 'Enter a valid email'; email.parentNode.appendChild(err); }
      }
      if (!valid) { e.preventDefault(); }
    });
  }

  function attachPasswordFormValidation() {
    var form = document.querySelector('#passwordForm');
    if (!form) return;

    var newPassword = document.getElementById('newPassword');
    var confirmPassword = document.getElementById('confirmPassword');
    var errorText = document.getElementById('errorText');

    if (!newPassword || !confirmPassword || !errorText) return;

    function validatePasswords() {
      if (newPassword.value !== confirmPassword.value) {
        errorText.style.display = 'block';
        confirmPassword.style.borderColor = 'var(--error-color)';
        return false;
      }

      errorText.style.display = 'none';
      confirmPassword.style.borderColor = 'var(--border-color)';
      return true;
    }

    confirmPassword.addEventListener('input', validatePasswords);
    newPassword.addEventListener('input', validatePasswords);

    form.addEventListener('submit', function (event) {
      if (!validatePasswords()) {
        event.preventDefault();
      }
    });
  }

  function setTheme(theme) {
    var root = document.documentElement;
    var current = theme === 'dark' ? 'dark' : 'light';
    root.classList.toggle('theme-dark', current === 'dark');
    var btn = document.getElementById('themeToggleBtn');
    if (btn) {
      btn.textContent = current === 'dark' ? '☀️' : '🌙';
      btn.setAttribute('aria-label', current === 'dark' ? 'Switch to light theme' : 'Switch to dark theme');
    }
    try {
      localStorage.setItem('abhyaas-theme', current);
    } catch (e) {
      // ignore storage failures
    }
  }

  function initTheme() {
    var stored = null;
    try {
      stored = localStorage.getItem('abhyaas-theme');
    } catch (e) {
      stored = null;
    }
    var initial = stored || (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    setTheme(initial);
  }

  initTheme();

  var themeToggleBtn = document.getElementById('themeToggleBtn');
  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', function () {
      var active = document.documentElement.classList.contains('theme-dark');
      setTheme(active ? 'light' : 'dark');
    });
  }

  attachFormValidation('#login-form');
  attachFormValidation('#register-form');
  attachFormValidation('#forgot-form');
  attachPasswordFormValidation();

  // Username availability check (registration & profile)
  function attachUsernameChecks() {
    var regUsername = document.getElementById('reg-username');
    var regNote = document.getElementById('username-availability');
    var profileUsername = document.getElementById('profile-username');
    var profileNote = document.getElementById('profile-username-availability');

    var pairs = [];
    if (regUsername && regNote) pairs.push({input: regUsername, note: regNote});
    if (profileUsername && profileNote) pairs.push({input: profileUsername, note: profileNote});
    if (!pairs.length) return;

    var timeout;
    pairs.forEach(function (pair) {
      pair.input.addEventListener('input', function () {
        pair.note.textContent = '';
        clearTimeout(timeout);
        timeout = setTimeout(function () {
          var val = pair.input.value || '';
          if (val.length < 3) return;
          var url = '/check-username?username=' + encodeURIComponent(val);
          fetch(url).then(function (res) {
            if (!res.ok) throw new Error('no-route');
            return res.json();
          }).then(function (data) {
            if (data && data.available) {
              pair.note.textContent = 'Username available';
              pair.note.style.color = 'var(--success-color)';
            } else {
              pair.note.textContent = 'Username not available';
              pair.note.style.color = 'var(--error-color)';
            }
          }).catch(function () {
            // silent fallback
          });
        }, 500);
      });
    });
  }

  // Inline profile username editor: toggle edit, cancel, and pre-submit availability check
  function attachProfileUsernameEditor() {
    var editBtn = document.getElementById('edit-username');
    var saveBtn = document.getElementById('save-username');
    var cancelBtn = document.getElementById('cancel-username');
    var input = document.getElementById('profile-username');
    var note = document.getElementById('profile-username-availability');
    var display = document.getElementById('display-username');
    if (!input || !editBtn || !saveBtn || !cancelBtn) return;

    var original = input.value || '';

    function enableEditMode() {
      input.style.cursor = 'text';
      setTimeout(function () {
        input.focus();
        try {
          input.select();
          if (input.setSelectionRange) input.setSelectionRange(0, input.value.length);
        } catch (e) {}
      }, 0);
      editBtn.style.display = 'none';
      saveBtn.style.display = '';
      cancelBtn.style.display = '';
    }

    editBtn.addEventListener('click', enableEditMode);
    input.addEventListener('click', function () {
      if (saveBtn.style.display === 'none') {
        enableEditMode();
      }
    });
    input.addEventListener('focus', function () {
      if (saveBtn.style.display === 'none') {
        enableEditMode();
      }
    });

    cancelBtn.addEventListener('click', function () {
      input.value = original;
      note.textContent = '';
      editBtn.style.display = '';
      saveBtn.style.display = 'none';
      cancelBtn.style.display = 'none';
    });

    var form = document.getElementById('username-form');
    if (!form) return;
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var val = input.value || '';
      var pat = input.getAttribute('pattern');
      if (pat) {
        var re = new RegExp(pat);
        if (!re.test(val)) {
          note.textContent = 'Invalid username format';
          note.style.color = 'var(--error-color)';
          return;
        }
      }

      fetch('/check-username?username=' + encodeURIComponent(val)).then(function (res) {
        if (!res.ok) throw new Error('no-route');
        return res.json();
      }).then(function (data) {
        if (data && data.available) {
          input.readOnly = true;
          original = val;
          if (display) display.textContent = val || 'User';
          form.submit();
        } else {
          note.textContent = 'Username not available';
          note.style.color = 'var(--error-color)';
        }
      }).catch(function () {
        form.submit();
      });
    });
  }

  attachUsernameChecks();
  attachProfileUsernameEditor();

  // Notification bell dropdown toggle
  var notifBtn = document.getElementById('notifBtn');
  var notifDropdown = document.getElementById('notifDropdown');
  if (notifBtn && notifDropdown) {
    notifBtn.addEventListener('click', function (event) {
      event.stopPropagation();
      notifDropdown.classList.toggle('open');
    });

    document.addEventListener('click', function (event) {
      if (!notifDropdown.contains(event.target) && event.target !== notifBtn) {
        notifDropdown.classList.remove('open');
      }
    });
  }

  // Topbar overflow menu (mobile)
  var overflowBtn = document.getElementById('topbarOverflowBtn');
  var overflowMenu = document.getElementById('topbarOverflowMenu');
  var overflowTheme = document.getElementById('overflowThemeToggle');
  var overflowNotif = document.getElementById('overflowNotifBtn');
  function closeOverflow() {
    if (overflowMenu) { overflowMenu.classList.remove('open'); overflowMenu.setAttribute('aria-hidden','true'); }
  }
  function openOverflow() {
    if (overflowMenu) { overflowMenu.classList.add('open'); overflowMenu.setAttribute('aria-hidden','false'); }
  }
  if (overflowBtn && overflowMenu) {
    overflowBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      if (overflowMenu.classList.contains('open')) closeOverflow(); else openOverflow();
    });
  }
  // Wire overflow theme toggle to existing theme button behavior
  if (overflowTheme) {
    overflowTheme.addEventListener('click', function () {
      var btn = document.getElementById('themeToggleBtn');
      if (btn) btn.click();
      closeOverflow();
    });
  }
  if (overflowNotif) {
    overflowNotif.addEventListener('click', function () {
      var btn = document.getElementById('notifBtn');
      if (btn) btn.click();
      closeOverflow();
    });
  }
  document.addEventListener('click', function (e) {
    if (overflowMenu && !overflowMenu.contains(e.target) && e.target !== overflowBtn) closeOverflow();
  });

  // Leave reason modal: open full reason text in modal when teacher clicks 'View'
  var reasonModalOverlay = null;
  function ensureReasonModal() {
    if (reasonModalOverlay) return reasonModalOverlay;
    reasonModalOverlay = document.createElement('div');
    reasonModalOverlay.className = 'reason-modal-overlay';
    reasonModalOverlay.innerHTML = '\n      <div class="reason-modal" role="dialog" aria-modal="true">\n        <div class="reason-modal-header">\n          <div>\n            <div class="reason-modal-title">Leave reason</div>\n            <div class="reason-modal-meta" style="font-size:0.9rem;color:var(--text-muted)"></div>\n          </div>\n          <button class="reason-modal-close" aria-label="Close">×</button>\n        </div>\n        <div class="reason-modal-body" id="reasonModalBody"></div>\n      </div>\n    ';
    document.body.appendChild(reasonModalOverlay);
    reasonModalOverlay.querySelector('.reason-modal-close').addEventListener('click', function () { reasonModalOverlay.classList.remove('open'); });
    reasonModalOverlay.addEventListener('click', function (ev) { if (ev.target === reasonModalOverlay) reasonModalOverlay.classList.remove('open'); });
    document.addEventListener('keydown', function (ev) { if (ev.key === 'Escape' && reasonModalOverlay.classList.contains('open')) reasonModalOverlay.classList.remove('open'); });
    return reasonModalOverlay;
  }

  document.addEventListener('click', function (ev) {
    var btn = ev.target.closest && ev.target.closest('.view-reason');
    if (!btn) return;
    ev.preventDefault();
    var text = btn.getAttribute('data-reason') || '';
    var requestId = btn.getAttribute('data-request-id') || '';
    var student = btn.getAttribute('data-student') || '';
    var submitted = btn.getAttribute('data-submitted') || '';
    var status = btn.getAttribute('data-status') || '';
    var dateRange = btn.getAttribute('data-date') || '';
    var leaveType = btn.getAttribute('data-type') || '';
    var modal = ensureReasonModal();
    var body = modal.querySelector('#reasonModalBody');
    if (body) body.textContent = text;
    // populate header details
    var titleEl = modal.querySelector('.reason-modal-title');
    if (titleEl) titleEl.textContent = student ? (student + " — " + status) : 'Leave reason';
    var metaEl = modal.querySelector('.reason-modal-meta');
    if (metaEl) metaEl.textContent = submitted ? ('Submitted: ' + submitted) : '';
    // append date and type information to meta
    if (dateRange) {
      metaEl.textContent += (metaEl.textContent ? ' • ' : '') + 'Dates: ' + dateRange;
    }
    if (leaveType) {
      metaEl.textContent += (metaEl.textContent ? ' • ' : '') + 'Type: ' + leaveType;
    }
    modal.classList.add('open');

    // If the request is pending, show a small inline popover next to the clicked button
    if (String(status).toLowerCase() === 'pending') {
      showActionPopover(btn, requestId);
    }
  });

  // Mobile sidebar toggle
  var navToggle = document.getElementById('navToggleBtn');
  var appShell = document.querySelector('.app-shell');
  var mobileOverlay = document.getElementById('mobileNavOverlay');
  function closeSidebar() {
    if (appShell) appShell.classList.remove('sidebar-open');
    if (mobileOverlay) mobileOverlay.classList.remove('open');
  }
  function openSidebar() {
    if (appShell) appShell.classList.add('sidebar-open');
    if (mobileOverlay) mobileOverlay.classList.add('open');
  }
  if (navToggle && appShell) {
    navToggle.addEventListener('click', function (e) {
      e.stopPropagation();
      if (appShell.classList.contains('sidebar-open')) closeSidebar(); else openSidebar();
    });
  }
  if (mobileOverlay) {
    mobileOverlay.addEventListener('click', function () { closeSidebar(); });
  }
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeSidebar();
  });
  window.addEventListener('resize', function () {
    if (window.innerWidth > 768) closeSidebar();
  });

  // Inline action popover for Approve/Reject
  var actionPopover = null;
  function removeActionPopover() {
    if (!actionPopover) return;
    actionPopover.remove();
    actionPopover = null;
    document.removeEventListener('click', onDocClickForPopover);
  }

  function onDocClickForPopover(e) {
    if (!actionPopover) return;
    if (e.target.closest && e.target.closest('.leave-action-popover')) return;
    if (e.target.closest && e.target.closest('.view-reason')) return;
    removeActionPopover();
  }

  function showActionPopover(anchorBtn, requestId) {
    removeActionPopover();
    actionPopover = document.createElement('div');
    actionPopover.className = 'leave-action-popover';
    // forms post to the same endpoint as teacher view
    var path = window.location.pathname;
    actionPopover.innerHTML = '\n      <form method="POST" action="' + path + '" class="popover-form">\n        <input type="hidden" name="request_id" value="' + (requestId || '') + '">\n        <input type="hidden" name="action" value="approve">\n        <button type="submit" class="btn-primary">Approve</button>\n      </form>\n      <form method="POST" action="' + path + '" class="popover-form">\n        <input type="hidden" name="request_id" value="' + (requestId || '') + '">\n        <input type="hidden" name="action" value="reject">\n        <button type="submit" class="btn-secondary">Reject</button>\n      </form>\n    ';
    document.body.appendChild(actionPopover);

    // position popover near anchor button
    var rect = anchorBtn.getBoundingClientRect();
    var left = rect.right + 8 + window.scrollX;
    var top = rect.top + window.scrollY;
    // if popover would overflow right edge, position to left
    var popRectApproxWidth = 220;
    if (left + popRectApproxWidth > window.scrollX + window.innerWidth) {
      left = rect.left - popRectApproxWidth - 8 + window.scrollX;
    }
    actionPopover.style.position = 'absolute';
    actionPopover.style.left = left + 'px';
    actionPopover.style.top = top + 'px';
    actionPopover.style.zIndex = 2400;

    // close popover when clicking outside
    setTimeout(function () { document.addEventListener('click', onDocClickForPopover); }, 0);
  }

  // Message contacts toggle (mobile): show/hide the message sidebar
  var contactsToggle = document.getElementById('contactsToggleBtn');
  function closeMessageSidebar() {
    if (appShell) appShell.classList.remove('message-sidebar-open');
    if (mobileOverlay) mobileOverlay.classList.remove('open');
  }
  function openMessageSidebar() {
    if (appShell) appShell.classList.add('message-sidebar-open');
    if (mobileOverlay) mobileOverlay.classList.add('open');
  }
  if (contactsToggle) {
    contactsToggle.addEventListener('click', function (e) {
      e.stopPropagation();
      if (appShell.classList.contains('message-sidebar-open')) closeMessageSidebar(); else openMessageSidebar();
    });
  }
  // Ensure overlay closes message sidebar too
  if (mobileOverlay) {
    mobileOverlay.addEventListener('click', function () { closeSidebar(); closeMessageSidebar(); });
  }

});
