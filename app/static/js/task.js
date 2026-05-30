document.addEventListener('DOMContentLoaded', function () {
  const filterButtons = document.querySelectorAll('.filter-chip');
  const taskItems = document.querySelectorAll('.task-item');

  filterButtons.forEach((button) => {
    button.addEventListener('click', () => {
      filterButtons.forEach((btn) => btn.classList.remove('active'));
      button.classList.add('active');

      const filter = button.dataset.filter;

      taskItems.forEach((item) => {
        const status = item.dataset.status;
        const matches = filter === 'all' || status === filter;
        item.style.display = matches ? 'block' : 'none';
      });
    });
  });

  const markButtons = document.querySelectorAll('.task-action-btn');
  markButtons.forEach((button) => {
    button.addEventListener('click', () => {
      const card = button.closest('.task-item');
      const panel = card.querySelector('.submission-panel');
      const isHidden = panel.hidden;

      document.querySelectorAll('.submission-panel').forEach((openPanel) => {
        if (openPanel !== panel) {
          openPanel.hidden = true;
        }
      });

      panel.hidden = !isHidden;
      button.textContent = panel.hidden ? 'Submit task' : 'Hide submission';
    });
  });

  document.querySelectorAll('.submission-panel').forEach((form) => {
    form.addEventListener('submit', (event) => {
      const linkInput = form.querySelector('input[type="url"]');
      const textarea = form.querySelector('textarea');

      if (linkInput && textarea && linkInput.value.trim()) {
        const currentText = textarea.value.trim();
        const linkText = `Submission link: ${linkInput.value.trim()}`;
        textarea.value = currentText ? `${currentText}\n${linkText}` : linkText;
        linkInput.value = '';
      }
    });
  });

  // Real task publishing and feedback are handled by the server.

  const searchInput = document.getElementById('submission-search');
  if (searchInput) {
    searchInput.addEventListener('input', (event) => {
      const query = event.target.value.toLowerCase().trim();
      document.querySelectorAll('.submission-row').forEach((row) => {
        const name = row.dataset.name || '';
        row.style.display = name.includes(query) ? '' : 'none';
      });
    });
  }
});
