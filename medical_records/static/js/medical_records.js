class MedicalRecordsManager {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
        this.initializeComponents();
    }

    bindEvents() {
        // Prescription management
        const addPrescriptionBtn = document.getElementById('addPrescription');
        if (addPrescriptionBtn) {
            addPrescriptionBtn.addEventListener('click', () => this.addPrescriptionRow());
        }

        // Remove prescription row
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('remove-prescription')) {
                this.removePrescriptionRow(e.target);
            }
        });

        // Lab test management
        const addLabTestBtn = document.getElementById('addLabTest');
        if (addLabTestBtn) {
            addLabTestBtn.addEventListener('click', () => this.addLabTestRow());
        }

        // Vitals form validation
        const vitalsForm = document.getElementById('vitalsForm');
        if (vitalsForm) {
            vitalsForm.addEventListener('submit', (e) => this.validateVitals(e));
        }

        // Medical record form
        const medicalRecordForm = document.getElementById('medicalRecordForm');
        if (medicalRecordForm) {
            medicalRecordForm.addEventListener('submit', (e) => this.validateMedicalRecord(e));
        }

        // Auto-save drafts
        this.initAutoSave();

        // Print medical record
        const printBtn = document.getElementById('printRecord');
        if (printBtn) {
            printBtn.addEventListener('click', () => this.printMedicalRecord());
        }
    }

    addPrescriptionRow() {
        const container = document.getElementById('prescriptionItems');
        const rowCount = container.children.length;

        const rowHtml = `
            <div class="prescription-row" data-index="${rowCount}">
                <div class="form-row">
                    <div class="form-group">
                        <input type="text" name="medication_name[]" 
                               class="form-control medication-input" 
                               placeholder="Medication name" required>
                        <div class="medication-suggestions"></div>
                    </div>
                    <div class="form-group">
                        <input type="text" name="dosage[]" 
                               class="form-control" 
                               placeholder="e.g., 500mg">
                    </div>
                    <div class="form-group">
                        <select name="frequency[]" class="form-control">
                            <option value="">Select frequency</option>
                            <option value="Once daily">Once daily</option>
                            <option value="Twice daily">Twice daily</option>
                            <option value="Three times daily">Three times daily</option>
                            <option value="Four times daily">Four times daily</option>
                            <option value="Every 4 hours">Every 4 hours</option>
                            <option value="Every 6 hours">Every 6 hours</option>
                            <option value="Every 8 hours">Every 8 hours</option>
                            <option value="As needed">As needed</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <input type="text" name="duration[]" 
                               class="form-control" 
                               placeholder="e.g., 7 days">
                    </div>
                    <div class="form-group">
                        <button type="button" class="btn btn-danger btn-sm remove-prescription">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
                <div class="form-group">
                    <textarea name="instructions[]" 
                              class="form-control" 
                              rows="2" 
                              placeholder="Special instructions (e.g., take with food)"></textarea>
                </div>
            </div>
        `;

        container.insertAdjacentHTML('beforeend', rowHtml);

        // Initialize medication autocomplete for new row
        this.initMedicationAutocomplete(container.lastElementChild);
    }

    removePrescriptionRow(button) {
        const row = button.closest('.prescription-row');
        row.remove();
    }

    addLabTestRow() {
        const container = document.getElementById('labTestItems');
        const rowCount = container.children.length;

        const rowHtml = `
            <div class="lab-test-row" data-index="${rowCount}">
                <div class="form-row">
                    <div class="form-group">
                        <input type="text" name="test_name[]" 
                               class="form-control" 
                               placeholder="Test name" required>
                    </div>
                    <div class="form-group">
                        <select name="priority[]" class="form-control">
                            <option value="routine">Routine</option>
                            <option value="urgent">Urgent</option>
                            <option value="stat">STAT</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <button type="button" class="btn btn-danger btn-sm remove-lab-test">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
                <div class="form-group">
                    <textarea name="test_description[]" 
                              class="form-control" 
                              rows="2" 
                              placeholder="Test description/notes"></textarea>
                </div>
            </div>
        `;

        container.insertAdjacentHTML('beforeend', rowHtml);
    }

    validateVitals(event) {
        const form = event.target;
        const formData = new FormData(form);

        // Validate blood pressure
        const systolic = formData.get('bp_systolic');
        const diastolic = formData.get('bp_diastolic');

        if (systolic && diastolic) {
            if (parseInt(systolic) <= parseInt(diastolic)) {
                this.showAlert('Systolic pressure should be higher than diastolic pressure', 'warning');
                event.preventDefault();
                return;
            }

            // Check for critical values
            if (parseInt(systolic) > 180 || parseInt(diastolic) > 120) {
                if (!confirm('Blood pressure readings are critically high. Continue recording?')) {
                    event.preventDefault();
                    return;
                }
            }
        }

        // Validate temperature
        const temperature = formData.get('temperature');
        if (temperature) {
            const temp = parseFloat(temperature);
            if (temp > 42 || temp < 30) {
                this.showAlert('Temperature reading seems unusual. Please verify.', 'warning');
            }
        }

        // Validate pulse rate
        const pulse = formData.get('pulse_rate');
        if (pulse) {
            const pulseRate = parseInt(pulse);
            if (pulseRate > 150 || pulseRate < 40) {
                if (!confirm('Pulse rate is outside normal range. Continue recording?')) {
                    event.preventDefault();
                    return;
                }
            }
        }
    }

    validateMedicalRecord(event) {
        const form = event.target;
        const diagnosis = form.querySelector('textarea[name="diagnosis"]').value.trim();
        const symptoms = form.querySelector('textarea[name="symptoms"]').value.trim();
        const treatmentPlan = form.querySelector('textarea[name="treatment_plan"]').value.trim();

        if (!diagnosis) {
            this.showAlert('Diagnosis is required', 'error');
            event.preventDefault();
            return;
        }

        if (!symptoms) {
            this.showAlert('Symptoms description is required', 'error');
            event.preventDefault();
            return;
        }

        if (!treatmentPlan) {
            this.showAlert('Treatment plan is required', 'error');
            event.preventDefault();
            return;
        }

        // Check for prescription drug interactions
        this.checkDrugInteractions();
    }

    checkDrugInteractions() {
        const medications = Array.from(document.querySelectorAll('input[name="medication_name[]"]'))
            .map(input => input.value.trim())
            .filter(med => med);

        if (medications.length > 1) {
            // Simple interaction check (in real app, use drug database API)
            const warningCombinations = [
                ['warfarin', 'aspirin'],
                ['warfarin', 'ibuprofen'],
                ['metformin', 'alcohol']
            ];

            for (let combo of warningCombinations) {
                const hasInteraction = combo.every(drug =>
                    medications.some(med => med.toLowerCase().includes(drug))
                );

                if (hasInteraction) {
                    this.showAlert(`Potential drug interaction detected: ${combo.join(' + ')}`, 'warning');
                }
            }
        }
    }

    initMedicationAutocomplete(container) {
        const input = container.querySelector('.medication-input');
        const suggestions = container.querySelector('.medication-suggestions');

        if (!input || !suggestions) return;

        let debounceTimer;

        input.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                this.searchMedications(e.target.value, suggestions);
            }, 300);
        });

        // Hide suggestions when clicking outside
        document.addEventListener('click', (e) => {
            if (!container.contains(e.target)) {
                suggestions.style.display = 'none';
            }
        });
    }

    searchMedications(query, suggestionsElement) {
        if (query.length < 2) {
            suggestionsElement.style.display = 'none';
            return;
        }

        // Mock medication database - in real app, use proper API
        const medications = [
            'Paracetamol', 'Ibuprofen', 'Aspirin', 'Amoxicillin', 'Ciprofloxacin',
            'Metformin', 'Amlodipine', 'Lisinopril', 'Simvastatin', 'Omeprazole',
            'Prednisolone', 'Dexamethasone', 'Insulin', 'Warfarin', 'Heparin'
        ];

        const matches = medications.filter(med =>
            med.toLowerCase().includes(query.toLowerCase())
        );

        if (matches.length === 0) {
            suggestionsElement.style.display = 'none';
            return;
        }

        suggestionsElement.innerHTML = matches.map(med =>
            `<div class="suggestion-item" onclick="this.parentElement.previousElementSibling.value='${med}'; this.parentElement.style.display='none';">
                ${med}
            </div>`
        ).join('');

        suggestionsElement.style.display = 'block';
    }

    initAutoSave() {
        const forms = document.querySelectorAll('form[data-autosave="true"]');

        forms.forEach(form => {
            const formId = form.id || 'medical_form';
            let autoSaveTimer;

            form.addEventListener('input', () => {
                clearTimeout(autoSaveTimer);
                autoSaveTimer = setTimeout(() => {
                    this.saveDraft(form, formId);
                }, 30000); // Auto-save every 30 seconds
            });

            // Load saved draft on page load
            this.loadDraft(form, formId);
        });
    }

    saveDraft(form, formId) {
        const formData = new FormData(form);
        const data = {};

        for (let [key, value] of formData.entries()) {
            data[key] = value;
        }

        localStorage.setItem(`draft_${formId}`, JSON.stringify(data));

        // Show save indicator
        this.showSaveIndicator();
    }

    loadDraft(form, formId) {
        const savedData = localStorage.getItem(`draft_${formId}`);

        if (savedData) {
            try {
                const data = JSON.parse(savedData);

                for (let [key, value] of Object.entries(data)) {
                    const input = form.querySelector(`[name="${key}"]`);
                    if (input) {
                        input.value = value;
                    }
                }

                this.showAlert('Draft loaded from previous session', 'info');
            } catch (error) {
                console.error('Error loading draft:', error);
            }
        }
    }

    showSaveIndicator() {
        const indicator = document.getElementById('saveIndicator') || this.createSaveIndicator();
        indicator.textContent = 'Draft saved';
        indicator.style.display = 'block';

        setTimeout(() => {
            indicator.style.display = 'none';
        }, 2000);
    }

    createSaveIndicator() {
        const indicator = document.createElement('div');
        indicator.id = 'saveIndicator';
        indicator.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--success);
            color: white;
            padding: 10px 15px;
            border-radius: 4px;
            z-index: 1000;
            display: none;
        `;
        document.body.appendChild(indicator);
        return indicator;
    }

    printMedicalRecord() {
        const printContent = document.getElementById('recordPrintArea').innerHTML;
        const originalContent = document.body.innerHTML;

        document.body.innerHTML = printContent;
        window.print();
        document.body.innerHTML = originalContent;

        // Reinitialize after print
        this.init();
    }

    initializeComponents() {
        // Initialize any existing prescription rows
        document.querySelectorAll('.prescription-row').forEach(row => {
            this.initMedicationAutocomplete(row);
        });

        // Initialize data tables if present
        const recordsTable = document.getElementById('recordsTable');
        if (recordsTable && typeof DataTable !== 'undefined') {
            new DataTable(recordsTable, {
                pageLength: 25,
                order: [[0, 'desc']],
                columnDefs: [
                    { targets: -1, orderable: false }
                ]
            });
        }
    }

    showAlert(message, type = 'info') {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="close" onclick="this.parentElement.remove()">
                <span>&times;</span>
            </button>
        `;

        const container = document.querySelector('.main-content');
        container.insertBefore(alert, container.firstChild);

        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }

    // Patient timeline functionality
    loadPatientTimeline(patientId) {
        fetch(`/medical-records/api/medical-history/${patientId}/`)
            .then(response => response.json())
            .then(data => this.renderTimeline(data))
            .catch(error => console.error('Error loading timeline:', error));
    }

    renderTimeline(data) {
        const timeline = document.getElementById('patientTimeline');
        if (!timeline) return;

        timeline.innerHTML = data.map(record => `
            <div class="timeline-item">
                <div class="timeline-date">${this.formatDate(record.created_at)}</div>
                <div class="timeline-content">
                    <h5>${record.diagnosis}</h5>
                    <p><strong>Doctor:</strong> Dr. ${record.doctor_name}</p>
                    <p><strong>Symptoms:</strong> ${record.symptoms}</p>
                    <p><strong>Treatment:</strong> ${record.treatment_plan}</p>
                </div>
            </div>
        `).join('');
    }

    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('en-GB', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }

    // Vital signs chart
    initVitalsChart(patientId) {
        fetch(`/medical-records/vitals/${patientId}/history/`)
            .then(response => response.json())
            .then(data => this.renderVitalsChart(data))
            .catch(error => console.error('Error loading vitals:', error));
    }

    renderVitalsChart(vitalsData) {
        const chartContainer = document.getElementById('vitalsChart');
        if (!chartContainer || !vitalsData.length) return;

        // Prepare data for chart
        const dates = vitalsData.map(v => this.formatDate(v.recorded_at));
        const bpSystolic = vitalsData.map(v => v.blood_pressure_systolic);
        const bpDiastolic = vitalsData.map(v => v.blood_pressure_diastolic);
        const pulse = vitalsData.map(v => v.pulse_rate);
        const temperature = vitalsData.map(v => v.temperature);

        // Simple canvas-based chart (you can replace with Chart.js or similar)
        this.drawVitalsChart(chartContainer, {
            dates,
            bpSystolic,
            bpDiastolic,
            pulse,
            temperature
        });
    }

    drawVitalsChart(container, data) {
        // Basic implementation - replace with proper charting library
        container.innerHTML = `
            <div class="chart-placeholder">
                <h4>Vital Signs Trend</h4>
                <p>Last ${data.dates.length} recordings</p>
                <div class="vitals-summary">
                    <div class="vital-item">
                        <label>Latest BP:</label>
                        <span>${data.bpSystolic[0]}/${data.bpDiastolic[0]} mmHg</span>
                    </div>
                    <div class="vital-item">
                        <label>Latest Pulse:</label>
                        <span>${data.pulse[0]} bpm</span>
                    </div>
                    <div class="vital-item">
                        <label>Latest Temperature:</label>
                        <span>${data.temperature[0]}°C</span>
                    </div>
                </div>
            </div>
        `;
    }
}

