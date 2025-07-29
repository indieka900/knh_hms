let patients = [];
let prescriptions = [];
let medicines = [];
let inventory = [];
let dispensingHistory = [];
let stats = {
    totalPatients: 0,
    pendingPrescriptions: 0,
    lowStockItems: 0,
    todayDispensed: 0
};

// CSRF Token for Django
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

// Initialize Dashboard
document.addEventListener('DOMContentLoaded', function () {
    console.log('Dashboard initializing...');
    loadDataFromBackend();
    initializeInteractiveElements();
    setupEventListeners();
});

// Load data from Django backend
async function loadDataFromBackend() {
    try {
        // Load dashboard data
        const response = await fetch('/pharmacy/api/pharmacy-dashboard-data/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            }
        });

        if (response.ok) {
            const data = await response.json();

            // Update stats from backend
            stats = {
                totalPatients: data.stats.total_patients,
                pendingPrescriptions: data.stats.pending_prescriptions || 0,
                lowStockItems: data.stats.low_stock_items,
                todayDispensed: data.stats.today_dispensed
            };

            // Convert backend data to frontend format
            patients = data.recent_patients.map(patient => ({
                id: patient.patient_id,
                name: `${patient.first_name} ${patient.last_name}`,
                phone: patient.phone_number,
                email: patient.email,
                age: patient.age,
                address: patient.address,
                lastVisit: patient.created_at ? patient.created_at.split('T')[0] : 'N/A'
            }));

            // Convert inventory data
            inventory = data.critical_inventory.map(item => ({
                id: item.id,
                medicineId: item.medicine.id,
                medicineName: `${item.medicine.name} ${item.medicine.strength || ''}`,
                batchNumber: item.batch_number,
                quantity: item.quantity_in_stock,
                unitPrice: parseFloat(item.unit_price),
                expiryDate: item.expiry_date,
                supplier: item.supplier,
                minStockLevel: item.minimum_stock_level,
                dateReceived: item.date_received
            }));

            // Convert dispensing history
            dispensingHistory = data.recent_dispensing.map(record => ({
                id: record.id,
                prescriptionId: record.prescription_id,
                patientName: `${record.prescription.patient.first_name} ${record.prescription.patient.last_name}`,
                medicineName: `${record.inventory_item.medicine.name} ${record.inventory_item.medicine.strength || ''}`,
                quantity: record.quantity_dispensed,
                dispensedAt: new Date(record.dispensed_at).toLocaleString(),
                pharmacist: record.pharmacist ? `${record.pharmacist.first_name} ${record.pharmacist.last_name}` : 'Unknown',
                notes: record.notes || ''
            }));

            // Update all displays
            updateStats();
            renderPatients();
            renderPrescriptions();
            renderInventory();
            renderDispensingHistory();
            populateMedicineSelect();

        } else {
            console.error('Failed to load dashboard data');
            showAlert('Failed to load dashboard data', 'danger');
        }
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showAlert('Error loading dashboard data', 'danger');
    }
}

// Load patients from backend
async function loadPatients() {
    try {
        const response = await fetch('/pharmacy/api/patients/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            }
        });

        if (response.ok) {
            const data = await response.json();
            patients = data.map(patient => ({
                id: patient.patient_id,
                name: `${patient.first_name} ${patient.last_name}`,
                phone: patient.phone_number,
                email: patient.email,
                age: patient.age,
                address: patient.address,
                lastVisit: patient.created_at ? patient.created_at.split('T')[0] : 'N/A'
            }));
            renderPatients();
        }
    } catch (error) {
        console.error('Error loading patients:', error);
    }
}

// Load inventory from backend
async function loadInventory() {
    try {
        const response = await fetch('/pharmacy/api/inventory/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            }
        });

        if (response.ok) {
            const data = await response.json();
            inventory = data.map(item => ({
                id: item.id,
                medicineId: item.medicine.id,
                medicineName: `${item.medicine.name} ${item.medicine.strength || ''}`,
                batchNumber: item.batch_number,
                quantity: item.quantity_in_stock,
                unitPrice: parseFloat(item.unit_price),
                expiryDate: item.expiry_date,
                supplier: item.supplier,
                minStockLevel: item.minimum_stock_level,
                dateReceived: item.date_received
            }));
            renderInventory();
            populateMedicineSelect();
        }
    } catch (error) {
        console.error('Error loading inventory:', error);
    }
}

