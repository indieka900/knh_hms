/* ── State ── */
let patients          = [];
let prescriptions     = [];
let inventory         = [];
let dispensingHistory = [];

/* ── CSRF ── */
function getCsrf() {
  const m = document.cookie.match(/csrftoken=([^;]+)/);
  return m ? decodeURIComponent(m[1]) : '';
}

/* ══════════════════════════════════════
   BOOTSTRAP MODAL HELPERS
══════════════════════════════════════ */
function openModal(id)  { bootstrap.Modal.getOrCreateInstance(document.getElementById(id)).show(); }
function closeModal(id) { bootstrap.Modal.getOrCreateInstance(document.getElementById(id)).hide(); }

/* ══════════════════════════════════════
   TOAST
══════════════════════════════════════ */
function toast(msg, type = 'info') {
  const c = document.getElementById('ph-toasts');
  if (!c) return;
  const icons = { success:'fa-check-circle', danger:'fa-times-circle', info:'fa-info-circle' };
  const cls   = { success:'ph-t-s', danger:'ph-t-d', info:'ph-t-i' };
  const el    = document.createElement('div');
  el.className = `ph-t ${cls[type] || cls.info}`;
  el.innerHTML = `<i class="fas ${icons[type] || icons.info}"></i><span>${msg}</span>`;
  c.appendChild(el);
  setTimeout(() => el.remove(), 4500);
}

/* ══════════════════════════════════════
   TAB PANE SWITCHER
══════════════════════════════════════ */
function switchPane(showId, hideId, btn) {
  document.getElementById(showId)?.classList.remove('d-none');
  document.getElementById(hideId)?.classList.add('d-none');

  /* Update Bootstrap nav-link active state in the same nav */
  btn.closest('ul')?.querySelectorAll('.nav-link').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');

  if (showId === 'prescriptions' && prescriptions.length === 0) loadPrescriptions();
}

/* ══════════════════════════════════════
   STATUS BADGE HTML  (inline styles — no CSS class dependency)
══════════════════════════════════════ */
const STATUS_STYLES = {
  Normal:   { bg:'#dcfce7', color:'#166534' },
  Low:      { bg:'#fef9c3', color:'#854d0e' },
  Critical: { bg:'#fee2e2', color:'#991b1b' },
  Expiring: { bg:'#ffedd5', color:'#9a3412' },
};

function pillHtml(label) {
  const s = STATUS_STYLES[label] || { bg:'#e2e8f0', color:'#475569' };
  return `<span style="display:inline-flex;align-items:center;padding:.2rem .65rem;border-radius:999px;font-size:.72rem;font-weight:700;background:${s.bg};color:${s.color}">${label}</span>`;
}

function stockStatus(item) {
  const days = (new Date(item.expiry) - new Date()) / 86400000;
  if (days < 90)              return 'Expiring';
  if (item.qty <= 5)          return 'Critical';
  if (item.qty <= item.minStock) return 'Low';
  return 'Normal';
}

