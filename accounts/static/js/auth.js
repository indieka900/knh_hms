(function () {
    window.toggleForms = function toggleForms() {
        const loginForm = document.getElementById('loginForm');
        const registerForm = document.getElementById('registerForm');

        loginForm.classList.toggle('active');
        registerForm.classList.toggle('active');
    }

    // Password strength checker
    function checkPasswordStrength(password) {
        const strengthElement = document.getElementById('passwordStrength');
        const strengthBar = strengthElement.querySelector('.strength-bar');
        const strengthLabel = document.getElementById('strengthLabel');

        let strength = 0;
        let label = 'Weak';

        // Check password criteria
        if (password.length >= 8) strength++;
        if (/[a-z]/.test(password)) strength++;
        if (/[A-Z]/.test(password)) strength++;
        if (/[0-9]/.test(password)) strength++;
        if (/[^A-Za-z0-9]/.test(password)) strength++;

        // Update strength indicator
        strengthBar.className = 'strength-bar';
        if (strength <= 2) {
            strengthBar.classList.add('strength-weak');
            label = 'Weak';
        } else if (strength <= 4) {
            strengthBar.classList.add('strength-medium');
            label = 'Medium';
        } else {
            strengthBar.classList.add('strength-strong');
            label = 'Strong';
        }

        strengthLabel.textContent = label;

        if (password.length > 0) {
            strengthElement.classList.add('show');
        } else {
            strengthElement.classList.remove('show');
        }
    }

    // Password confirmation validation
    function validatePasswordConfirmation() {
        const password = document.getElementById('registerPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        const confirmInput = document.getElementById('confirmPassword');

        if (confirmPassword && password !== confirmPassword) {
            confirmInput.style.borderColor = 'var(--danger)';
            return false;
        } else {
            confirmInput.style.borderColor = 'var(--primary-light)';
            return true;
        }
    }

    // Form submission with loading state
    function handleFormSubmit(formId, buttonId) {
        const form = document.getElementById(formId);
        const button = document.getElementById(buttonId);

        form.addEventListener('submit', function (e) {
            // Add loading state
            button.classList.add('loading');
            button.disabled = true;

            // For demo purposes - remove this in production
            setTimeout(() => {
                button.classList.remove('loading');
                button.disabled = false;
            }, 2000);
        });
    }

    // Event listeners
    document.addEventListener('DOMContentLoaded', function () {
        // Password strength checker
        const passwordInput = document.getElementById('registerPassword');
        if (passwordInput) {
            passwordInput.addEventListener('input', function () {
                checkPasswordStrength(this.value);
            });
        }

        // Password confirmation validation
        const confirmPasswordInput = document.getElementById('confirmPassword');
        if (confirmPasswordInput) {
            confirmPasswordInput.addEventListener('input', validatePasswordConfirmation);
            passwordInput.addEventListener('input', validatePasswordConfirmation);
        }

        // Form submission handlers
        handleFormSubmit('loginForm', 'loginBtn');
        handleFormSubmit('registerForm', 'registerBtn');

        // Input focus animations
        const inputs = document.querySelectorAll('.form-input, .form-select');
        inputs.forEach(input => {
            input.addEventListener('focus', function () {
                this.parentElement.style.transform = 'scale(1.02)';
            });

            input.addEventListener('blur', function () {
                this.parentElement.style.transform = 'scale(1)';
            });
        });
    });

    // Auto-resize for mobile
    function adjustForMobile() {
        if (window.innerWidth <= 768) {
            const authContainer = document.querySelector('.auth-container');
            authContainer.style.minHeight = 'auto';
        }
    }

    window.addEventListener('resize', adjustForMobile);
    window.addEventListener('load', adjustForMobile);
})();