// Load prescriptions from backend
async function loadPrescriptions() {
    try {
        const response = await fetch('/pharmacy/api/prescriptions/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            }
        });

        if (response.ok) {
            const data = await response.json();
            prescriptions = data.prescriptions.map(prescription => ({
                id: prescription.id,
                patientName: prescription.patient_name,
                doctor: prescription.doctor,
                date: prescription.date,
                medicines: prescription.medicines,
                status: prescription.status,
                patientId: prescription.patient_id
            }));
            renderPrescriptions();
        } else {
            console.error('Failed to load prescriptions');
            showAlert('Failed to load prescriptions', 'danger');
        }
    } catch (error) {
        console.error('Error loading prescriptions:', error);
        showAlert('Error loading prescriptions', 'danger');
    }
}

// Statistics Update
function updateStats() {
    const totalPatientsEl = document.getElementById('totalPatients');
    const pendingPrescriptionsEl = document.getElementById('pendingPrescriptions');
    const lowStockItemsEl = document.getElementById('lowStockItems');
    const todayDispensedEl = document.getElementById('todayDispensed');

    if (totalPatientsEl) totalPatientsEl.textContent = stats.totalPatients;
    if (pendingPrescriptionsEl) pendingPrescriptionsEl.textContent = stats.pendingPrescriptions;
    if (lowStockItemsEl) lowStockItemsEl.textContent = stats.lowStockItems;
    if (todayDispensedEl) todayDispensedEl.textContent = stats.todayDispensed;
}

