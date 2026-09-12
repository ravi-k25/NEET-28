document.addEventListener('DOMContentLoaded', () => {
  const currentPage = document.body.dataset.page;
  const navItems = document.querySelectorAll('.nav-item');

  navItems.forEach((item) => {
    const href = item.getAttribute('href');
    const isActive =
      (currentPage === 'dashboard' && href === '/') ||
      (currentPage === 'tasks' && href === '/tasks') ||
      (currentPage === 'analytics' && href === '/analytics') ||
      (currentPage === 'tests' && href === '/tests') ||
      (currentPage === 'syllabus' && href === '/syllabus') ||
      (currentPage === 'mistakes' && href === '/mistakes');

    if (isActive) {
      item.classList.add('active');
    }
  });

  const modalOpenButtons = document.querySelectorAll('[data-open-modal]');
  const modalCloseButtons = document.querySelectorAll('[data-close-modal]');
  const closeButtons = document.querySelectorAll('[data-close-modal]');

  const openModal = (modalId) => {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    modal.classList.remove('hidden');
    modal.setAttribute('aria-hidden', 'false');
  };

  const closeModal = (modalId) => {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    modal.classList.add('hidden');
    modal.setAttribute('aria-hidden', 'true');
  };

  modalOpenButtons.forEach((button) => {
    button.addEventListener('click', () => openModal(button.dataset.openModal));
  });

  modalCloseButtons.forEach((button) => {
    button.addEventListener('click', () => closeModal(button.dataset.closeModal));
  });

  if (currentPage === 'tasks' && new URLSearchParams(window.location.search).get('open') === 'add') {
    openModal('task-modal');
  }

  const filterFields = document.querySelectorAll('[data-filter-type]');
  const buildQueryString = () => {
    const params = new URLSearchParams(window.location.search);
    const status = document.getElementById('statusFilter')?.value || params.get('status') || 'All';
    const subject = document.getElementById('subjectFilter')?.value || params.get('subject') || 'All';
    const priority = document.getElementById('priorityFilter')?.value || params.get('priority') || 'All';
    const sort = document.getElementById('sortFilter')?.value || params.get('sort') || 'deadline';

    const query = new URLSearchParams();
    query.set('status', status);
    query.set('subject', subject);
    query.set('priority', priority);
    query.set('sort', sort);

    return query.toString();
  };

  filterFields.forEach((field) => {
    field.addEventListener('change', () => {
      const query = buildQueryString();
      window.location.href = `${window.location.pathname}?${query}`;
    });
  });

  const editButtons = document.querySelectorAll('[data-edit-task]');
  const taskModal = document.getElementById('task-modal');
  const form = taskModal ? taskModal.querySelector('.task-form') : null;

  editButtons.forEach((button) => {
    button.addEventListener('click', () => {
      const card = button.closest('.task-card');
      if (!card || !form || !taskModal) return;

      const taskId = card.dataset.id;
      form.action = `/tasks/${taskId}/edit`;
      form.querySelector('input[name="title"]').value = card.dataset.title || '';
      form.querySelector('select[name="subject"]').value = card.dataset.subject || 'Other';
      form.querySelector('input[name="chapter"]').value = card.dataset.chapter || '';
      form.querySelector('select[name="priority"]').value = card.dataset.priority || 'Medium';
      form.querySelector('input[name="estimated_minutes"]').value = card.dataset.estimatedMinutes || card.dataset.estimatedMinutes || '45';
      form.querySelector('input[name="deadline"]').value = card.dataset.deadline || '';
      form.querySelector('select[name="status"]').value = card.dataset.status || 'Pending';

      const modalTitle = taskModal.querySelector('.modal-header h2');
      if (modalTitle) {
        modalTitle.textContent = 'Edit Task';
      }

      openModal('task-modal');
    });
  });

  const modalTitle = taskModal ? taskModal.querySelector('.modal-header h2') : null;
  if (modalTitle && form) {
    const originalSubmit = form.querySelector('button[type="submit"]');
    if (originalSubmit) {
      originalSubmit.textContent = 'Save task';
    }

    const resetForm = () => {
      form.action = '/tasks/add';
      form.reset();
      if (modalTitle) {
        modalTitle.textContent = 'Add Task';
      }
      if (originalSubmit) {
        originalSubmit.textContent = 'Save task';
      }
    };

    closeButtons.forEach((button) => {
      button.addEventListener('click', resetForm);
    });
  }

});
