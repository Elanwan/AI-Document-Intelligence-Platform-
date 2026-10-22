const byId = (id) => document.getElementById(id);
const pct = (value) => `${Math.round(value * 100)}%`;

async function loadHealth() {
  try {
    const health = await fetch('/api/health').then((r) => r.json());
    byId('health').textContent = health.classifier_ready ? 'Service ready' : 'Starting…';
  } catch { byId('health').textContent = 'Service unavailable'; }
}

function showResult(doc) {
  byId('result-section').classList.remove('hidden');
  const badge = byId('result-badge');
  badge.textContent = doc.needs_review ? 'Needs review' : 'Auto accepted';
  badge.className = `badge ${doc.needs_review ? 'review' : ''}`;
  byId('result-metrics').innerHTML = [
    ['Type', doc.document_type.replaceAll('_', ' ')],
    ['Classification', pct(doc.classification_confidence)],
    ['Overall score', pct(doc.overall_confidence)],
  ].map(([name, value]) => `<div class="metric"><span class="muted">${name}</span><strong>${value}</strong></div>`).join('');
  byId('fields').innerHTML = Object.entries(doc.extracted_fields).map(([key, value]) =>
    `<div class="field"><span>${key.replaceAll('_', ' ')}</span><strong>${value}</strong></div>`).join('') || '<p class="muted">No fields extracted.</p>';
  byId('issues').innerHTML = doc.validation_issues.map((issue) =>
    `<div class="issue ${issue.severity}"><strong>${issue.field}</strong><br>${issue.message}</div>`).join('') || '<p class="muted">No validation issues.</p>';
}

async function loadQueue() {
  const docs = await fetch('/api/reviews?status=pending').then((r) => r.json());
  byId('queue').innerHTML = docs.length ? docs.map((doc) => `
    <div class="queue-item">
      <strong>${doc.filename}</strong><span>${doc.document_type.replaceAll('_', ' ')}</span>
      <span>${pct(doc.overall_confidence)}</span><button onclick="approve(${doc.id})">Approve</button>
    </div>`).join('') : '<p class="muted">The review queue is empty.</p>';
}

async function approve(id) {
  await fetch(`/api/reviews/${id}`, { method:'PATCH', headers:{'Content-Type':'application/json'}, body:JSON.stringify({action:'approve'}) });
  await loadQueue();
}

byId('upload-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const button = event.currentTarget.querySelector('button');
  button.disabled = true; byId('upload-message').textContent = 'Processing…';
  try {
    const response = await fetch('/api/documents', { method:'POST', body:new FormData(event.currentTarget) });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Upload failed');
    showResult(data); byId('upload-message').textContent = `Processed ${data.filename}`; await loadQueue();
  } catch (error) { byId('upload-message').textContent = error.message; }
  finally { button.disabled = false; }
});
byId('refresh').addEventListener('click', loadQueue);
loadHealth(); loadQueue();