/* ══════════════════════════════════════
   INIT
══════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', () => {
  loadDashboard();
  document.getElementById('medicineForm')  ?.addEventListener('submit', submitMedicine);
  document.getElementById('patientForm')   ?.addEventListener('submit', submitPatient);
  document.getElementById('dispensingForm')?.addEventListener('submit', submitDispensing);
});

/* ══════════════════════════════════════
   DATA LOADING
══════════════════════════════════════ */
async function loadDashboard() {
  try {
    const res  = await fetch('/pharmacy/api/pharmacy-dashboard-data/');
    if (!res.ok) { toast('Failed to load dashboard data', 'danger'); return; }
    const data = await res.json();

    setText('totalPatients',        data.stats.total_patients);
    setText('pendingPrescriptions', data.stats.pending_prescriptions || 0);
    setText('lowStockItems',        data.stats.low_stock_items);
    setText('todayDispensed',       data.stats.today_dispensed);

    patients = (data.recent_patients || []).map(p => ({
      id:        p.patient_id,
      name:      `${p.first_name} ${p.last_name}`,
      phone:     p.phone_number || '—',
      email:     p.email        || '—',
      age:       p.age          ?? '—',
      address:   p.address      || '—',
      lastVisit: p.created_at   ? p.created_at.split('T')[0] : '—',
    }));

    inventory = (data.critical_inventory || []).map(i => ({
      id:          i.id,
      medicineName:i.medicine.name,
      genericName: i.medicine.generic_name || '',
      strength:    i.medicine.strength     || '',
      batch:       i.batch_number,
      qty:         i.quantity_in_stock,
      price:       parseFloat(i.unit_price),
      expiry:      i.expiry_date,
      supplier:    i.supplier,
      minStock:    i.minimum_stock_level,
      received:    i.date_received || '—',
    }));

    dispensingHistory = (data.recent_dispensing || []).map(r => ({
      patientName: r.prescription
        ? `${r.prescription.patient.first_name} ${r.prescription.patient.last_name}`
        : '—',
      medicine: `${r.inventory_item.medicine.name}${r.inventory_item.medicine.strength ? ' '+r.inventory_item.medicine.strength : ''}`,
      qty:  r.quantity_dispensed,
      at:   new Date(r.dispensed_at).toLocaleString(),
      by:   r.pharmacist ? `${r.pharmacist.first_name} ${r.pharmacist.last_name}` : '—',
      notes:r.notes || '',
    }));

    renderPatients(patients);
    renderInventory(inventory);
    renderHistory();
    populateMedicineSelect();

  } catch (e) {
    console.error(e);
    toast('Network error loading dashboard', 'danger');
  }
}

async function loadPrescriptions() {
  try {
    const res  = await fetch('/pharmacy/api/prescriptions/');
    if (!res.ok) return;
    const data = await res.json();
    prescriptions = (data.prescriptions || []).map(p => ({
      id:          p.id,
      patientName: p.patient_name,
      doctor:      p.doctor,
      date:        p.date,
      medicines:   p.medicines,
      status:      p.status,
    }));
    renderPrescriptions(prescriptions);
  } catch (e) { console.error(e); }
}

/* ══════════════════════════════════════
   RENDER HELPERS
══════════════════════════════════════ */
function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

function renderPatients(list) {
  const tbody = document.getElementById('patientsTableBody');
  if (!tbody) return;

  if (!list.length) {
    tbody.innerHTML = `<tr><td colspan="4" class="text-center text-muted py-4" style="font-size:.85rem">No patients found.</td></tr>`;
    return;
  }

  tbody.innerHTML = list.map(p => `
    <tr>
      <td style="font-size:.78rem;font-family:monospace;color:#94a3b8">${p.id}</td>
      <td class="fw-semibold" style="color:#0f3460">${p.name}</td>
      <td class="text-muted d-none d-md-table-cell" style="font-size:.85rem">${p.phone}</td>
      <td>
        <button class="btn btn-sm btn-outline-secondary py-0 px-2" style="border-color:#007B83;color:#007B83"
                onclick="viewPatient('${p.id}')" title="View patient">
          <i class="fas fa-eye" style="font-size:.75rem"></i>
        </button>
      </td>
    </tr>`).join('');
}

