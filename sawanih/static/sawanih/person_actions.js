// Delete flow shared by the dashboard and the profile page.
// A button with data-delete-url / data-name / data-after opens the confirm dialog, then sends DELETE.
(function () {
  const dlg = document.getElementById('confirmDialog');
  if (!dlg) return;
  const token = document.querySelector('meta[name="csrf-token"]').content;
  const err = dlg.querySelector('[data-err]');
  const confirmBtn = dlg.querySelector('[data-confirm]');
  let current = null;

  document.addEventListener('click', e => {
    const btn = e.target.closest('[data-delete-url]');
    if (!btn) return;
    current = btn;
    dlg.querySelector('[data-name]').textContent = btn.dataset.name;
    err.style.display = 'none';
    dlg.showModal();
  });
  dlg.querySelector('[data-cancel]').addEventListener('click', () => dlg.close());

  confirmBtn.addEventListener('click', async () => {
    confirmBtn.disabled = true;
    try {
      const r = await fetch(current.dataset.deleteUrl, { method: 'DELETE', headers: { 'X-CSRFToken': token } });
      if (r.ok) {                                    // success toast is shown after the reload
        if (current.dataset.after) location.href = current.dataset.after; else location.reload();
        return;
      }
      err.textContent = r.status === 403 ? 'تاسو د ړنګولو اجازه نه لرئ.' : 'یوه ستونزه رامنځته شوه. بیا هڅه وکړئ.';
    } catch (_) {
      err.textContent = 'له سرور سره اړیکه نشته. بیا هڅه وکړئ.';
    }
    err.style.display = 'block';
    confirmBtn.disabled = false;
  });
})();
