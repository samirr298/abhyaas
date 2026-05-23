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

  attachFormValidation('#login-form');
  attachFormValidation('#register-form');
  attachFormValidation('#forgot-form');
  attachPasswordFormValidation();

});
