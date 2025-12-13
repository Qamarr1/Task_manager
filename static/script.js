// User Dropdown Functions
function toggleUserDropdown(event) {
    event.stopPropagation();
    const dropdown = document.getElementById('userDropdown');
    if (dropdown) {
        dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
    }
}

document.addEventListener('click', function(event) {
    const dropdown = document.getElementById('userDropdown');
    const userButton = document.getElementById('userDropdownBtn');
    if (!dropdown || !userButton) return;
    if (!userButton.contains(event.target) && !dropdown.contains(event.target)) {
        dropdown.style.display = 'none';
    }
});

const userBtn = document.getElementById('userDropdownBtn');
if (userBtn) {
    userBtn.addEventListener('click', toggleUserDropdown);
}

// Change Username Modal
function openChangeUsernameModal() {
    document.getElementById('changeUsernameModal').style.display = 'flex';
    const dropdown = document.getElementById('userDropdown');
    if (dropdown) dropdown.style.display = 'none';
}

function closeChangeUsernameModal() {
    document.getElementById('changeUsernameModal').style.display = 'none';
    document.getElementById('changeUsernameForm').reset();
}

async function changeUsername(event) {
    event.preventDefault();
    const newUsername = document.getElementById('newUsername').value;
    const currentPassword = document.getElementById('currentPasswordUsername').value;

    try {
        const response = await fetch('/change-username', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                new_username: newUsername,
                current_password: currentPassword
            })
        });

        const data = await response.json();
        if (response.ok) {
            alert('Username changed successfully!');
            closeChangeUsernameModal();
            location.reload();
        } else {
            alert(data.error || 'Failed to change username');
        }
    } catch (error) {
        alert('An error occurred. Please try again.');
        console.error('Error:', error);
    }
}

// Change Password Modal
function openChangePasswordModal() {
    document.getElementById('changePasswordModal').style.display = 'flex';
    const dropdown = document.getElementById('userDropdown');
    if (dropdown) dropdown.style.display = 'none';
}

function closeChangePasswordModal() {
    document.getElementById('changePasswordModal').style.display = 'none';
    document.getElementById('changePasswordForm').reset();
}

async function changePassword(event) {
    event.preventDefault();
    const currentPassword = document.getElementById('currentPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    if (newPassword !== confirmPassword) {
        alert('New passwords do not match!');
        return;
    }

    try {
        const response = await fetch('/change-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword
            })
        });

        const data = await response.json();
        if (response.ok) {
            alert('Password changed successfully!');
            closeChangePasswordModal();
        } else {
            alert(data.error || 'Failed to change password');
        }
    } catch (error) {
        alert('An error occurred. Please try again.');
        console.error('Error:', error);
    }
}

// Settings Modal
function openSettingsModal() {
    const modal = document.getElementById('settingsModal');
    modal.style.display = 'flex';
    const dropdown = document.getElementById('userDropdown');
    if (dropdown) dropdown.style.display = 'none';
    loadSettings();
}

function closeSettingsModal() {
    document.getElementById('settingsModal').style.display = 'none';
}

function loadSettings() {
    const theme = localStorage.getItem('theme') || 'light';
    const themeSelect = document.getElementById('themeSelect');
    if (themeSelect) {
        themeSelect.value = theme;
    }
    const browserNotifs = localStorage.getItem('browserNotifications') === 'true';
    const soundNotifs = localStorage.getItem('soundNotifications') === 'true';
    const browserCheckbox = document.getElementById('browserNotifications');
    const soundCheckbox = document.getElementById('soundNotifications');
    if (browserCheckbox) browserCheckbox.checked = browserNotifs;
    if (soundCheckbox) soundCheckbox.checked = soundNotifs;
}

function applyTheme(theme) {
    localStorage.setItem('theme', theme);
    document.body.setAttribute('data-theme', theme);
}

async function toggleBrowserNotifications(enabled) {
    if (enabled) {
        if ('Notification' in window) {
            const permission = await Notification.requestPermission();
            if (permission === 'granted') {
                localStorage.setItem('browserNotifications', 'true');
            } else {
                document.getElementById('browserNotifications').checked = false;
                alert('Please enable notifications in your browser settings');
            }
        } else {
            alert('Your browser does not support notifications');
            document.getElementById('browserNotifications').checked = false;
        }
    } else {
        localStorage.setItem('browserNotifications', 'false');
    }
}