// Prescription template manager
class PrescriptionTemplates {
    constructor() {
        this.templates = this.loadTemplates();
        this.init();
    }

    init() {
        const templateSelect = document.getElementById('prescriptionTemplate');
        if (templateSelect) {
            templateSelect.addEventListener('change', (e) => {
                this.applyTemplate(e.target.value);
            });
        }

        const saveTemplateBtn = document.getElementById('savePrescriptionTemplate');
        if (saveTemplateBtn) {
            saveTemplateBtn.addEventListener('click', () => this.saveCurrentAsTemplate());
        }
    }

    loadTemplates() {
        const saved = localStorage.getItem('prescription_templates');
        return saved ? JSON.parse(saved) : this.getDefaultTemplates();
    }

    getDefaultTemplates() {
        return {
            'common_cold': {
                name: 'Common Cold',
                medications: [
                    {
                        name: 'Paracetamol',
                        dosage: '500mg',
                        frequency: 'Three times daily',
                        duration: '5 days',
                        instructions: 'Take with food'
                    },
                    {
                        name: 'Vitamin C',
                        dosage: '1000mg',
                        frequency: 'Once daily',
                        duration: '7 days',
                        instructions: 'Take with water'
                    }
                ]
            },
            'hypertension': {
                name: 'Hypertension Management',
                medications: [
                    {
                        name: 'Amlodipine',
                        dosage: '5mg',
                        frequency: 'Once daily',
                        duration: '30 days',
                        instructions: 'Take in the morning'
                    },
                    {
                        name: 'Hydrochlorothiazide',
                        dosage: '25mg',
                        frequency: 'Once daily',
                        duration: '30 days',
                        instructions: 'Take with breakfast'
                    }
                ]
            }
        };
    }

