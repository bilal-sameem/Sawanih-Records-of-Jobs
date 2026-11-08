// Client-side validation for the "Add New Person" form.
// The server repeats every check, so these are only for fast feedback.
(function () {
  const form = document.getElementById('personForm');
  const summary = document.getElementById('summary');
  const saveBtn = document.getElementById('saveBtn');
  const today = new Date().toISOString().slice(0, 10);
  const edit = form.dataset.mode === 'edit';          // edit => PUT, create => POST
  const previewBox = document.getElementById('preview');
  const originalPreview = previewBox.innerHTML;       // current photo (edit) or placeholder

  const MSG = {
    required: 'دا ډګر اړین دی.',
    id: 'د تذکرې شمېره سمه نه ده (۵ تر ۳۰ توري، شمېرې یا - /).',
    phone: 'د تلیفون شمېره سمه نه ده. بېلګه: 0700123456',
    email: 'بریښنالیک سم نه دی.',
    dob: 'د زېږېدو نېټه سمه نه ده.',
    year: 'د فراغت کال سم نه دی.',
    start: 'د پیل نېټه نشي کولی راتلونکې وي.',
    photoType: 'عکس باید JPG، PNG یا WEBP وي.',
    photoSize: 'د عکس اندازه باید له 2 MB څخه کمه وي.',
    network: 'له سرور سره اړیکه نشته. بیا هڅه وکړئ.',
    server: 'یوه ستونزه رامنځته شوه. بیا هڅه وکړئ.',
    summary: 'مهرباني وکړئ په سور رنګ نښه شوي ډګرونه سم کړئ.'
  };

  // Accept Pashto/Persian digits too: ۰-۹ and ٠-٩ -> 0-9
  const latin = s => s.replace(/[۰-۹]/g, d => d.charCodeAt(0) - 1776)
                      .replace(/[٠-٩]/g, d => d.charCodeAt(0) - 1632);

  const rules = {
    full_name: v => !v.trim() && MSG.required,
    father_name: v => !v.trim() && MSG.required,
    date_of_birth: v => !v ? MSG.required : (v > today || v < '1900-01-01') && MSG.dob,
    id_number: v => !v.trim() ? MSG.required : !/^[0-9A-Za-z\/\-]{5,30}$/.test(latin(v.trim())) && MSG.id,
    phone: v => { if (!v.trim()) return MSG.required;
                  return !/^\+?\d{9,15}$/.test(latin(v).replace(/[\s\-()]/g, '')) && MSG.phone; },
    email: v => v.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.trim()) && MSG.email,
    graduation_year: v => { if (!v) return false; const n = +latin(v);
                            return !(n >= 1950 && n <= new Date().getFullYear() + 6) && MSG.year; },
    start_date: v => v && v > today && MSG.start,
    photo: () => { const f = document.getElementById('photo').files[0];
                   if (!f) return false;
                   if (!/^image\/(jpeg|png|webp)$/.test(f.type)) return MSG.photoType;
                   return f.size > 2 * 1024 * 1024 && MSG.photoSize; }
  };

  const wrap = name => form.querySelector('.field[data-name="' + name + '"]');
  function setError(name, text) {
    const w = wrap(name); if (!w) return;
    w.classList.toggle('invalid', !!text);
    w.querySelector('.err').textContent = text || '';
    const input = w.querySelector('input,textarea');
    if (input) input.setAttribute('aria-invalid', text ? 'true' : 'false');
  }
  function check(name) {
    const el = form.elements[name];
    const msg = rules[name] ? rules[name](el.value || '') : false;
    setError(name, msg || '');
    return !msg;
  }

  // Validate a field when the user leaves it; clear its error while typing.
  Object.keys(rules).forEach(name => {
    const el = form.elements[name];
    el.addEventListener('blur', () => check(name));
    el.addEventListener('input', () => { if (wrap(name).classList.contains('invalid')) check(name); });
  });

  // Photo preview
  document.getElementById('photo').addEventListener('change', e => {
    const box = previewBox; const f = e.target.files[0];
    box.innerHTML = originalPreview;
    if (f && /^image\//.test(f.type)) {
      const img = new Image(); img.alt = '';
      img.src = URL.createObjectURL(f); box.textContent = ''; box.append(img);
    }
    check('photo');
  });

  function showSummary(on) { summary.textContent = on ? MSG.summary : ''; summary.classList.toggle('show', on); }

  form.addEventListener('submit', async e => {
    e.preventDefault();
    const bad = Object.keys(rules).filter(n => !check(n));
    showSummary(bad.length > 0);
    if (bad.length) { form.elements[bad[0]].focus(); return; }

    saveBtn.disabled = true;
    try {
      const headers = { 'X-Requested-With': 'XMLHttpRequest' };
      if (edit) headers['X-CSRFToken'] = form.elements.csrfmiddlewaretoken.value;   // PUT: token goes in the header
      const r = await fetch(form.action, { method: edit ? 'PUT' : 'POST', body: new FormData(form), headers });
      if (r.status === (edit ? 200 : 201)) { window.location.href = form.dataset.redirect; return; }  // toast shows there
      if (r.status === 400) {
        const { errors } = await r.json();
        let first = null;
        Object.entries(errors).forEach(([name, text]) => { setError(name, text); first = first || name; });
        showSummary(true);
        if (first && form.elements[first]) form.elements[first].focus();
      } else { summary.textContent = MSG.server; summary.classList.add('show'); }
    } catch (_) { summary.textContent = MSG.network; summary.classList.add('show'); }
    saveBtn.disabled = false;
  });
})();