// Patient Management
function renderPatients() {
    const tbody = document.getElementById('patientsTableBody');
    if (!tbody) return;

    tbody.innerHTML = '';

    patients.forEach(patient => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${patient.id}</td>
            <td class="text-truncate-mobile">${patient.name}</td>
            <td class="d-none d-md-table-cell">${patient.phone}</td>
            <td class="d-none d-lg-table-cell">${patient.lastVisit}</td>
            <td>
                <div class="btn-group" role="group">
                    <button class="btn btn-sm btn-outline-primary" onclick="viewPatient('${patient.id}')" title="View">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-warning" onclick="editPatient('${patient.id}')" title="Edit">
                        <i class="fas fa-edit"></i>
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// Prescription Management
function renderPrescriptions() {
    const container = document.getElementById('prescriptionsList');
    if (!container) {
        console.error('prescriptionsList container not found');
        return;
    }

    container.innerHTML = '';

    if (!prescriptions || prescriptions.length === 0) {
        container.innerHTML = '<div class="alert alert-info">No prescriptions found.</div>';
        return;
    }

    prescriptions.forEach(prescription => {
        const statusBadge = prescription.status === 'pending' ? 'status-in-progress' : 'status-confirmed';
        const prescriptionDiv = document.createElement('div');
        prescriptionDiv.className = 'prescription-item';
        prescriptionDiv.innerHTML = `
            <div class="d-flex flex-column flex-md-row justify-content-between">
                <div class="flex-grow-1 mb-2 mb-md-0">
                    <h5>Prescription #${prescription.id}</h5>
                    <p class="mb-1"><strong>Patient:</strong> ${prescription.patientName}</p>
                    <p class="mb-1"><strong>Doctor:</strong> ${prescription.doctor}</p>
                    <p class="mb-1"><strong>Date:</strong> ${prescription.date}</p>
                    <p class="mb-0"><strong>Medicines:</strong> ${prescription.medicines.length > 0 ? prescription.medicines.join(', ') : 'No medicines listed'}</p>
                </div>
                <div class="d-flex flex-column align-items-md-end">
                    <span class="status-badge ${statusBadge} mb-2">${prescription.status.toUpperCase()}</span>
                    ${prescription.status === 'pending' ?
                `<button class="btn btn-sm btn-success" onclick="dispensePrescription('${prescription.id}')">
                            <i class="fas fa-pills me-1"></i>Dispense
                        </button>` : ''}
                </div>
            </div>
        `;
        container.appendChild(prescriptionDiv);
    });
}

// Inventory Management
function renderInventory() {
    const tbody = document.getElementById('inventoryTableBody');
    if (!tbody) return;

    tbody.innerHTML = '';

    inventory.forEach(item => {
        const row = document.createElement('tr');
        let statusClass = '';
        let status = 'Normal';
        let badgeColor = 'bg-success';

        if (item.quantity <= 5) {
            statusClass = 'inventory-critical';
            status = 'Critical';
            badgeColor = 'bg-danger';
        } else if (item.quantity <= item.minStockLevel) {
            statusClass = 'inventory-low';
            status = 'Low Stock';
            badgeColor = 'bg-warning';
        }

        // Check expiry date
        const expiryDate = new Date(item.expiryDate);
        const today = new Date();
        const monthsToExpiry = (expiryDate - today) / (1000 * 60 * 60 * 24 * 30);

        if (monthsToExpiry < 3) {
            status = 'Expiring Soon';
            statusClass = 'inventory-critical';
            badgeColor = 'bg-danger';
        }

        const statusBadgeClass = status === 'Normal' ? 'status-confirmed' :
            status === 'Low Stock' ? 'status-in-progress' : 'status-cancelled';

        row.className = statusClass;
        row.innerHTML = `
            <td class="text-truncate-mobile">${item.medicineName}</td>
            <td><span class="badge ${badgeColor}">${item.quantity}</span></td>
            <td class="d-none d-md-table-cell">${item.expiryDate}</td>
            <td><span class="status-badge ${statusBadgeClass}">${status}</span></td>
            <td>
                <div class="btn-group" role="group">
                    <button class="btn btn-sm btn-outline-primary" onclick="viewInventoryItem('${item.id}')" title="View">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-warning" onclick="updateStock('${item.id}')" title="Update">
                        <i class="fas fa-sync"></i>
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// Dispensing History Management
function renderDispensingHistory() {
    const container = document.getElementById('dispensingList');
    if (!container) return;

    container.innerHTML = '';

    if (!dispensingHistory || dispensingHistory.length === 0) {
        container.innerHTML = '<div class="alert alert-info">No dispensing history found.</div>';
        return;
    }

    dispensingHistory.forEach(record => {
        const recordDiv = document.createElement('div');
        recordDiv.className = 'card mb-2';
        recordDiv.innerHTML = `
            <div class="card-body p-3">
                <div class="d-flex flex-column flex-md-row justify-content-between">
                    <div class="flex-grow-1">
                        <h6 class="card-title mb-1">${record.patientName} - ${record.medicineName}</h6>
                        <p class="card-text small text-muted mb-1">Quantity: ${record.quantity}</p>
                        <p class="card-text small text-muted mb-1">Pharmacist: ${record.pharmacist}</p>
                        <p class="card-text small text-muted mb-0">Dispensed: ${record.dispensedAt}</p>
                        ${record.notes ? `<p class="card-text small text-muted mb-0">Notes: ${record.notes}</p>` : ''}
                    </div>
                    <div class="text-md-end mt-2 mt-md-0">
                        <span class="badge bg-success">Completed</span>
                    </div>
                </div>
            </div>
        `;
        container.appendChild(recordDiv);
    });
}

// Populate medicine select dropdown
function populateMedicineSelect() {
    const select = document.getElementById('medicineSelect');
    if (!select) return;

    select.innerHTML = '<option value="">Select Medicine</option>';

    inventory.forEach(item => {
        if (item.quantity > 0) {
            const option = document.createElement('option');
            option.value = item.id;
            option.textContent = `${item.medicineName} (Stock: ${item.quantity})`;
            select.appendChild(option);
        }
    });
}

// Search Functions
function setupSearchFunctionality() {
    // Patient search
    const patientSearch = document.getElementById('patientSearch');
    if (patientSearch) {
        patientSearch.addEventListener('keyup', function () {
            const searchTerm = this.value.toLowerCase();
            const filteredPatients = patients.filter(patient =>
                patient.name.toLowerCase().includes(searchTerm) ||
                patient.phone.includes(searchTerm) ||
                patient.id.toLowerCase().includes(searchTerm)
            );
            renderFilteredPatients(filteredPatients);
        });
    }

    // Prescription search
    const prescriptionSearch = document.getElementById('prescriptionSearch');
    if (prescriptionSearch) {
        prescriptionSearch.addEventListener('keyup', function () {
            const searchTerm = this.value.toLowerCase();
            const filteredPrescriptions = prescriptions.filter(prescription =>
                prescription.id.toLowerCase().includes(searchTerm) ||
                prescription.patientName.toLowerCase().includes(searchTerm) ||
                prescription.doctor.toLowerCase().includes(searchTerm) ||
                prescription.medicines.some(medicine => medicine.toLowerCase().includes(searchTerm))
            );
            renderFilteredPrescriptions(filteredPrescriptions);
        });
    }

    // Inventory search
    const inventorySearch = document.getElementById('inventorySearch');
    if (inventorySearch) {
        inventorySearch.addEventListener('keyup', function () {
            const searchTerm = this.value.toLowerCase();
            const filteredInventory = inventory.filter(item =>
                item.medicineName.toLowerCase().includes(searchTerm) ||
                item.batchNumber.toLowerCase().includes(searchTerm) ||
                item.supplier.toLowerCase().includes(searchTerm)
            );
            renderFilteredInventory(filteredInventory);
        });
    }
}

function renderFilteredPatients(filteredPatients) {
    const tbody = document.getElementById('patientsTableBody');
    if (!tbody) return;

    tbody.innerHTML = '';

    filteredPatients.forEach(patient => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${patient.id}</td>
            <td class="text-truncate-mobile">${patient.name}</td>
            <td class="d-none d-md-table-cell">${patient.phone}</td>
            <td class="d-none d-lg-table-cell">${patient.lastVisit}</td>
            <td>
                <div class="btn-group" role="group">
                    <button class="btn btn-sm btn-outline-primary" onclick="viewPatient('${patient.id}')" title="View">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-warning" onclick="editPatient('${patient.id}')" title="Edit">
                        <i class="fas fa-edit"></i>
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function renderFilteredPrescriptions(filteredPrescriptions) {
    const container = document.getElementById('prescriptionsList');
    if (!container) return;

    container.innerHTML = '';

    if (filteredPrescriptions.length === 0) {
        container.innerHTML = '<div class="alert alert-info">No matching prescriptions found.</div>';
        return;
    }

    filteredPrescriptions.forEach(prescription => {
        const statusBadge = prescription.status === 'pending' ? 'status-in-progress' : 'status-confirmed';
        const prescriptionDiv = document.createElement('div');
        prescriptionDiv.className = 'prescription-item';
        prescriptionDiv.innerHTML = `
            <div class="d-flex flex-column flex-md-row justify-content-between">
                <div class="flex-grow-1 mb-2 mb-md-0">
                    <h5>Prescription #${prescription.id}</h5>
                    <p class="mb-1"><strong>Patient:</strong> ${prescription.patientName}</p>
                    <p class="mb-1"><strong>Doctor:</strong> ${prescription.doctor}</p>
                    <p class="mb-1"><strong>Date:</strong> ${prescription.date}</p>
                    <p class="mb-0"><strong>Medicines:</strong> ${prescription.medicines.length > 0 ? prescription.medicines.join(', ') : 'No medicines listed'}</p>
                </div>
                <div class="d-flex flex-column align-items-md-end">
                    <span class="status-badge ${statusBadge} mb-2">${prescription.status.toUpperCase()}</span>
                    ${prescription.status === 'pending' ?
                `<button class="btn btn-sm btn-success" onclick="dispensePrescription('${prescription.id}')">
                            <i class="fas fa-pills me-1"></i>Dispense
                        </button>` : ''}
                </div>
            </div>
        `;
        container.appendChild(prescriptionDiv);
    });
}

function renderFilteredInventory(filteredInventory) {
    const tbody = document.getElementById('inventoryTableBody');
    if (!tbody) return;

    tbody.innerHTML = '';

    filteredInventory.forEach(item => {
        const row = document.createElement('tr');
        let statusClass = '';
        let status = 'Normal';
        let badgeColor = 'bg-success';

        if (item.quantity <= 5) {
            statusClass = 'inventory-critical';
            status = 'Critical';
            badgeColor = 'bg-danger';
        } else if (item.quantity <= item.minStockLevel) {
            statusClass = 'inventory-low';
            status = 'Low Stock';
            badgeColor = 'bg-warning';
        }

        const expiryDate = new Date(item.expiryDate);
        const today = new Date();
        const monthsToExpiry = (expiryDate - today) / (1000 * 60 * 60 * 24 * 30);

        if (monthsToExpiry < 3) {
            status = 'Expiring Soon';
            statusClass = 'inventory-critical';
            badgeColor = 'bg-danger';
        }

        const statusBadgeClass = status === 'Normal' ? 'status-confirmed' :
            status === 'Low Stock' ? 'status-in-progress' : 'status-cancelled';

        row.className = statusClass;
        row.innerHTML = `
            <td class="text-truncate-mobile">${item.medicineName}</td>
            <td><span class="badge ${badgeColor}">${item.quantity}</span></td>
            <td class="d-none d-md-table-cell">${item.expiryDate}</td>
            <td><span class="status-badge ${statusBadgeClass}">${status}</span></td>
            <td>
                <div class="btn-group" role="group">
                    <button class="btn btn-sm btn-outline-primary" onclick="viewInventoryItem('${item.id}')" title="View">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-warning" onclick="updateStock('${item.id}')" title="Update">
                        <i class="fas fa-sync"></i>
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// Event Listeners Setup
function setupEventListeners() {
    // Form handlers
    const patientForm = document.getElementById('patientForm');
    if (patientForm) {
        patientForm.addEventListener('submit', handlePatientFormSubmit);
    }

    const medicineForm = document.getElementById('medicineForm');
    if (medicineForm) {
        medicineForm.addEventListener('submit', handleMedicineFormSubmit);
    }

    const dispensingForm = document.getElementById('dispensingForm');
    if (dispensingForm) {
        dispensingForm.addEventListener('submit', handleDispensingFormSubmit);
    }

    // Setup search functionality
    setupSearchFunctionality();

    // Bootstrap tab event listeners
    const patientTabs = document.querySelectorAll('#patientTabs button[data-bs-toggle="tab"]');
    patientTabs.forEach(tab => {
        tab.addEventListener('shown.bs.tab', function (event) {
            const target = event.target.getAttribute('data-bs-target');
            if (target === '#patients') {
                loadPatients();
            } else if (target === '#prescriptions') {
                loadPrescriptions();
            }
        });
    });

    const inventoryTabs = document.querySelectorAll('#inventoryTabs button[data-bs-toggle="tab"]');
    inventoryTabs.forEach(tab => {
        tab.addEventListener('shown.bs.tab', function (event) {
            const target = event.target.getAttribute('data-bs-target');
            if (target === '#inventory') {
                loadInventory();
            }
        });
    });
}

// Form Handlers
async function handlePatientFormSubmit(e) {
    e.preventDefault();

    const formData = new FormData(e.target);
    const patientData = {
        first_name: formData.get('patientName').split(' ')[0],
        last_name: formData.get('patientName').split(' ').slice(1).join(' '),
        phone_number: formData.get('patientPhone'),
        email: formData.get('patientEmail'),
        age: parseInt(formData.get('patientAge')),
        address: formData.get('patientAddress')
    };

    try {
        const response = await fetch('/api/patients/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify(patientData)
        });

        if (response.ok) {
            await loadPatients();
            await loadDataFromBackend();
            const modal = bootstrap.Modal.getInstance(document.getElementById('patientModal'));
            modal.hide();
            showAlert('Patient added successfully!', 'success');
            e.target.reset();
        } else {
            const error = await response.json();
            showAlert('Error adding patient: ' + JSON.stringify(error), 'danger');
        }
    } catch (error) {
        console.error('Error adding patient:', error);
        showAlert('Error adding patient', 'danger');
    }
}

async function handleMedicineFormSubmit(e) {
    e.preventDefault();

    const formData = new FormData(e.target);
    const data = {};

    for (let [key, value] of formData.entries()) {
        if (key === 'expiry_date') {
            const date = new Date(value);
            if (isNaN(date)) {
                showAlert('Invalid expiry date', 'danger');
                return;
            }
            data[key] = date.toISOString().split('T')[0];
        } else if (['quantity_in_stock', 'unit_price', 'minimum_stock_level'].includes(key)) {
            data[key] = Number(value);
        } else {
            data[key] = value;
        }
    }

    try {
        const response = await fetch('/pharmacy/api/inventory/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (response.ok) {
            const modalElement = document.getElementById('medicineModal');
            let modal = bootstrap.Modal.getInstance(modalElement);

            if (!modal) {
                modal = new bootstrap.Modal(modalElement);
            }

            modal.hide();
            showAlert('Medicine added to inventory successfully!', 'success');
            e.target.reset();
            await loadInventory();
            await loadDataFromBackend();
        } else {
            showAlert(result.error || 'Failed to add medicine to inventory', 'danger');
        }
    } catch (error) {
        console.error('Error submitting form:', error);
        showAlert('Network error occurred', 'danger');
    }
}


async function handleDispensingFormSubmit(e) {
    e.preventDefault();

    const dispensingData = {
        prescription_id: document.getElementById('prescriptionId').value,
        inventory_item_id: document.getElementById('medicineSelect').value,
        quantity_dispensed: parseInt(document.getElementById('dispenseQuantity').value),
        notes: document.getElementById('dispensingNotes').value
    };

    try {
        const response = await fetch('/pharmacy/api/dispensing/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify(dispensingData)
        });

        if (response.ok) {
            await loadDataFromBackend();
            const modal = bootstrap.Modal.getInstance(document.getElementById('dispensingModal'));
            modal.hide();
            showAlert('Medicine dispensed successfully!', 'success');
            e.target.reset();
        } else {
            const error = await response.json();
            showAlert('Error dispensing medicine: ' + JSON.stringify(error), 'danger');
        }
    } catch (error) {
        console.error('Error dispensing medicine:', error);
        showAlert('Error dispensing medicine', 'danger');
    }
}

// Helper Functions
function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = `
        top: 20px;
        right: 20px;
        z-index: 9999;
        max-width: 300px;
    `;

    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(alertDiv);

    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

function viewPatient(patientId) {
    const patient = patients.find(p => p.id === patientId);
    if (patient) {
        alert(`Patient Details:\n\nName: ${patient.name}\nPhone: ${patient.phone}\nEmail: ${patient.email}\nAge: ${patient.age}\nAddress: ${patient.address}\nLast Visit: ${patient.lastVisit}`);
    }
}

function editPatient(patientId) {
    const patient = patients.find(p => p.id === patientId);
    if (patient) {
        document.getElementById('patientName').value = patient.name;
        document.getElementById('patientPhone').value = patient.phone;
        document.getElementById('patientEmail').value = patient.email;
        document.getElementById('patientAge').value = patient.age;
        document.getElementById('patientAddress').value = patient.address;

        const modal = new bootstrap.Modal(document.getElementById('patientModal'));
        modal.show();
        showAlert('Edit functionality would need API endpoint for updates', 'info');
    }
}

function viewInventoryItem(itemId) {
    const item = inventory.find(i => i.id === itemId);
    if (item) {
        alert(`Inventory Details:\n\nMedicine: ${item.medicineName}\nBatch: ${item.batchNumber}\nQuantity: ${item.quantity}\nUnit Price: ${item.unitPrice}\nExpiry: ${item.expiryDate}\nSupplier: ${item.supplier}\nMin Stock: ${item.minStockLevel}`);
    }
}

async function updateStock(itemId) {
    const item = inventory.find(i => i.id === itemId);
    if (item) {
        const newQuantity = prompt(`Current stock: ${item.quantity}\nEnter new quantity:`, item.quantity);
        if (newQuantity !== null && !isNaN(newQuantity) && newQuantity >= 0) {
            try {
                const response = await fetch(`/pharmacy/api/inventory/${itemId}/update-stock/`, {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrftoken
                    },
                    body: JSON.stringify({
                        quantity_in_stock: parseInt(newQuantity)
                    })
                });

                if (response.ok) {
                    await loadInventory();
                    await loadDataFromBackend(); // Refresh stats
                    showAlert('Stock updated successfully!', 'success');
                } else {
                    showAlert('Error updating stock', 'danger');
                }
            } catch (error) {
                console.error('Error updating stock:', error);
                showAlert('Error updating stock', 'danger');
            }
        }
    }
}

function dispensePrescription(prescriptionId) {
    document.getElementById('prescriptionId').value = prescriptionId;
    openModal('dispensingModal');
}

// Initialize interactive elements
function initializeInteractiveElements() {
    // Add hover effects for better UX
    const cards = document.querySelectorAll('.stat-card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function () {
            this.style.transform = 'translateY(-5px)';
        });

        card.addEventListener('mouseleave', function () {
            this.style.transform = 'translateY(0)';
        });
    });
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'block';
    }
}


function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
    }
}

function switchTab(tabName, element) {
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(tab => tab.style.display = 'none');

    const tabButtons = document.querySelectorAll('.nav-tab');
    tabButtons.forEach(btn => btn.classList.remove('active'));

    document.getElementById(tabName).style.display = 'block';
    element.classList.add('active');
}


// Auto-refresh data every 5 minutes
setInterval(loadDataFromBackend, 300000);