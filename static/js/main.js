/**
 * STUDENT PERFORMANCE PREDICTION SYSTEM
 * JavaScript Utilities & Chart Configurations
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Sidebar Toggle for Mobile View
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebarOverlay = document.getElementById('sidebarOverlay');

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function () {
            sidebar.classList.toggle('open');
            if (sidebarOverlay) {
                sidebarOverlay.classList.toggle('active');
            }
        });
    }

    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', function () {
            sidebar.classList.remove('open');
            sidebarOverlay.classList.remove('active');
        });
    }

    // 2. Password Toggle for Login Page
    const togglePasswordBtn = document.getElementById('togglePassword');
    const passwordInput = document.getElementById('password');
    if (togglePasswordBtn && passwordInput) {
        togglePasswordBtn.addEventListener('click', function () {
            const isPassword = passwordInput.getAttribute('type') === 'password';
            passwordInput.setAttribute('type', isPassword ? 'text' : 'password');
            this.innerHTML = isPassword 
                ? '<i class="bi bi-eye-slash"></i>' 
                : '<i class="bi bi-eye"></i>';
        });
    }

    // 3. Client-Side Input Real-Time Validation
    const attInput = document.getElementById('attendance');
    const hoursInput = document.getElementById('study_hours');
    const marksInput = document.getElementById('marks');

    function validateRange(input, min, max, name) {
        if (!input) return;
        input.addEventListener('input', function () {
            const val = parseFloat(this.value);
            if (isNaN(val)) return;
            if (val < min) this.value = min;
            if (val > max) this.value = max;
        });
    }

    validateRange(attInput, 0, 100, 'Attendance');
    validateRange(hoursInput, 0, 24, 'Study Hours');
    validateRange(marksInput, 0, 50, 'Marks');

    // 4. Client-Side Table Instant Filter
    const searchInput = document.getElementById('tableSearch');
    if (searchInput) {
        searchInput.addEventListener('keyup', function () {
            const filter = this.value.toLowerCase();
            const table = document.querySelector('.custom-table tbody');
            if (!table) return;
            const rows = table.getElementsByTagName('tr');
            for (let i = 0; i < rows.length; i++) {
                const text = rows[i].textContent.toLowerCase();
                rows[i].style.display = text.includes(filter) ? '' : 'none';
            }
        });
    }

    // 5. Initialize Tooltips
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) bsAlert.close();
        }, 5000);
    });
});

// Confirmation helper for dangerous actions
function confirmAction(message) {
    return confirm(message || 'Are you sure you want to proceed with this action?');
}
