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

});