function toggleSoundNotifications(enabled) {
    // Sound notifications removed per user request; keep checkbox but no-op for storage
    localStorage.setItem('soundNotifications', 'false');
    const box = document.getElementById('soundNotifications');
    if (box) box.checked = false;
}

// Task Filtering
function filterTasks() {
    const searchTerm = (document.getElementById('searchInput')?.value || '').toLowerCase();
    const categoryFilter = document.getElementById('categoryFilter')?.value || 'All';
    const priorityFilter = document.getElementById('priorityFilter')?.value || 'All';

    const taskCards = document.querySelectorAll('.task-card');
    taskCards.forEach(card => {
        const title = card.querySelector('.task-card__title')?.textContent.toLowerCase() || '';
        const description = card.querySelector('.task-card__desc')?.textContent.toLowerCase() || '';
        const category = card.getAttribute('data-category') || '';
        const priority = card.getAttribute('data-priority') || '';

        const matchesSearch = !searchTerm || title.includes(searchTerm) || description.includes(searchTerm);
        const matchesCategory = categoryFilter === 'All' || category === categoryFilter;
        const matchesPriority = priorityFilter === 'All' || priority === priorityFilter;

        card.style.display = (matchesSearch && matchesCategory && matchesPriority) ? '' : 'none';
    });

    updateColumnCounts();
}

function resetFilters() {
    const searchInput = document.getElementById('searchInput');
    const categorySelect = document.getElementById('categoryFilter');
    const prioritySelect = document.getElementById('priorityFilter');
    if (searchInput) searchInput.value = '';
    if (categorySelect) categorySelect.value = 'All';
    if (prioritySelect) prioritySelect.value = 'All';
    filterTasks();
}

function updateColumnCounts() {
    ['todo', 'in_progress', 'in_review', 'done'].forEach(status => {
        const column = document.getElementById(`column-${status}`);
        const countElement = document.getElementById(`count-${status}`);
        if (!column || !countElement) return;
        const visibleTasks = Array.from(column.querySelectorAll('.task-card')).filter(card => {
            return window.getComputedStyle(card).display !== 'none';
        }).length;
        countElement.textContent = visibleTasks;
    });
}

// Task Modal helpers
function closeTaskModal() {
    const modal = document.getElementById('taskModal');
    if (modal) {
        modal.classList.remove('show');
    }
}

function openAddModal() {
    const modal = document.getElementById('taskModal');
    const form = document.getElementById('taskForm');
    const titleEl = document.getElementById('taskModalTitle');
    if (!modal || !form) return;
    form.reset();
    form.action = modal.dataset.addUrl;
    const priorityField = form.querySelector('select[name="priority"]');
    const statusField = form.querySelector('select[name="status"]');
    if (priorityField) priorityField.value = 'Medium';
    if (statusField) statusField.value = 'todo';
    if (titleEl) titleEl.textContent = 'Add task';
    modal.classList.add('show');
}

function openEditModal(buttonEl) {
    const modal = document.getElementById('taskModal');
    const form = document.getElementById('taskForm');
    const titleEl = document.getElementById('taskModalTitle');
    if (!modal || !form || !buttonEl?.dataset) return;

    const editTemplate = modal.dataset.editUrlTemplate || '';
    form.action = editTemplate.replace('0', buttonEl.dataset.id);

    form.querySelector('input[name="title"]').value = buttonEl.dataset.title || '';
    form.querySelector('textarea[name="description"]').value = buttonEl.dataset.description || '';
    form.querySelector('select[name="priority"]').value = buttonEl.dataset.priority || 'Medium';
    form.querySelector('select[name="category"]').value = buttonEl.dataset.category || 'Other';
    form.querySelector('select[name="status"]').value = buttonEl.dataset.status || 'todo';
    form.querySelector('input[name="due_date"]').value = buttonEl.dataset.due || '';

    if (titleEl) titleEl.textContent = 'Edit task';
    modal.classList.add('show');
}

