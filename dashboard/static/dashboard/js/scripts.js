document.getElementById('menuToggle').addEventListener('click', function () {
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('mainContent');
    if (window.innerWidth <= 768) {
        sidebar.classList.toggle('active');
        // Add or remove backdrop
        toggleMobileBackdrop(sidebar.classList.contains('active'));
    } else {
        sidebar.classList.toggle('collapsed');
        mainContent.classList.toggle('expanded');
    }
});

// Improved mobile interaction
document.addEventListener('click', function (event) {
    const sidebar = document.getElementById('sidebar');
    const menuToggle = document.getElementById('menuToggle');
    const backdrop = document.getElementById('mobile-backdrop');
    
    if (window.innerWidth <= 768 && sidebar.classList.contains('active')) {
        // Close sidebar if clicking on backdrop or outside sidebar
        if (backdrop && event.target === backdrop) {
            closeMobileSidebar();
        } else if (!sidebar.contains(event.target) && !menuToggle.contains(event.target)) {
            closeMobileSidebar();
        }
    }
});

// Function to toggle mobile backdrop
function toggleMobileBackdrop(show) {
    let backdrop = document.getElementById('mobile-backdrop');
    
    if (show && !backdrop) {
        backdrop = document.createElement('div');
        backdrop.id = 'mobile-backdrop';
        backdrop.className = 'mobile-backdrop';
        backdrop.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            z-index: 1040;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;
        document.body.appendChild(backdrop);
        // Trigger opacity transition
        setTimeout(() => backdrop.style.opacity = '1', 10);
    } else if (!show && backdrop) {
        backdrop.style.opacity = '0';
        setTimeout(() => {
            if (backdrop.parentNode) {
                backdrop.parentNode.removeChild(backdrop);
            }
        }, 300);
    }
}

// Function to close mobile sidebar
function closeMobileSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.remove('active');
    toggleMobileBackdrop(false);
}

// Auto-close sidebar when clicking on navigation links on mobile
document.addEventListener('DOMContentLoaded', function() {
    const sidebarLinks = document.querySelectorAll('#sidebar a[href]:not([href="#"])');
    sidebarLinks.forEach(link => {
        link.addEventListener('click', function() {
            if (window.innerWidth <= 768) {
                closeMobileSidebar();
            }
        });
    });
});

window.addEventListener('resize', function () {
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('mainContent');
    if (window.innerWidth > 768) {
        sidebar.classList.remove('active');
        if (sidebar.classList.contains('collapsed')) {
            mainContent.classList.add('expanded');
        } else {
            mainContent.classList.remove('expanded');
        }
    } else {
        sidebar.classList.remove('collapsed');
        mainContent.classList.remove('expanded');
    }
});

function showLoading() {
    document.getElementById('loadingOverlay').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loadingOverlay').style.display = 'none';
}

document.querySelectorAll('a[href]').forEach(link => {
    link.addEventListener('click', function (e) {
        if (this.getAttribute('href') !== '#') {
            showLoading();
            setTimeout(hideLoading, 2000);
        }
    });
});

window.addEventListener('load', function () {
    hideLoading();
});

document.addEventListener('DOMContentLoaded', function () {
    // Initialize patient search functionality
    initializePatientSearch();

    // Initialize create patient modal
    initializeCreatePatientModal();
});

function initializePatientSearch() {
    const patientSelect = document.querySelector('select[name="patient"]');
    const searchInput = document.querySelector('#patientSearch');

    if (!patientSelect) return;

    // Convert select to searchable input with dropdown
    createSearchablePatientInput(patientSelect);
}