    applyTemplate(templateId) {
        if (!templateId || !this.templates[templateId]) return;

        const template = this.templates[templateId];
        const container = document.getElementById('prescriptionItems');

        // Clear existing prescriptions
        container.innerHTML = '';

        // Add template medications
        template.medications.forEach((med, index) => {
            const medicalRecordsManager = new MedicalRecordsManager();
            medicalRecordsManager.addPrescriptionRow();

            const row = container.children[index];
            if (row) {
                row.querySelector('input[name="medication_name[]"]').value = med.name;
                row.querySelector('input[name="dosage[]"]').value = med.dosage;
                row.querySelector('select[name="frequency[]"]').value = med.frequency;
                row.querySelector('input[name="duration[]"]').value = med.duration;
                row.querySelector('textarea[name="instructions[]"]').value = med.instructions;
            }
        });
    }

    saveCurrentAsTemplate() {
        const templateName = prompt('Enter template name:');
        if (!templateName) return;

        const medications = this.getCurrentPrescriptions();
        if (medications.length === 0) {
            alert('No prescriptions to save');
            return;
        }

        const templateId = templateName.toLowerCase().replace(/\s+/g, '_');
        this.templates[templateId] = {
            name: templateName,
            medications: medications
        };

        this.saveTemplates();
        this.updateTemplateSelect();

        alert('Template saved successfully!');
    }