// Inline banner helper (uses flash banner styles)
function showInlineBanner(message, type = 'info') {
    let container = document.getElementById('flashBanner');
    if (!container) {
        container = document.createElement('div');
        container.id = 'flashBanner';
        container.className = 'flash-banner-container';
        document.body.appendChild(container);
    }

    const banner = document.createElement('div');
    banner.className = `flash-banner ${type}`;
    banner.textContent = message;
    container.appendChild(banner);

    setTimeout(() => {
        banner.style.opacity = '0';
        setTimeout(() => banner.remove(), 500);
    }, 3000);
}

// Notifications
function checkDueTasksAndNotify() {
    const browserNotifs = localStorage.getItem('browserNotifications') === 'true';
    if (!browserNotifs) return;

    const overdueStat = document.querySelector('.stat-overdue .stat-value');
    const todayStat = document.querySelector('.stat-today .stat-value');
    const overdue = overdueStat ? parseInt(overdueStat.textContent, 10) : 0;
    const dueToday = todayStat ? parseInt(todayStat.textContent, 10) : 0;

    if (overdue === 0 && dueToday === 0) return;

    if (!('Notification' in window)) {
        showInlineBanner('Browser notifications not supported here.', 'error');
        return;
    }

    if (Notification.permission !== 'granted') {
        showInlineBanner('Enable notifications in your browser to get alerts.', 'error');
        return;
    }

    if (overdue > 0) {
        const body = `You have ${overdue} overdue task${overdue > 1 ? 's' : ''}!`;
        new Notification('Taskly - Overdue Tasks', {
            body,
            icon: '/static/favicon.ico',
            tag: 'overdue-tasks'
        });
        showInlineBanner(body, 'error');
    }

    if (dueToday > 0) {
        const body = `You have ${dueToday} task${dueToday > 1 ? 's' : ''} due today!`;
        new Notification('Taskly - Due Today', {
            body,
            icon: '/static/favicon.ico',
            tag: 'due-today-tasks'
        });
        showInlineBanner(body, 'success');
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    const theme = localStorage.getItem('theme') || 'light';
    applyTheme(theme);

    const searchInput = document.getElementById('searchInput');
    const categoryFilter = document.getElementById('categoryFilter');
    const priorityFilter = document.getElementById('priorityFilter');

    if (searchInput) searchInput.addEventListener('input', filterTasks);
    if (categoryFilter) categoryFilter.addEventListener('change', filterTasks);
    if (priorityFilter) priorityFilter.addEventListener('change', filterTasks);

    const taskModal = document.getElementById('taskModal');
    if (taskModal) {
        taskModal.addEventListener('click', (e) => {
            if (e.target === taskModal) closeTaskModal();
        });
    }

    updateColumnCounts();
    checkDueTasksAndNotify();

    const bellBtn = document.getElementById('notificationsBtn');
    const notifDropdown = document.getElementById('notificationsDropdown');
    const notifList = document.getElementById('notifList');

    if (bellBtn && notifDropdown && notifList) {
        bellBtn.addEventListener('click', () => {
            const isOpen = notifDropdown.style.display === 'block';
            notifDropdown.style.display = isOpen ? 'none' : 'block';
            if (isOpen) return;

            notifList.innerHTML = '';
            const overdueStat = document.querySelector('.stat-overdue .stat-value');
            const todayStat = document.querySelector('.stat-today .stat-value');
            const overdue = overdueStat ? parseInt(overdueStat.textContent, 10) : 0;
            const dueToday = todayStat ? parseInt(todayStat.textContent, 10) : 0;

            if (overdue > 0) {
                const item = document.createElement('div');
                item.className = 'notif-item';
                item.innerHTML = `<strong>Overdue</strong><span class="meta">${overdue} task${overdue > 1 ? 's' : ''}</span>`;
                notifList.appendChild(item);
            }

            if (dueToday > 0) {
                const item = document.createElement('div');
                item.className = 'notif-item';
                item.innerHTML = `<strong>Due Today</strong><span class="meta">${dueToday} task${dueToday > 1 ? 's' : ''}</span>`;
                notifList.appendChild(item);
            }

            if (overdue === 0 && dueToday === 0) {
                const empty = document.createElement('div');
                empty.className = 'notif-empty';
                empty.textContent = 'No due items right now.';
                notifList.appendChild(empty);
            }
        });

        document.addEventListener('click', (e) => {
            if (!notifDropdown.contains(e.target) && !bellBtn.contains(e.target)) {
                notifDropdown.style.display = 'none';
            }
        });
    }
});
