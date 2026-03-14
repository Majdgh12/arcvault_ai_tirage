const resultsBody = document.getElementById("results-body");
const statusText = document.getElementById("status-text");
const limitSelect = document.getElementById("limit-select");
const refreshButton = document.getElementById("refresh-button");
const summaryCount = document.getElementById("summary-count");
const summaryEscalated = document.getElementById("summary-escalated");
const summaryHigh = document.getElementById("summary-high");
const summaryUpdated = document.getElementById("summary-updated");

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function formatDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}

function confidenceText(value) {
  return `${Math.round(Number(value) * 100)}%`;
}

function priorityBadge(priority) {
  const normalized = String(priority || "").toLowerCase();
  const className =
    normalized === "high" ? "badge-high" : normalized === "medium" ? "badge-medium" : "badge-low";
  return `<span class="badge ${className}">${escapeHtml(priority)}</span>`;
}

function escalationBadge(isEscalated) {
  return isEscalated
    ? '<span class="badge badge-escalated">Escalated</span>'
    : '<span class="badge badge-standard">Standard</span>';
}

function renderIdentifiers(identifiers) {
  if (!identifiers || identifiers.length === 0) {
    return '<span class="tag">None</span>';
  }

  return identifiers
    .map((identifier) => `<span class="tag">${escapeHtml(identifier)}</span>`)
    .join("");
}

function renderTable(records) {
  if (!records || records.length === 0) {
    resultsBody.innerHTML = '<tr><td class="empty-table" colspan="11">No triage records found.</td></tr>';
    return;
  }

  resultsBody.innerHTML = records
    .map(
      (record) => `
        <tr>
          <td class="mono">${escapeHtml(formatDate(record.processed_at))}</td>
          <td>${escapeHtml(record.source || "-")}</td>
          <td><span class="badge badge-category">${escapeHtml(record.category)}</span></td>
          <td>${priorityBadge(record.priority)}</td>
          <td>${escapeHtml(confidenceText(record.confidence))}</td>
          <td>${escapeHtml(record.urgency)}</td>
          <td>${escapeHtml(record.route_to)}</td>
          <td>${escalationBadge(record.escalation_flag)}</td>
          <td><div class="tag-row">${renderIdentifiers(record.identifiers)}</div></td>
          <td>${escapeHtml(record.core_issue)}</td>
          <td>${escapeHtml(record.summary)}</td>
        </tr>
      `,
    )
    .join("");
}

function renderSummary(records) {
  summaryCount.textContent = String(records.length);
  summaryEscalated.textContent = String(records.filter((record) => record.escalation_flag).length);
  summaryHigh.textContent = String(
    records.filter((record) => String(record.priority).toLowerCase() === "high").length,
  );
  summaryUpdated.textContent = records.length > 0 ? formatDate(records[0].processed_at) : "-";
}

async function loadResults() {
  const limit = Number(limitSelect.value);
  statusText.textContent = "Loading saved triage records...";

  try {
    const response = await fetch(`/results?limit=${limit}`);
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Failed to load results.");
    }

    renderSummary(data);
    renderTable(data);
    statusText.textContent = `Showing ${data.length} saved triage records.`;
  } catch (error) {
    renderSummary([]);
    renderTable([]);
    statusText.textContent = error.message;
  }
}

limitSelect.addEventListener("change", loadResults);
refreshButton.addEventListener("click", loadResults);

loadResults();
