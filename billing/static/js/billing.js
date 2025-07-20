class BillingManager {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
        this.initializeDataTables();
    }

    bindEvents() {
        // Bill creation form
        const addItemBtn = document.getElementById('addBillItem');
        if (addItemBtn) {
            addItemBtn.addEventListener('click', () => this.addBillItem());
        }

        // Remove item buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('remove-item')) {
                this.removeBillItem(e.target);
            }
        });

        // Calculate totals when quantities or prices change
        document.addEventListener('input', (e) => {
            if (e.target.matches('.quantity-input, .price-input')) {
                this.calculateRowTotal(e.target);
                this.calculateBillTotal();
            }
        });

        // Service type selection
        document.addEventListener('change', (e) => {
            if (e.target.matches('.service-select')) {
                this.updateServicePrice(e.target);
            }
        });

        // Payment processing
        const paymentForm = document.getElementById('paymentForm');
        if (paymentForm) {
            paymentForm.addEventListener('submit', (e) => this.processPayment(e));
        }

        // Print bill
        const printBtn = document.getElementById('printBill');
        if (printBtn) {
            printBtn.addEventListener('click', () => this.printBill());
        }
    }

    addBillItem() {
        const container = document.getElementById('billItems');
        const itemCount = container.children.length;

        const itemHtml = `
            <div class="bill-item-row" data-index="${itemCount}">
                <div class="form-group">
                    <select name="service[]" class="form-control service-select" required>
                        <option value="">Select Service</option>
                        ${this.getServiceOptions()}
                    </select>
                </div>
                <div class="form-group">
                    <input type="text" name="description[]" 
                           class="form-control" placeholder="Description">
                </div>
                <div class="form-group">
                    <input type="number" name="quantity[]" 
                           class="form-control quantity-input" 
                           value="1" min="1" required>
                </div>
                <div class="form-group">
                    <input type="number" name="unit_price[]" 
                           class="form-control price-input" 
                           step="0.01" min="0" required>
                </div>
                <div class="form-group">
                    <input type="text" class="form-control total-display" 
                           readonly placeholder="0.00">
                </div>
                <div class="form-group">
                    <button type="button" class="btn btn-danger btn-sm remove-item">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;

        container.insertAdjacentHTML('beforeend', itemHtml);
    }

    removeBillItem(button) {
        const row = button.closest('.bill-item-row');
        row.remove();
        this.calculateBillTotal();
    }

    calculateRowTotal(input) {
        const row = input.closest('.bill-item-row');
        const quantity = row.querySelector('.quantity-input').value || 0;
        const unitPrice = row.querySelector('.price-input').value || 0;
        const total = (parseFloat(quantity) * parseFloat(unitPrice)).toFixed(2);

        row.querySelector('.total-display').value = `KSh ${total}`;
    }

    calculateBillTotal() {
        const rows = document.querySelectorAll('.bill-item-row');
        let total = 0;

        rows.forEach(row => {
            const quantity = row.querySelector('.quantity-input').value || 0;
            const unitPrice = row.querySelector('.price-input').value || 0;
            total += parseFloat(quantity) * parseFloat(unitPrice);
        });

        const totalDisplay = document.getElementById('billTotal');
        if (totalDisplay) {
            totalDisplay.textContent = `KSh ${total.toFixed(2)}`;
        }
    }

    updateServicePrice(select) {
        const serviceId = select.value;
        if (serviceId) {
            // Fetch service price via AJAX
            fetch(`/billing/api/service-price/${serviceId}/`)
                .then(response => response.json())
                .then(data => {
                    const row = select.closest('.bill-item-row');
                    const priceInput = row.querySelector('.price-input');
                    const descInput = row.querySelector('input[name="description[]"]');

                    priceInput.value = data.price;
                    if (!descInput.value) {
                        descInput.value = data.name;
                    }

                    this.calculateRowTotal(priceInput);
                    this.calculateBillTotal();
                })
                .catch(error => console.error('Error fetching service price:', error));
        }
    }

    getServiceOptions() {
        // This would be populated from Django template context
        // For now, return empty string - should be populated server-side
        return '';
    }

    processPayment(event) {
        event.preventDefault();

        const form = event.target;
        const formData = new FormData(form);
        const amount = formData.get('amount');
        const billTotal = parseFloat(document.querySelector('.bill-total').dataset.total);
        const amountPaid = parseFloat(document.querySelector('.amount-paid').dataset.paid);
        const balance = billTotal - amountPaid;

        // Validate payment amount
        if (parseFloat(amount) > balance) {
            this.showAlert('Payment amount cannot exceed outstanding balance', 'error');
            return;
        }

        if (parseFloat(amount) <= 0) {
            this.showAlert('Payment amount must be greater than zero', 'error');
            return;
        }

        // Show confirmation
        const paymentMethod = formData.get('payment_method');
        const confirmMsg = `Process payment of KSh ${amount} via ${paymentMethod}?`;

        if (confirm(confirmMsg)) {
            form.submit();
        }
    }

    printBill() {
        const printContent = document.getElementById('billPrintArea').innerHTML;
        const originalContent = document.body.innerHTML;

        document.body.innerHTML = printContent;
        window.print();
        document.body.innerHTML = originalContent;

        // Reinitialize after print
        this.init();
    }

    initializeDataTables() {
        // Initialize DataTables for bill lists if present
        const billTable = document.getElementById('billsTable');
        if (billTable && typeof DataTable !== 'undefined') {
            new DataTable(billTable, {
                pageLength: 25,
                order: [[0, 'desc']], // Sort by date descending
                columnDefs: [
                    { targets: -1, orderable: false } // Disable sorting on action column
                ]
            });
        }
    }

    showAlert(message, type = 'info') {
        // Create alert element
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="close" onclick="this.parentElement.remove()">
                <span>&times;</span>
            </button>
        `;

        // Insert at top of page
        const container = document.querySelector('.main-content');
        container.insertBefore(alert, container.firstChild);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }

    // Patient search functionality
    searchPatients(query, callback) {
        if (query.length < 2) {
            callback([]);
            return;
        }

        fetch(`/patients/api/search/?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => callback(data.results))
            .catch(error => {
                console.error('Error searching patients:', error);
                callback([]);
            });
    }

    // Format currency
    formatCurrency(amount) {
        return `KSh ${parseFloat(amount).toLocaleString('en-KE', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        })}`;
    }

    // Get CSRF token
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }
}

// Patient search autocomplete
class PatientSearch {
    constructor(inputElement, resultsElement, onSelect) {
        this.input = inputElement;
        this.results = resultsElement;
        this.onSelect = onSelect;
        this.debounceTimer = null;

        this.init();
    }

    init() {
        this.input.addEventListener('input', (e) => {
            clearTimeout(this.debounceTimer);
            this.debounceTimer = setTimeout(() => {
                this.search(e.target.value);
            }, 300);
        });

        // Hide results when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.input.contains(e.target) && !this.results.contains(e.target)) {
                this.hideResults();
            }
        });
    }

    search(query) {
        if (query.length < 2) {
            this.hideResults();
            return;
        }

        fetch(`/patients/search/?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => this.displayResults(data.patients))
            .catch(error => {
                console.error('Search error:', error);
                this.hideResults();
            });
    }

    selectPatient(patient) {
        this.input.value = `${patient.name} (${patient.patient_id})`;
        this.hideResults();

        const hiddenInput = document.getElementById('selectedPatientId');
        if (hiddenInput) {
            hiddenInput.value = patient.patient_id;
        }

        if (this.onSelect) {
            this.onSelect(patient);
        }

        // Load pending bills for selected patient (instead of appointments)
        loadPatientPendingBills(patient.patient_id);
    }

    displayResults(patients) {
        this.results.innerHTML = '';

        if (patients.length === 0) {
            this.hideResults();
            return;
        }

        patients.forEach(patient => {
            const div = document.createElement('div');
            div.className = 'search-result-item';
            div.innerHTML = `
                <div class="patient-info">
                    <strong>${patient.name}</strong>
                    <small>ID: ${patient.patient_id}</small>
                </div>
            `;

            div.addEventListener('click', () => {
                this.selectPatient(patient);
            });

            this.results.appendChild(div);
        });

        this.showResults();
    }

    showResults() {
        this.results.style.display = 'block';
    }

    hideResults() {
        this.results.style.display = 'none';
    }
}