function renderInventory(list) {
  const tbody = document.getElementById('inventoryTableBody');
  if (!tbody) return;

  if (!list.length) {
    tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted py-4" style="font-size:.85rem">No inventory items.</td></tr>`;
    return;
  }

  tbody.innerHTML = list.map(item => {
    const status   = stockStatus(item);
    const qtyColor = (item.qty <= item.minStock) ? '#dc2626' : '#16a34a';
    return `
    <tr>
      <td class="fw-semibold" style="color:#0f3460;font-size:.88rem">
        ${item.medicineName}
        ${item.strength ? `<span class="text-muted ms-1" style="font-size:.75rem">${item.strength}</span>` : ''}
      </td>
      <td class="fw-bold" style="color:${qtyColor}">${item.qty}</td>
      <td class="text-muted d-none d-md-table-cell" style="font-size:.8rem">${item.expiry}</td>
      <td>${pillHtml(status)}</td>
      <td style="white-space:nowrap">
        <button class="btn btn-sm py-0 px-2 me-1" style="border:1.5px solid #007B83;color:#007B83;border-radius:7px"
                onclick="viewInventory(${item.id})" title="View details">
          <i class="fas fa-eye" style="font-size:.75rem"></i>
        </button>
        <button class="btn btn-sm py-0 px-2 me-1" style="border:1.5px solid #d97706;color:#d97706;border-radius:7px"
                onclick="openEditStock(${item.id})" title="Update stock">
          <i class="fas fa-edit" style="font-size:.75rem"></i>
        </button>
        <button class="btn btn-sm py-0 px-2" style="border:1.5px solid #059669;color:#059669;border-radius:7px"
                onclick="openDispenseFor(${item.id})" title="Dispense">
          <i class="fas fa-pills" style="font-size:.75rem"></i>
        </button>
      </td>
    </tr>`;
  }).join('');
}

function renderPrescriptions(list) {
  const el = document.getElementById('prescriptionsList');
  if (!el) return;

  if (!list.length) {
    el.innerHTML = `<p class="text-muted text-center py-4" style="font-size:.85rem">No prescriptions found.</p>`;
    return;
  }

  el.innerHTML = list.map(rx => {
    const isPending = rx.status === 'pending';
    const pill = isPending
      ? `<span style="display:inline-flex;align-items:center;padding:.2rem .65rem;border-radius:999px;font-size:.72rem;font-weight:700;background:#fef9c3;color:#854d0e">PENDING</span>`
      : `<span style="display:inline-flex;align-items:center;padding:.2rem .65rem;border-radius:999px;font-size:.72rem;font-weight:700;background:#dcfce7;color:#166534">DISPENSED</span>`;

    return `
    <div class="rx-card">
      <div class="d-flex align-items-start justify-content-between gap-2">
        <div class="flex-grow-1 overflow-hidden">
          <p class="fw-semibold mb-0" style="color:#0f3460;font-size:.9rem">#${rx.id} — ${rx.patientName}</p>
          <p class="text-muted mb-1" style="font-size:.78rem">Dr. ${rx.doctor} &middot; ${rx.date}</p>
          <p class="text-muted mb-0 text-truncate" style="font-size:.8rem">${rx.medicines.join(', ') || '—'}</p>
        </div>
        <div class="d-flex flex-column align-items-end gap-1 flex-shrink-0">
          ${pill}
          ${isPending ? `<button class="btn btn-sm btn-green fw-semibold mt-1 rounded-2"
              style="font-size:.75rem;padding:.25rem .65rem"
              onclick="openDispenseForRx('${rx.id}')">
            <i class="fas fa-pills me-1"></i>Dispense
          </button>` : ''}
        </div>
      </div>
    </div>`;
  }).join('');
}

function renderHistory() {
  const el = document.getElementById('dispensingList');
  if (!el) return;

  if (!dispensingHistory.length) {
    el.innerHTML = `<p class="text-muted text-center py-4" style="font-size:.85rem">No recent dispensing records.</p>`;
    return;
  }

  el.innerHTML = dispensingHistory.map(r => `
    <div class="d-flex align-items-start justify-content-between p-3 mb-2 rounded-3"
         style="border:1px solid #f1f5f9">
      <div>
        <p class="fw-semibold mb-0" style="font-size:.88rem;color:#0f3460">
          ${r.patientName} &mdash; <span class="fw-normal text-muted">${r.medicine}</span>
        </p>
        <p class="text-muted mb-0" style="font-size:.77rem">Qty: ${r.qty} &middot; ${r.by} &middot; ${r.at}</p>
        ${r.notes ? `<p class="text-muted fst-italic mb-0" style="font-size:.75rem">${r.notes}</p>` : ''}
      </div>
      <span style="display:inline-flex;align-items:center;padding:.2rem .65rem;border-radius:999px;font-size:.72rem;font-weight:700;background:#dcfce7;color:#166534;white-space:nowrap">Done</span>
    </div>`).join('');
}