function createSearchablePatientInput(originalSelect) {
    const wrapper = document.createElement('div');
    wrapper.className = 'patient-search-wrapper position-relative';

    // Create search input
    const searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.className = 'form-control';
    searchInput.placeholder = 'Search for patient by name, email, or ID...';
    searchInput.id = 'patientSearchInput';

    // Create dropdown for results
    const dropdown = document.createElement('div');
    dropdown.className = 'patient-dropdown position-absolute w-100 bg-white border rounded shadow-sm';
    dropdown.style.zIndex = '1050';
    dropdown.style.display = 'none';
    dropdown.style.maxHeight = '200px';
    dropdown.style.overflowY = 'auto';

    // Hidden input to store selected patient ID
    const hiddenInput = document.createElement('input');
    hiddenInput.type = 'hidden';
    hiddenInput.name = originalSelect.name;

    // Replace original select
    originalSelect.parentNode.insertBefore(wrapper, originalSelect);
    wrapper.appendChild(searchInput);
    wrapper.appendChild(dropdown);
    wrapper.appendChild(hiddenInput);
    originalSelect.remove();

    // Add search functionality
    let searchTimeout;
    searchInput.addEventListener('input', function () {
        clearTimeout(searchTimeout);
        const query = this.value.trim();

        if (query.length < 2) {
            hideDropdown();
            return;
        }

        searchTimeout = setTimeout(() => {
            searchPatients(query, dropdown, searchInput, hiddenInput);
        }, 300);
    });

    // Hide dropdown when clicking outside
    document.addEventListener('click', function (e) {
        if (!wrapper.contains(e.target)) {
            hideDropdown();
        }
    });

    function hideDropdown() {
        dropdown.style.display = 'none';
    }

    function showDropdown() {
        dropdown.style.display = 'block';
    }

    function searchPatients(query, dropdown, searchInput, hiddenInput) {
        fetch(`/patients/search/?q=${encodeURIComponent(query)}`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            }
        })
            .then(response => response.json())
            .then(data => {
                dropdown.innerHTML = '';

                if (data.patients.length === 0) {
                    const noResults = document.createElement('div');
                    noResults.className = 'p-3 text-muted text-center';
                    noResults.textContent = 'No patients found';
                    dropdown.appendChild(noResults);

                    // Add "Create Patient" option if user is doctor
                    if (userIsDoctor) {
                        const createOption = document.createElement('div');
                        createOption.className = 'p-2 border-top create-patient-option';
                        createOption.innerHTML = `
                        <button type="button" class="btn btn-sm btn-outline-primary w-100" 
                                onclick="showCreatePatientModal()">
                            <i class="fas fa-user-plus me-1"></i>
                            Create New Patient
                        </button>
                    `;
                        dropdown.appendChild(createOption);
                    }
                } else {
                    data.patients.forEach(patient => {
                        const item = document.createElement('div');
                        item.className = 'patient-item p-2 border-bottom hover-bg-light cursor-pointer';
                        item.innerHTML = `
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <div class="fw-semibold">${patient.name}</div>
                                <small class="text-muted">${patient.email}</small>
                            </div>
                            <small class="text-muted">${patient.patient_id}</small>
                        </div>
                    `;

                        item.addEventListener('click', function () {
                            searchInput.value = patient.name;
                            hiddenInput.value = patient.id;
                            hideDropdown();

                            // Add selected styling
                            searchInput.classList.add('border-success');
                            setTimeout(() => {
                                searchInput.classList.remove('border-success');
                            }, 2000);
                        });

                        dropdown.appendChild(item);
                    });

                    // Add "Create Patient" option at the bottom if user is doctor
                    if (userIsDoctor) {
                        const createOption = document.createElement('div');
                        createOption.className = 'p-2 border-top create-patient-option bg-light';
                        createOption.innerHTML = `
                        <button type="button" class="btn btn-sm btn-outline-primary w-100" 
                                onclick="showCreatePatientModal()">
                            <i class="fas fa-user-plus me-1"></i>
                            Create New Patient
                        </button>
                    `;
                        dropdown.appendChild(createOption);
                    }
                }

                showDropdown();
            })
            .catch(error => {
                console.error('Error searching patients:', error);
                dropdown.innerHTML = '<div class="p-3 text-danger">Error searching patients</div>';
                showDropdown();
            });
    }
}

function initializeCreatePatientModal() {
    // Create modal HTML if it doesn't exist
    if (!document.getElementById('createPatientModal')) {
        const modalContainer = document.createElement('div');
        modalContainer.id = 'createPatientModalContainer';
        document.body.appendChild(modalContainer);
    }
}

function showCreatePatientModal() {
    const modalContainer = document.getElementById('createPatientModalContainer');

    // Show loading state
    modalContainer.innerHTML = `
        <div class="modal fade show" style="display: block;" tabindex="-1">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-body text-center p-4">
                        <div class="spinner-border text-primary mb-3" role="status"></div>
                        <p>Loading patient creation form...</p>
                    </div>
                </div>
            </div>
        </div>
        <div class="modal-backdrop fade show"></div>
    `;

    // Fetch modal content
    fetch('/patients/create/', {
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
        .then(response => response.text())
        .then(html => {
            modalContainer.innerHTML = html;

            // Initialize the modal
            const modal = new bootstrap.Modal(document.getElementById('createPatientModal'));
            modal.show();

            // Clean up when modal is hidden
            document.getElementById('createPatientModal').addEventListener('hidden.bs.modal', function () {
                modalContainer.innerHTML = '';
            });
        })
        .catch(error => {
            console.error('Error loading modal:', error);
            modalContainer.innerHTML = '';
            alert('Error loading patient creation form. Please try again.');
        });
}

// Function called after successful patient creation
function updatePatientDropdown(patientId, patientName) {
    const searchInput = document.getElementById('patientSearchInput');
    const hiddenInput = document.querySelector('input[name="patient"]');

    if (searchInput && hiddenInput) {
        searchInput.value = patientName;
        hiddenInput.value = patientId;

        // Add success styling
        searchInput.classList.add('border-success');
        setTimeout(() => {
            searchInput.classList.remove('border-success');
        }, 3000);

        // Show success message
        const successDiv = document.createElement('div');
        successDiv.className = 'alert alert-success alert-dismissible fade show mt-2';
        successDiv.innerHTML = `
            <i class="fas fa-check-circle me-1"></i>
            Patient created and selected successfully!
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        searchInput.parentNode.appendChild(successDiv);

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (successDiv.parentNode) {
                successDiv.remove();
            }
        }, 5000);
    }
}

// CSS styles to add to your stylesheet
const styles = `
<style>
.patient-search-wrapper {
    position: relative;
}

.patient-dropdown {
    top: 100%;
    left: 0;
    right: 0;
    max-height: 300px;
    overflow-y: auto;
    border: 1px solid #dee2e6;
    border-top: none;
    border-radius: 0 0 0.375rem 0.375rem;
    background: white;
    z-index: 1050;
}

.patient-item {
    cursor: pointer;
    transition: background-color 0.2s ease;
}

.patient-item:hover {
    background-color: #f8f9fa;
}

.patient-item:last-child {
    border-bottom: none;
}

.create-patient-option {
    background-color: #f8f9fa;
    border-top: 2px solid #dee2e6;
}

.hover-bg-light:hover {
    background-color: #f8f9fa;
}

.cursor-pointer {
    cursor: pointer;
}

.border-success {
    border-color: #28a745 !important;
    box-shadow: 0 0 0 0.2rem rgba(40, 167, 69, 0.25);
}

@media (max-width: 768px) {
    .patient-dropdown {
        position: fixed;
        left: 1rem;
        right: 1rem;
        max-height: 50vh;
    }
}
</style>
`;

// Add styles to document head
document.head.insertAdjacentHTML('beforeend', styles);