// Function to load pending bills for a patient
function loadPatientPendingBills(patientId) {
    const billSelect = document.getElementById('patientBills');
    const paymentAmount = document.getElementById('paymentAmount');
    const balanceInfo = document.getElementById('balanceInfo');

    if (!billSelect) return;

    // Clear existing options and show loading
    billSelect.innerHTML = '<option value="">Loading bills...</option>';

    // Clear payment amount and balance info
    if (paymentAmount) paymentAmount.value = '';
    if (balanceInfo) balanceInfo.textContent = '';

    fetch(`/billing/api/patient-pending-bills/${patientId}/`)
        .then(response => response.json())
        .then(data => {
            billSelect.innerHTML = '<option value="">Select a bill...</option>';

            if (data.bills.length === 0) {
                const option = document.createElement('option');
                option.text = 'No pending bills found';
                option.disabled = true;
                billSelect.appendChild(option);
            } else {
                data.bills.forEach(bill => {
                    const option = document.createElement('option');
                    option.value = bill.bill_id;
                    option.dataset.totalAmount = bill.total_amount;
                    option.dataset.paidAmount = bill.paid_amount || 0;
                    option.dataset.balance = bill.balance;
                    option.textContent = `${bill.bill_id} - KSh ${parseFloat(bill.balance).toLocaleString('en-KE', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                    })} (Due: ${bill.due_date})`;
                    billSelect.appendChild(option);
                });
            }
        })
        .catch(error => {
            console.error('Error loading bills:', error);
            billSelect.innerHTML = '<option value="">Error loading bills</option>';
        });
}