    getCurrentPrescriptions() {
        const rows = document.querySelectorAll('.prescription-row');
        const medications = [];

        rows.forEach(row => {
            const name = row.querySelector('input[name="medication_name[]"]').value.trim();
            if (name) {
                medications.push({
                    name: name,
                    dosage: row.querySelector('input[name="dosage[]"]').value,
                    frequency: row.querySelector('select[name="frequency[]"]').value,
                    duration: row.querySelector('input[name="duration[]"]').value,
                    instructions: row.querySelector('textarea[name="instructions[]"]').value
                });
            }
        });

        return medications;
    }

    saveTemplates() {
        localStorage.setItem('prescription_templates', JSON.stringify(this.templates));
    }

    updateTemplateSelect() {
        const select = document.getElementById('prescriptionTemplate');
        if (!select) return;

        select.innerHTML = '<option value="">Select a template...</option>';

        Object.entries(this.templates).forEach(([id, template]) => {
            const option = document.createElement('option');
            option.value = id;
            option.textContent = template.name;
            select.appendChild(option);
        });
    }
}

// Drug interaction checker
class DrugInteractionChecker {
    constructor() {
        this.interactions = this.loadInteractionDatabase();
    }

    loadInteractionDatabase() {
        // Simplified interaction database
        return {
            'warfarin': {
                'aspirin': 'Increased bleeding risk',
                'ibuprofen': 'Increased bleeding risk',
                'paracetamol': 'Monitor INR levels'
            },
            'metformin': {
                'alcohol': 'Risk of lactic acidosis',
                'contrast_dye': 'Discontinue before imaging'
            },
            'simvastatin': {
                'amlodipine': 'Reduce simvastatin dose',
                'clarithromycin': 'Avoid combination'
            }
        };
    }

