function checkConflicts() {
    const formData = new FormData(document.getElementById('appointmentForm'));

    fetch('/appointments/check-conflicts/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.conflicts && data.conflicts.length > 0) {
                showConflictModal(data.conflicts);
            } else {
                submitForm();
            }
        })
        .catch(error => {
            console.error('Error checking conflicts:', error);
            submitForm();
        });
}

function submitForm() {
    document.getElementById('appointmentForm').submit();
}

function showConflictModal(conflicts) {
    const conflictMessage = document.getElementById('conflictMessage');
    let message = '<ul>';
    conflicts.forEach(conflict => {
        message += `<li style="margin-bottom: 5px;">${conflict}</li>`;
    });
    message += '</ul>';
    conflictMessage.innerHTML = message;
    showModal('conflictModal');
}

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

// Update appointment status
function updateStatus(appointmentId, newStatus) {
    fetch(`/appointments/update-status/${appointmentId}/${newStatus}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        },
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert(data.message || 'Failed to update status.');
            }
        })
        .catch(error => {
            console.error('Error updating status:', error);
        });
}

// Show cancel confirmation modal
let appointmentToCancel = null;

// Modal helpers
function showModal(modalId) {
    document.getElementById(modalId).style.display = 'block';
}

function hideModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

function showCancelModal(appointmentId) {
    appointmentToCancel = appointmentId;
    showModal('cancelModal');
}

function confirmCancel() {
    if (appointmentToCancel) {
        updateStatus(appointmentToCancel, 'cancelled');
        hideModal('cancelModal');
    }
}





document.addEventListener('DOMContentLoaded', function () {
    const timeSlots = [
        '08:00', '08:30', '09:00', '09:30', '10:00', '10:30', '11:00', '11:30',
        '12:00', '12:30', '13:00', '13:30', '14:00', '14:30', '15:00', '15:30',
        '16:00', '16:30', '17:00', '17:30', '18:00', '18:30', '19:00', '19:30'
    ];

    // Safely load template values
    const userIsDoctor = "{{ user_is_doctor|yesno:'true,false'|default:'false' }}" === "true";
    const userIsPatient = "{{ user_is_patient|yesno:'true,false'|default:'false' }}" === "true";
    const isEditing = "{{ object|yesno:'true,false'|default:'false' }}" === "true";
    const currentTimeValue = "{{ object.appointment_time|time:'H:i' }}" || '';

    // Populate time slots
    function populateTimeSlots() {
        const timeSelect = document.getElementById('id_appointment_time');
        const currentValue = currentTimeValue || timeSelect.value;

        timeSelect.innerHTML = '<option value="">Select time...</option>';

        timeSlots.forEach(time => {
            const option = document.createElement('option');
            option.value = time;
            option.textContent = formatTime(time);
            if (time === currentValue) {
                option.selected = true;
            }
            timeSelect.appendChild(option);
        });
    }

    // Format time for display
    function formatTime(time) {
        const [hours, minutes] = time.split(':');
        const hour = parseInt(hours);
        const ampm = hour >= 12 ? 'PM' : 'AM';
        const displayHour = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour;
        return `${displayHour}:${minutes} ${ampm}`;
    }

    // Get current doctor ID
    function getCurrentDoctorId() {
        if (userIsDoctor) {
            return '{{ current_doctor.doctor_id |default: "" }}';
        } else {
            const doctorSelect = document.getElementById('id_doctor');
            return doctorSelect ? doctorSelect.value : null;
        }
    }

    // Update doctor information
    function updateDoctorInfo() {
        const doctorSelect = document.getElementById('id_doctor');
        const doctorInfo = document.getElementById('doctorInfo');
        const doctorSpecialization = document.getElementById('doctorSpecialization');
        const doctorFee = document.getElementById('doctorFee');

        let doctorId, specialization, fee;

        if (userIsDoctor) {
            doctorId = '{{ current_doctor.doctor_id|default:"" }}';
            specialization = '{{ current_doctor.specialization |default: "" }}';
            fee = '{{ current_doctor.consultation_fee |default: "" }}';
        } else if (doctorSelect && doctorSelect.value) {
            const selectedOption = doctorSelect.selectedOptions[0];
            doctorId = doctorSelect.value;
            specialization = selectedOption.getAttribute('data-specialization');
            fee = selectedOption.getAttribute('data-fee');
        }

        if (doctorId) {
            doctorSpecialization.textContent = specialization || 'Not specified';
            doctorFee.textContent = fee ? `$${fee}` : 'Not specified';
            doctorInfo.style.display = 'block';

            loadAvailableSlots();
        } else {
            doctorInfo.style.display = 'none';
            document.getElementById('availableSlots').style.display = 'none';
        }
    }

    document.getElementById('id_appointment_date').addEventListener('change', function () {
        loadAvailableSlots();
    });

    // Load available time slots
    function loadAvailableSlots() {
        const doctorId = getCurrentDoctorId();
        const date = document.getElementById('id_appointment_date').value;
        const appointmentId = isEditing ? '{{ object.appointment_id |default: "" }}' : null;

        if (doctorId && date) {
            let url = `/appointments/available-slots/?doctor=${doctorId}&date=${date}`;
            if (appointmentId) {
                url += `&appointment_id=${appointmentId}`;
            }

            fetch(url)
                .then(response => response.json())
                .then(data => {
                    displayAvailableSlots(data.slots);
                })
                .catch(error => {
                    console.error('Error loading available slots:', error);
                });
        }
    }

    // Display available slots
    function displayAvailableSlots(slots) {
        const slotsContainer = document.getElementById('slotsContainer');
        const availableSlots = document.getElementById('availableSlots');

        slotsContainer.innerHTML = '';

        if (slots.length > 0) {
            slots.forEach(slot => {
                const slotButton = document.createElement('button');
                slotButton.type = 'button';
                slotButton.className = 'btn btn-sm btn-secondary';
                slotButton.textContent = formatTime(slot);
                slotButton.onclick = (e) => selectTimeSlot(slot, e);

                const currentTime = document.getElementById('id_appointment_time').value;
                if (slot === currentTime) {
                    slotButton.className = 'btn btn-sm btn-primary';
                }

                slotsContainer.appendChild(slotButton);
            });
            availableSlots.style.display = 'block';
        } else {
            availableSlots.style.display = 'none';
        }
    }

    // Select a time slot
    function selectTimeSlot(time, event) {
        document.getElementById('id_appointment_time').value = time;
        document.querySelectorAll('#slotsContainer button').forEach(btn => {
            btn.className = 'btn btn-sm btn-secondary';
        });
        event.target.className = 'btn btn-sm btn-primary';
    }



    // Event listeners
    const doctorSelect = document.getElementById('id_doctor');
    if (doctorSelect) {
        doctorSelect.addEventListener('change', updateDoctorInfo);
    }

    document.getElementById('id_appointment_date').addEventListener('change', loadAvailableSlots);

    // Initialize
    populateTimeSlots();

    if (userIsDoctor || (isEditing && getCurrentDoctorId())) {
        updateDoctorInfo();
    }

    if (getCurrentDoctorId() && document.getElementById('id_appointment_date').value) {
        loadAvailableSlots();
    }
});
