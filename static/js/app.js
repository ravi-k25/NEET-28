document.addEventListener('DOMContentLoaded', () => {
  const currentPage = document.body.dataset.page;
  const navItems = document.querySelectorAll('.nav-item');

  navItems.forEach((item) => {
    const href = item.getAttribute('href');
    const isActive =
      (currentPage === 'dashboard' && href === '/') ||
      (currentPage === 'tasks' && href === '/tasks') ||
      (currentPage === 'timer' && href === '/timer') ||
      (currentPage === 'analytics' && href === '/analytics') ||
      (currentPage === 'tests' && href === '/tests') ||
      (currentPage === 'syllabus' && href === '/syllabus') ||
      (currentPage === 'revisions' && href === '/revisions') ||
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

  const timerPage = document.querySelector('.timer-page');
  if (timerPage) {
    const STORAGE_KEY = 'neet-study-companion-timer';
    const BREAK_MESSAGES = [
      'Drink some water, dear 🥤❤️',
      'Stretch your shoulders a little 🌸',
      'Look away from the screen for 20 seconds 👀',
      'Take a small walk 🚶‍♀️',
      'Take a deep breath. You\'ve got this 🫶',
      'Rest properly. Recovery is part of studying too ❤️'
    ];

    const presetMap = {
      pomodoro: { label: 'POMODORO', studyMinutes: 25, breakMinutes: 5, sessionType: 'pomodoro' },
      standard: { label: 'STANDARD', studyMinutes: 50, breakMinutes: 10, sessionType: 'standard' },
      deep_work: { label: 'DEEP WORK', studyMinutes: 90, breakMinutes: 15, sessionType: 'deep_work' },
      custom: { label: 'CUSTOM', studyMinutes: 25, breakMinutes: 5, sessionType: 'custom' }
    };

    const timerDisplay = document.getElementById('timerDisplay');
    const timerBadge = document.getElementById('timerBadge');
    const modeLabel = document.getElementById('modeLabel');
    const timerPhaseLabel = document.getElementById('timerPhaseLabel');
    const statusBox = document.getElementById('statusBox');
    const modeButtons = document.querySelectorAll('[data-mode]');
    const customSettings = document.getElementById('customSettings');
    const customStudyMinutes = document.getElementById('customStudyMinutes');
    const customBreakMinutes = document.getElementById('customBreakMinutes');
    const subjectSelect = document.getElementById('subjectSelect');
    const chapterInput = document.getElementById('chapterInput');
    const quickPomodoroBtn = document.getElementById('quickPomodoroBtn');
    const startBtn = document.getElementById('startBtn');
    const pauseBtn = document.getElementById('pauseBtn');
    const resumeBtn = document.getElementById('resumeBtn');
    const resetBtn = document.getElementById('resetBtn');
    const skipBtn = document.getElementById('skipBtn');

    let timerInterval = null;

    function loadState() {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) {
        return {
          mode: 'pomodoro',
          phase: 'focus',
          studyMinutes: 25,
          breakMinutes: 5,
          totalDurationMs: 25 * 60 * 1000,
          remainingMs: 25 * 60 * 1000,
          isRunning: false,
          startedAt: null,
          sessionType: 'pomodoro',
          subject: 'Physics',
          chapter: '',
          lastTick: null
        };
      }

      try {
        return JSON.parse(raw);
      } catch (error) {
        return {
          mode: 'pomodoro',
          phase: 'focus',
          studyMinutes: 25,
          breakMinutes: 5,
          totalDurationMs: 25 * 60 * 1000,
          remainingMs: 25 * 60 * 1000,
          isRunning: false,
          startedAt: null,
          sessionType: 'pomodoro',
          subject: 'Physics',
          chapter: '',
          lastTick: null
        };
      }
    }

    let state = loadState();

    function saveState(nextState = state) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(nextState));
      state = nextState;
    }

    function formatTime(ms) {
      const totalSeconds = Math.max(0, Math.ceil(ms / 1000));
      const minutes = Math.floor(totalSeconds / 60);
      const seconds = totalSeconds % 60;
      return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    }

    function updateModeButtons() {
      modeButtons.forEach((button) => {
        const isSelected = button.dataset.mode === state.mode;
        button.classList.toggle('selected', isSelected);
      });
      const customSelected = state.mode === 'custom';
      customSettings.classList.toggle('hidden', !customSelected);
    }

    function applyPresetSelection(modeKey) {
      const preset = presetMap[modeKey] || presetMap.pomodoro;
      state.mode = modeKey;
      state.phase = 'focus';
      state.sessionType = preset.sessionType;
      state.studyMinutes = modeKey === 'custom' ? Number(customStudyMinutes.value || 25) : preset.studyMinutes;
      state.breakMinutes = modeKey === 'custom' ? Number(customBreakMinutes.value || 5) : preset.breakMinutes;
      state.totalDurationMs = state.studyMinutes * 60 * 1000;
      state.remainingMs = state.totalDurationMs;
      state.isRunning = false;
      state.startedAt = null;
      updateUI();
      saveState(state);
      statusBox.textContent = 'Focus session ready. Start when you are set. 💫';
    }

    function updateUI() {
      const currentPreset = presetMap[state.mode] || presetMap.pomodoro;
      const displayMinutes = state.phase === 'focus' ? state.studyMinutes : state.breakMinutes;
      const totalDuration = state.phase === 'focus' ? state.studyMinutes * 60 * 1000 : state.breakMinutes * 60 * 1000;
      const currentRemainingMs = state.isRunning && state.startedAt
        ? Math.max(totalDuration - (Date.now() - state.startedAt), 0)
        : state.remainingMs;

      const label = state.phase === 'focus' ? 'FOCUS MODE' : 'BREAK MODE';
      state.totalDurationMs = totalDuration;
      state.remainingMs = currentRemainingMs;

      timerDisplay.textContent = formatTime(currentRemainingMs);
      timerBadge.textContent = formatTime(currentRemainingMs);
      modeLabel.textContent = state.phase === 'focus' ? (state.mode === 'custom' ? 'CUSTOM' : currentPreset.label) : 'BREAK';
      timerPhaseLabel.textContent = label;
      updateModeButtons();
    }

    function startTimer() {
      if (state.isRunning) return;

      if (state.remainingMs <= 0) {
        state.remainingMs = (state.phase === 'focus' ? state.studyMinutes : state.breakMinutes) * 60 * 1000;
      }

      state.startedAt = Date.now();
      state.isRunning = true;
      state.lastTick = Date.now();
      saveState(state);
      statusBox.textContent = state.phase === 'focus' ? 'Focus mode active. Let’s go, future doctor. ✨' : 'Break mode active. Breathe and reset. 🌿';
      tickTimer();
    }

    function tickTimer() {
      if (timerInterval) clearInterval(timerInterval);

      timerInterval = setInterval(() => {
        if (!state.isRunning || !state.startedAt) return;

        const totalDuration = state.phase === 'focus' ? state.studyMinutes * 60 * 1000 : state.breakMinutes * 60 * 1000;
        const elapsed = Date.now() - state.startedAt;
        const remaining = Math.max(totalDuration - elapsed, 0);

        state.remainingMs = remaining;
        updateUI();

        if (remaining <= 0) {
          clearInterval(timerInterval);
          completeCycle();
        }
      }, 250);
    }

    function pauseTimer() {
      if (!state.isRunning || !state.startedAt) return;

      const totalDuration = state.phase === 'focus' ? state.studyMinutes * 60 * 1000 : state.breakMinutes * 60 * 1000;
      const elapsed = Date.now() - state.startedAt;
      state.remainingMs = Math.max(totalDuration - elapsed, 0);
      state.isRunning = false;
      state.startedAt = null;
      saveState(state);
      updateUI();
      statusBox.textContent = 'Paused. Breathe. Resume when you are ready. 💪';
    }

    function resumeTimer() {
      if (state.isRunning) return;
      if (state.remainingMs <= 0) {
        state.remainingMs = (state.phase === 'focus' ? state.studyMinutes : state.breakMinutes) * 60 * 1000;
      }
      state.startedAt = Date.now();
      state.isRunning = true;
      saveState(state);
      statusBox.textContent = state.phase === 'focus' ? 'Back in focus. Keep the momentum. ✨' : 'Break time is on. Take care of yourself. 🌸';
      tickTimer();
    }

    function resetTimer() {
      if (timerInterval) clearInterval(timerInterval);
      state.isRunning = false;
      state.startedAt = null;
      state.phase = 'focus';
      if (state.mode === 'custom') {
        state.studyMinutes = Number(customStudyMinutes.value || 25);
        state.breakMinutes = Number(customBreakMinutes.value || 5);
      }
      state.remainingMs = state.studyMinutes * 60 * 1000;
      saveState(state);
      updateUI();
      statusBox.textContent = 'Timer reset. Ready for a fresh round. 🌟';
    }

    function skipTimer() {
      if (timerInterval) clearInterval(timerInterval);
      completeCycle(true);
    }

    function completeCycle(skipped = false) {
      const wasFocus = state.phase === 'focus';
      state.isRunning = false;
      state.startedAt = null;

      if (wasFocus) {
        const sessionMinutes = state.studyMinutes;
        const finishedAt = new Date().toISOString();
        const startedAt = new Date(Date.now() - sessionMinutes * 60 * 1000).toISOString();
        fetch('/timer/session', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            subject: subjectSelect.value,
            chapter: chapterInput.value,
            duration_minutes: sessionMinutes,
            session_type: state.sessionType,
            started_at: startedAt,
            completed_at: finishedAt
          })
        }).catch(() => {
          statusBox.textContent = 'Focus session complete. The session was saved locally in the browser for later sync. 💪';
        });

        statusBox.textContent = 'Focus session complete! 🎯❤️';
        state.phase = 'break';
        state.remainingMs = state.breakMinutes * 60 * 1000;
        const breakMessage = BREAK_MESSAGES[Math.floor(Math.random() * BREAK_MESSAGES.length)];
        state.statusMessage = breakMessage;
        if (!skipped) {
          statusBox.textContent = `${breakMessage}`;
        }
      } else {
        state.phase = 'focus';
        state.remainingMs = state.studyMinutes * 60 * 1000;
        statusBox.textContent = 'Break\'s over, doctor-to-be 😤❤️ Ready for another round?';
      }

      saveState(state);
      updateUI();
    }

    modeButtons.forEach((button) => {
      button.addEventListener('click', () => {
        const modeKey = button.dataset.mode;
        if (modeKey === 'custom') {
          state.mode = 'custom';
          state.phase = 'focus';
          state.studyMinutes = Number(customStudyMinutes.value || 25);
          state.breakMinutes = Number(customBreakMinutes.value || 5);
          state.remainingMs = state.studyMinutes * 60 * 1000;
          state.isRunning = false;
          state.startedAt = null;
          saveState(state);
          updateUI();
          statusBox.textContent = 'Custom focus mode selected. Set your perfect rhythm. 🌱';
          customSettings.classList.remove('hidden');
          return;
        }
        applyPresetSelection(modeKey);
      });
    });

    customStudyMinutes.addEventListener('input', () => {
      if (state.mode === 'custom') {
        state.studyMinutes = Number(customStudyMinutes.value || 25);
        state.remainingMs = state.studyMinutes * 60 * 1000;
        saveState(state);
        updateUI();
      }
    });

    customBreakMinutes.addEventListener('input', () => {
      if (state.mode === 'custom') {
        state.breakMinutes = Number(customBreakMinutes.value || 5);
        saveState(state);
      }
    });

    startBtn.addEventListener('click', startTimer);
    pauseBtn.addEventListener('click', pauseTimer);
    resumeBtn.addEventListener('click', resumeTimer);
    resetBtn.addEventListener('click', resetTimer);
    skipBtn.addEventListener('click', skipTimer);
    quickPomodoroBtn.addEventListener('click', () => {
      applyPresetSelection('pomodoro');
      startTimer();
    });

    if (state.mode === 'custom') {
      customSettings.classList.remove('hidden');
    }

    updateUI();
  }
});