    checkInteractions(medications) {
        const interactions = [];
        const drugList = medications.map(med => med.toLowerCase().trim());

        for (let i = 0; i < drugList.length; i++) {
            for (let j = i + 1; j < drugList.length; j++) {
                const drug1 = this.findDrugKey(drugList[i]);
                const drug2 = this.findDrugKey(drugList[j]);

                if (drug1 && drug2) {
                    const interaction = this.getInteraction(drug1, drug2);
                    if (interaction) {
                        interactions.push({
                            drugs: [drugList[i], drugList[j]],
                            warning: interaction
                        });
                    }
                }
            }
        }

        return interactions;
    }

    findDrugKey(drugName) {
        return Object.keys(this.interactions).find(key =>
            drugName.includes(key) || key.includes(drugName)
        );
    }

    getInteraction(drug1, drug2) {
        if (this.interactions[drug1] && this.interactions[drug1][drug2]) {
            return this.interactions[drug1][drug2];
        }
        if (this.interactions[drug2] && this.interactions[drug2][drug1]) {
            return this.interactions[drug2][drug1];
        }
        return null;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    // Initialize main medical records manager
    const medicalRecordsManager = new MedicalRecordsManager();

    // Initialize prescription templates
    const prescriptionTemplates = new PrescriptionTemplates();
    prescriptionTemplates.updateTemplateSelect();

    // Initialize drug interaction checker
    window.drugChecker = new DrugInteractionChecker();

    // Add interaction checking to prescription forms
    document.addEventListener('input', function (e) {
        if (e.target.matches('input[name="medication_name[]"]')) {
            setTimeout(() => {
                checkCurrentPrescriptionInteractions();
            }, 500);
        }
    });

    function checkCurrentPrescriptionInteractions() {
        const medications = Array.from(document.querySelectorAll('input[name="medication_name[]"]'))
            .map(input => input.value.trim())
            .filter(med => med);

        if (medications.length > 1) {
            const interactions = window.drugChecker.checkInteractions(medications);
            displayInteractionWarnings(interactions);
        }
    }

    function displayInteractionWarnings(interactions) {
        // Remove existing warnings
        document.querySelectorAll('.interaction-warning').forEach(el => el.remove());

        if (interactions.length === 0) return;

        const warningContainer = document.createElement('div');
        warningContainer.className = 'interaction-warning alert alert-warning';
        warningContainer.innerHTML = `
            <h5><i class="fas fa-exclamation-triangle"></i> Drug Interaction Warnings</h5>
            <ul>
                ${interactions.map(interaction =>
            `<li><strong>${interaction.drugs.join(' + ')}:</strong> ${interaction.warning}</li>`
        ).join('')}
            </ul>
        `;

        const prescriptionContainer = document.getElementById('prescriptionItems');
        if (prescriptionContainer) {
            prescriptionContainer.parentNode.insertBefore(warningContainer, prescriptionContainer);
        }
    }
});