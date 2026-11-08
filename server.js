// npm i express better-sqlite3 jsonwebtoken zod helmet express-rate-limit
// Run: JWT_SECRET=change-me ADMIN_USER=admin ADMIN_PASSWORD=strong-pass node server.js
const fs = require('fs'), path = require('path'), crypto = require('crypto');
const express = require('express'), helmet = require('helmet'), jwt = require('jsonwebtoken');
const rateLimit = require('express-rate-limit'), Database = require('better-sqlite3');
const { z } = require('zod');

const { JWT_SECRET, ADMIN_USER, ADMIN_PASSWORD } = process.env;
if (!JWT_SECRET || !ADMIN_USER || !ADMIN_PASSWORD) {
  console.error('Set JWT_SECRET, ADMIN_USER and ADMIN_PASSWORD'); process.exit(1);
}

const db = new Database(process.env.DB_FILE || 'sawanih.db');
db.pragma('foreign_keys = ON');
db.exec(fs.readFileSync(path.join(__dirname, 'schema.sql'), 'utf8'));

// ---------- validation ----------
const Entry = z.object({
  slug: z.string().regex(/^[a-z0-9-]{1,80}$/),
  title: z.string().min(1).max(200),
  subtitle: z.string().max(300).default(''),
  intro: z.string().max(2000).default(''),
  language: z.string().max(5).default('ps'),
  published: z.boolean().default(false),
  sections: z.array(z.object({ heading: z.string().min(1).max(200), body: z.string().max(20000) })).max(50).default([]),
  timeline: z.array(z.object({ date_label: z.string().min(1).max(60), title: z.string().min(1).max(200), description: z.string().max(2000).default('') })).max(200).default([]),
  quotes: z.array(z.object({ text: z.string().min(1).max(1000), attribution: z.string().max(200).default('') })).max(50).default([])
});

// ---------- auth ----------
const hash = s => crypto.createHash('sha256').update(String(s)).digest();
const same = (a, b) => crypto.timingSafeEqual(hash(a), hash(b));
const isAdmin = req => {
  const t = (req.headers.authorization || '').replace(/^Bearer /, '');
  try { return !!t && jwt.verify(t, JWT_SECRET).role === 'admin'; } catch { return false; }
};
const requireAdmin = (req, res, next) => isAdmin(req) ? next() : res.status(401).json({ error: 'unauthorized' });

// ---------- data access ----------
const children = (t, cols, id) =>
  db.prepare(`SELECT ${cols} FROM ${t} WHERE sawanih_id = ? ORDER BY position`).all(id);

function load(slug, admin) {
  const e = db.prepare('SELECT * FROM sawanih WHERE slug = ?').get(slug);
  if (!e || (!e.published && !admin)) return null;
  return {
    slug: e.slug, title: e.title, subtitle: e.subtitle, intro: e.intro, language: e.language,
    published: !!e.published, created_at: e.created_at, updated_at: e.updated_at,
    sections: children('sawanih_sections', 'heading, body', e.id),
    timeline: children('timeline_events', 'date_label, event_title AS title, event_description AS description', e.id),
    quotes: children('quotes', 'text, attribution', e.id)
  };
}

const save = db.transaction((d, id) => {
  if (id === undefined) {
    id = db.prepare('INSERT INTO sawanih (slug,title,subtitle,intro,language,published) VALUES (?,?,?,?,?,?)')
      .run(d.slug, d.title, d.subtitle, d.intro, d.language, +d.published).lastInsertRowid;
  } else {
    db.prepare("UPDATE sawanih SET title=?,subtitle=?,intro=?,language=?,published=?,updated_at=datetime('now') WHERE id=?")
      .run(d.title, d.subtitle, d.intro, d.language, +d.published, id);
    for (const t of ['sawanih_sections', 'timeline_events', 'quotes'])
      db.prepare(`DELETE FROM ${t} WHERE sawanih_id = ?`).run(id);
  }
  const s = db.prepare('INSERT INTO sawanih_sections (sawanih_id,heading,body,position) VALUES (?,?,?,?)');
  const t = db.prepare('INSERT INTO timeline_events (sawanih_id,date_label,event_title,event_description,position) VALUES (?,?,?,?,?)');
  const q = db.prepare('INSERT INTO quotes (sawanih_id,text,attribution,position) VALUES (?,?,?,?)');
  d.sections.forEach((x, i) => s.run(id, x.heading, x.body, i));
  d.timeline.forEach((x, i) => t.run(id, x.date_label, x.title, x.description, i));
  d.quotes.forEach((x, i) => q.run(id, x.text, x.attribution, i));
});

// ---------- app ----------
const app = express();
app.use(helmet({ contentSecurityPolicy: { directives: {
  defaultSrc: ["'self'"], scriptSrc: ["'self'", "'unsafe-inline'"], styleSrc: ["'self'", "'unsafe-inline'"]
} } }));
app.use(express.json({ limit: '200kb' }));
app.use('/api', rateLimit({ windowMs: 60_000, limit: 120 }));

app.post('/api/auth/login', rateLimit({ windowMs: 15 * 60_000, limit: 5 }), (req, res) => {
  const { username = '', password = '' } = req.body || {};
  if (same(username, ADMIN_USER) && same(password, ADMIN_PASSWORD))
    return res.json({ token: jwt.sign({ role: 'admin' }, JWT_SECRET, { expiresIn: '2h' }) });
  res.status(401).json({ error: 'invalid credentials' });
});

app.get('/api/sawanih', (req, res) => {
  const rows = db.prepare(`SELECT slug,title,subtitle,language,published,updated_at FROM sawanih
    ${isAdmin(req) ? '' : 'WHERE published = 1'} ORDER BY updated_at DESC`).all();
  res.json(rows.map(r => ({ ...r, published: !!r.published })));
});

app.get('/api/sawanih/:slug', (req, res) => {
  const d = load(req.params.slug, isAdmin(req));
  d ? res.json(d) : res.status(404).json({ error: 'not found' });
});

app.post('/api/sawanih', requireAdmin, (req, res) => {
  const p = Entry.safeParse(req.body);
  if (!p.success) return res.status(400).json({ error: p.error.flatten() });
  try { save(p.data); res.status(201).json(load(p.data.slug, true)); }
  catch (e) {
    if (String(e.code).startsWith('SQLITE_CONSTRAINT')) return res.status(409).json({ error: 'slug already exists' });
    console.error(e); res.status(500).json({ error: 'server error' });
  }
});

app.put('/api/sawanih/:slug', requireAdmin, (req, res) => {
  const row = db.prepare('SELECT id FROM sawanih WHERE slug = ?').get(req.params.slug);
  if (!row) return res.status(404).json({ error: 'not found' });
  const p = Entry.omit({ slug: true }).safeParse(req.body);
  if (!p.success) return res.status(400).json({ error: p.error.flatten() });
  save({ ...p.data, slug: req.params.slug }, row.id);
  res.json(load(req.params.slug, true));
});

app.delete('/api/sawanih/:slug', requireAdmin, (req, res) => {
  const r = db.prepare('DELETE FROM sawanih WHERE slug = ?').run(req.params.slug);
  r.changes ? res.status(204).end() : res.status(404).json({ error: 'not found' });
});

// ---------- pages ----------
const page = path.join(__dirname, 'public', 'sawanih.html');
app.get(['/', '/sawanih/:slug'], (_req, res) => res.sendFile(page));
app.use(express.static(path.join(__dirname, 'public')));

app.listen(process.env.PORT || 3000, () => console.log('http://localhost:' + (process.env.PORT || 3000)));