// Function to handle bill selection and auto-fill payment amount
function handleBillSelection() {
    const billSelect = document.getElementById('patientBills');
    const paymentAmount = document.getElementById('paymentAmount');
    const balanceInfo = document.getElementById('balanceInfo');

    if (!billSelect || !paymentAmount || !balanceInfo) return;

    billSelect.addEventListener('change', function () {
        const selectedOption = this.selectedOptions[0];

        if (selectedOption && selectedOption.value) {
            const balance = parseFloat(selectedOption.dataset.balance) || 0;
            const totalAmount = parseFloat(selectedOption.dataset.totalAmount) || 0;
            const paidAmount = parseFloat(selectedOption.dataset.paidAmount) || 0;

            // Auto-fill the payment amount with the balance
            paymentAmount.value = balance.toFixed(2);
            paymentAmount.max = balance; // Set max to prevent overpayment

            // Show balance information
            balanceInfo.innerHTML = `
                <strong>Bill Details:</strong><br>
                Total: KSh ${totalAmount.toLocaleString('en-KE', { minimumFractionDigits: 2 })} | 
                Paid: KSh ${paidAmount.toLocaleString('en-KE', { minimumFractionDigits: 2 })} | 
                <span class="text-danger">Balance: KSh ${balance.toLocaleString('en-KE', { minimumFractionDigits: 2 })}</span>
            `;
        } else {
            paymentAmount.value = '';
            paymentAmount.removeAttribute('max');
            balanceInfo.textContent = '';
        }
    });
}

// Function to validate payment amount
function validatePaymentAmount() {
    const paymentAmount = document.getElementById('paymentAmount');
    const billSelect = document.getElementById('patientBills');

    if (!paymentAmount || !billSelect) return;

    paymentAmount.addEventListener('input', function () {
        const selectedOption = billSelect.selectedOptions[0];
        if (selectedOption && selectedOption.value) {
            const balance = parseFloat(selectedOption.dataset.balance) || 0;
            const enteredAmount = parseFloat(this.value) || 0;

            if (enteredAmount > balance) {
                this.setCustomValidity(`Amount cannot exceed balance of KSh ${balance.toFixed(2)}`);
            } else if (enteredAmount <= 0) {
                this.setCustomValidity('Amount must be greater than 0');
            } else {
                this.setCustomValidity('');
            }
        }
    });
}

// Initialize the quick payment modal
function initializeQuickPayment() {
    const patientSearchInput = document.getElementById('patientSearch');
    const patientResults = document.getElementById('patientResults');

    if (patientSearchInput && patientResults) {
        new PatientSearch(patientSearchInput, patientResults, (patient) => {
            console.log('Patient selected:', patient);
        });
    }

    // Initialize bill selection handler
    handleBillSelection();

    // Initialize payment amount validation
    validatePaymentAmount();

    // Handle form submission
    const quickPaymentForm = document.getElementById('quickPaymentForm');
    if (quickPaymentForm) {
        quickPaymentForm.addEventListener('submit', handleQuickPaymentSubmission);
    }
}

// Handle form submission
function handleQuickPaymentSubmission(e) {
    e.preventDefault();

    const formData = new FormData();
    formData.append('patient_id', document.getElementById('selectedPatientId').value);
    formData.append('bill_id', document.getElementById('patientBills').value);
    formData.append('amount', document.getElementById('paymentAmount').value);
    formData.append('payment_method', document.getElementById('paymentMethod').value);
    formData.append('transaction_ref', document.getElementById('transactionRef').value || '');
    formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);

    // Submit the payment
    fetch('/billing/api/quick-payment/', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Payment processed successfully!');
                closeQuickPayment();
                // Optionally refresh the page or update the UI
                location.reload();
            } else {
                alert('Error processing payment: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Payment error:', error);
            alert('Error processing payment. Please try again.');
        });
}

// Functions to open and close the modal
function openQuickPayment() {
    document.getElementById('quickPaymentModal').style.display = 'block';
}

function closeQuickPayment() {
    const modal = document.getElementById('quickPaymentModal');
    modal.style.display = 'none';

    // Reset form
    document.getElementById('quickPaymentForm').reset();
    document.getElementById('selectedPatientId').value = '';
    document.getElementById('patientBills').innerHTML = '<option value="">Select a bill...</option>';
    document.getElementById('balanceInfo').textContent = '';
    document.getElementById('patientResults').style.display = 'none';
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    new BillingManager();
    initializeQuickPayment();

    // Initialize patient search if elements exist
    const patientInput = document.getElementById('patientSearch');
    const patientResults = document.getElementById('patientResults');

    if (patientInput && patientResults) {
        new PatientSearch(patientInput, patientResults, (patient) => {
            // Handle patient selection
            console.log('Selected patient:', patient);
        });
    }
});