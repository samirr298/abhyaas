// document.addEventListener('DOMContentLoaded', initTaskScripts);

// function initTaskScripts() {
//   setupFilterChips();
//   setupSubmissionToggles();
//   setupSubmissionFormHandlers();
//   setupSubmissionSearch();
// }

// function setupFilterChips() {
//   const filterButtons = Array.from(document.querySelectorAll('.filter-chip'));
//   const taskItems = Array.from(document.querySelectorAll('.task-item'));

//   if (!filterButtons.length || !taskItems.length) return;

//   function applyFilter(filterValue) {
//     taskItems.forEach((item) => {
//       const status = (item.dataset.status || '').toString();
//       const shouldShow = filterValue === 'all' || status === filterValue;
//       item.style.display = shouldShow ? 'block' : 'none';
//     });
//   }

//   filterButtons.forEach((button) => {
//     button.addEventListener('click', () => {
//       // update active state on chips
//       filterButtons.forEach((b) => b.classList.remove('active'));
//       button.classList.add('active');

//       const selectedFilter = button.dataset.filter || 'all';
//       applyFilter(selectedFilter);
//     });
//   });
// }

// function setupSubmissionToggles() {
//   const actionButtons = Array.from(document.querySelectorAll('.task-action-btn'));
//   if (!actionButtons.length) return;

//   actionButtons.forEach((btn) => {
//     btn.addEventListener('click', () => {
//       const taskCard = btn.closest('.task-item');
//       if (!taskCard) return;

//       const panel = taskCard.querySelector('.submission-panel');
//       if (!panel) return;

//       const panelIsCurrentlyHidden = !!panel.hidden;

//       // Close all other open panels first
//       document.querySelectorAll('.submission-panel').forEach((other) => {
//         if (other !== panel) other.hidden = true;
//       });

//       // Toggle the target panel and update the button label
//       panel.hidden = !panelIsCurrentlyHidden;
//       btn.textContent = panel.hidden ? 'Submit task' : 'Hide submission';
//     });
//   });
// }

// function setupSubmissionFormHandlers() {
//   const submissionForms = Array.from(document.querySelectorAll('.submission-panel'));
//   if (!submissionForms.length) return;

//   submissionForms.forEach((form) => {
//     form.addEventListener('submit', (e) => {
//       // If the user provided a link, append it to the textarea so server receives it as part of the message
//       const urlInput = form.querySelector('input[type="url"]');
//       const messageBox = form.querySelector('textarea');

//       if (!messageBox) return;
//       if (!urlInput) return; // nothing to do if no url input present

//       const link = (urlInput.value || '').trim();
//       if (!link) return; // allow normal submit when link empty

//       const existing = (messageBox.value || '').trim();
//       const linkLine = `Submission link: ${link}`;
//       messageBox.value = existing ? `${existing}\n${linkLine}` : linkLine;
//       urlInput.value = '';

//       // Let the form submit normally; server-side handles publishing
//     });
//   });
// }

// function setupSubmissionSearch() {
//   const searchInput = document.getElementById('submission-search');
//   if (!searchInput) return;

//   searchInput.addEventListener('input', (event) => {
//     const raw = (event.target.value || '').toLowerCase().trim();
//     const rows = Array.from(document.querySelectorAll('.submission-row'));

//     if (!raw) {
//       // show all rows when search is cleared
//       rows.forEach((r) => (r.style.display = ''));
//       return;
//     }

//     rows.forEach((row) => {
//       const name = (row.dataset.name || '').toLowerCase();
//       row.style.display = name.includes(raw) ? '' : 'none';
//     });
//   });
// }