function populateMedicineSelect() {
  const sel = document.getElementById('medicineSelect');
  if (!sel) return;
  const prev = sel.value;
  sel.innerHTML = '<option value="">— choose medicine —</option>';
  inventory.filter(i => i.qty > 0).forEach(i => {
    const opt   = document.createElement('option');
    opt.value   = i.id;
    opt.textContent = `${i.medicineName}${i.strength ? ' '+i.strength : ''} (Stock: ${i.qty})`;
    sel.appendChild(opt);
  });
  if (prev) sel.value = prev;
}

/* ══════════════════════════════════════
   VIEW DETAIL MODALS
══════════════════════════════════════ */
function viewPatient(pid) {
  const p = patients.find(x => x.id === pid);
  if (!p) return;
  const initials = p.name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
  document.getElementById('vp_avatar').textContent  = initials;
  document.getElementById('vp_name').textContent    = p.name;
  document.getElementById('vp_id').textContent      = `ID: ${p.id}`;
  document.getElementById('vp_phone').textContent   = p.phone;
  document.getElementById('vp_email').textContent   = p.email;
  document.getElementById('vp_age').textContent     = p.age !== '—' ? `${p.age} yrs` : '—';
  document.getElementById('vp_reg').textContent     = p.lastVisit;
  document.getElementById('vp_address').textContent = p.address;
  openModal('viewPatientModal');
}

function viewInventory(itemId) {
  const item = inventory.find(x => x.id === itemId);
  if (!item) return;

  const status = stockStatus(item);
  document.getElementById('vi_badge').innerHTML = pillHtml(status);
  document.getElementById('vi_name').textContent    = `${item.medicineName}${item.strength ? ' '+item.strength : ''}`;
  document.getElementById('vi_generic').textContent = item.genericName || '—';
  document.getElementById('vi_batch').textContent   = item.batch;
  document.getElementById('vi_qty').textContent     = item.qty;
  document.getElementById('vi_price').textContent   = `KSh ${item.price.toFixed(2)}`;
  document.getElementById('vi_expiry').textContent  = item.expiry;
  document.getElementById('vi_supplier').textContent= item.supplier;
  document.getElementById('vi_minstock').textContent= item.minStock;
  document.getElementById('vi_received').textContent= item.received;
  document.getElementById('vi_edit_btn').onclick    = () => { closeModal('viewInventoryModal'); openEditStock(itemId); };
  openModal('viewInventoryModal');
}

function openEditStock(itemId) {
  const item = inventory.find(x => x.id === itemId);
  if (!item) return;
  document.getElementById('editStockId').value         = itemId;
  document.getElementById('editStockName').textContent = item.medicineName;
  document.getElementById('editStockQty').value        = item.qty;
  document.getElementById('editStockPrice').value      = item.price.toFixed(2);
  document.getElementById('editStockExpiry').value     = item.expiry;
  document.getElementById('editStockBatch').value      = item.batch;
  openModal('editStockModal');
}

function openDispenseFor(itemId) {
  populateMedicineSelect();
  document.getElementById('medicineSelect').value = itemId;
  openModal('dispensingModal');
}

function openDispenseForRx(rxId) {
  document.getElementById('prescriptionId').value = rxId;
  openModal('dispensingModal');
}

/* ══════════════════════════════════════
   SEARCH
══════════════════════════════════════ */
function searchPatients() {
  const q = document.getElementById('patientSearch').value.toLowerCase();
  renderPatients(patients.filter(p =>
    p.name.toLowerCase().includes(q) || p.id.toLowerCase().includes(q) || p.phone.includes(q)
  ));
}

function searchPrescriptions() {
  const q = document.getElementById('prescriptionSearch').value.toLowerCase();
  renderPrescriptions(prescriptions.filter(rx =>
    rx.patientName.toLowerCase().includes(q) ||
    rx.doctor.toLowerCase().includes(q)      ||
    String(rx.id).includes(q)
  ));
}

