function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    const container = document.getElementById('alertContainer') || document.body;
    container.prepend(alertDiv);

    setTimeout(() => alertDiv.remove(), 5000);
}

// Set up search bar using vanilla JS
function setupSearchHandlerVanilla() {
    const searchInput = document.getElementById('searchInput');
    const patientRows = document.querySelectorAll('.patient-row');

    if (!searchInput) return;

    searchInput.addEventListener('input', function () {
        const query = this.value.toLowerCase();

        patientRows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(query) ? '' : 'none';
        });
    });
}

// Calculate new patients (dummy logic)
function calculateNewPatients() {
    const patientRows = document.querySelectorAll('.patient-row');
    const newPatients = Math.floor(patientRows.length / 3);
    const badge = document.getElementById('newPatientsBadge');

    if (badge) badge.textContent = newPatients;
}

// Handle viewing patient details in modal
function viewPatient(patientId) {
    console.log('Viewing patient:', patientId);

    try {
        const patientRows = document.querySelectorAll('.patient-row');
        let patientRow = null;

        patientRows.forEach(function (row) {
            const badge = row.querySelector('.patient-id-badge');
            if (badge && badge.textContent.trim() === patientId) {
                patientRow = row;
            }
        });

        if (!patientRow) {
            alert('Patient not found');
            return;
        }

        const patientName = patientRow.querySelector('.fw-bold')?.textContent ?? 'N/A';
        const patientGender = patientRow.querySelector('.gender-badge')?.textContent.trim() ?? 'Not specified';
        const bloodGroup = patientRow.querySelector('.blood-group-badge')?.textContent.trim() ?? 'Not specified';
        const contactInfoEls = patientRow.querySelectorAll('.contact-info');
        const contactInfo = contactInfoEls[0]?.textContent.trim() ?? 'Not available';
        const emergencyContact = contactInfoEls[1]?.textContent.trim() ?? 'Not available';
        const registeredDate = patientRow.cells[patientRow.cells.length - 2]?.textContent.trim() ?? 'Not available';

        const detailsHtml = `
            <div class="row">
                <div class="col-md-6">
                    <h6>Personal Info</h6>
                    <div>Full Name: ${patientName}</div>
                    <div>Patient ID: ${patientId}</div>
                    <div>Gender: ${patientGender}</div>
                    <div>Blood Group: ${bloodGroup}</div>
                </div>
                <div class="col-md-6">
                    <h6>Contact Info</h6>
                    <div>Contact: ${contactInfo}</div>
                    <div>Emergency: ${emergencyContact}</div>
                    <div>Registered: ${registeredDate}</div>
                </div>
            </div>
        `;

        const contentEl = document.getElementById('patientDetailsContent');
        if (contentEl) {
            contentEl.innerHTML = detailsHtml;
        }

        // Safely show the modal
        const modalEl = document.getElementById('patientDetailsModal');
        if (modalEl) {
            // Remove any lingering aria-hidden attributes
            modalEl.removeAttribute('aria-hidden');

            const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
            modal.show();

            // Wait for modal to fully show before manipulating focus
            modalEl.addEventListener('shown.bs.modal', () => {
                modalEl.focus(); // Set focus to modal safely
            }, { once: true });
        }

    } catch (error) {
        console.error('Error:', error);
    }
}


// Handle edit button click
function setupEditPatientBtn() {
    const editBtn = document.getElementById('editPatientBtn');

    if (editBtn) {
        editBtn.addEventListener('click', () => {
            const patientId = editBtn.getAttribute('data-patient-id');
            if (patientId) {
                window.location.href = `/patients/${patientId}/edit/`;
            }
        });
    }
}

// Initialize the script
window.addEventListener('DOMContentLoaded', () => {
    setupSearchHandlerVanilla();
    setupEditPatientBtn();
    calculateNewPatients();
});