function searchInventory() {
  const q = document.getElementById('inventorySearch').value.toLowerCase();
  renderInventory(inventory.filter(i =>
    i.medicineName.toLowerCase().includes(q) ||
    i.batch.toLowerCase().includes(q)        ||
    i.supplier.toLowerCase().includes(q)
  ));
}

/* ══════════════════════════════════════
   FORM SUBMISSIONS
══════════════════════════════════════ */
async function submitMedicine(e) {
  e.preventDefault();
  const fd = new FormData(e.target);
  const payload = {
    medicine_name:       fd.get('medicine_name'),
    generic_name:        fd.get('generic_name') || '',
    manufacturer:        fd.get('manufacturer'),
    batch_number:        fd.get('batch_number'),
    quantity_in_stock:   Number(fd.get('quantity_in_stock')),
    unit_price:          Number(fd.get('unit_price')),
    expiry_date:         fd.get('expiry_date'),
    supplier:            fd.get('supplier'),
    minimum_stock_level: Number(fd.get('minimum_stock_level')),
  };
  try {
    const res  = await fetch('/pharmacy/api/inventory/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (res.ok) {
      toast('Medicine added to inventory!', 'success');
      closeModal('medicineModal');
      e.target.reset();
      await loadDashboard();
    } else {
      toast(data.error || 'Failed to save medicine', 'danger');
    }
  } catch { toast('Network error', 'danger'); }
}

async function submitPatient(e) {
  e.preventDefault();
  const fd = new FormData(e.target);
  const payload = {
    first_name:    fd.get('first_name'),
    last_name:     fd.get('last_name'),
    email:         fd.get('email') || '',
    phone:         fd.get('phone'),
    date_of_birth: fd.get('date_of_birth') || null,
    address:       fd.get('address') || '',
  };
  try {
    const res  = await fetch('/pharmacy/api/patients/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (res.ok) {
      toast('Patient added successfully!', 'success');
      closeModal('patientModal');
      e.target.reset();
      await loadDashboard();
    } else {
      toast(data.error || 'Failed to add patient', 'danger');
    }
  } catch { toast('Network error', 'danger'); }
}

async function submitDispensing(e) {
  e.preventDefault();
  const itemId = document.getElementById('medicineSelect').value;
  if (!itemId) { toast('Please select a medicine', 'danger'); return; }
  const payload = {
    prescription_id:    document.getElementById('prescriptionId').value || null,
    inventory_item_id:  itemId,
    quantity_dispensed: parseInt(document.getElementById('dispenseQuantity').value),
    notes:              document.getElementById('dispensingNotes').value,
  };
  try {
    const res  = await fetch('/pharmacy/api/dispensing/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (res.ok) {
      toast('Medicine dispensed successfully!', 'success');
      closeModal('dispensingModal');
      e.target.reset();
      await loadDashboard();
    } else {
      toast(data.error || 'Failed to dispense', 'danger');
    }
  } catch { toast('Network error', 'danger'); }
}

async function submitEditStock() {
  const id  = document.getElementById('editStockId').value;
  const qty = parseInt(document.getElementById('editStockQty').value);
  if (!id || isNaN(qty)) { toast('Please enter a valid quantity', 'danger'); return; }

  const payload   = { quantity_in_stock: qty };
  const price     = document.getElementById('editStockPrice').value;
  const expiry    = document.getElementById('editStockExpiry').value;
  const batch     = document.getElementById('editStockBatch').value;
  if (price)  payload.unit_price   = parseFloat(price);
  if (expiry) payload.expiry_date  = expiry;
  if (batch)  payload.batch_number = batch;

  try {
    const res  = await fetch(`/pharmacy/api/inventory/${id}/update-stock/`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (res.ok) {
      toast('Stock updated successfully!', 'success');
      closeModal('editStockModal');
      await loadDashboard();
    } else {
      toast(data.error || 'Failed to update stock', 'danger');
    }
  } catch { toast('Network error', 'danger'); }
}

/* Auto-refresh every 5 min */
setInterval(loadDashboard, 300_000);
