const API = window.location.origin;
let token = null;
let sessionId = crypto.randomUUID();

/* ---------- Auth ---------- */
async function authRegister() {
  const userId = document.getElementById("auth-user").value.trim();
  const password = document.getElementById("auth-pass").value;
  const role = document.getElementById("auth-role").value;
  if (!userId || !password) return showAuthError("Fill in all fields.");
  try {
    const res = await fetch(`${API}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, password, role }),
    });
    const data = await res.json();
    if (!res.ok) return showAuthError(data.detail || "Registration failed.");
    token = data.access_token;
    enterChat(userId, data.role);
  } catch (e) {
    showAuthError("Network error.");
  }
}

async function authLogin() {
  const userId = document.getElementById("auth-user").value.trim();
  const password = document.getElementById("auth-pass").value;
  if (!userId || !password) return showAuthError("Fill in all fields.");
  try {
    const res = await fetch(`${API}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, password }),
    });
    const data = await res.json();
    if (!res.ok) return showAuthError(data.detail || "Login failed.");
    token = data.access_token;
    enterChat(userId, data.role);
  } catch (e) {
    showAuthError("Network error.");
  }
}

function skipAuth() {
  enterChat("guest", "student");
}

function logout() {
  token = null;
  document.getElementById("auth-panel").classList.remove("hidden");
  document.getElementById("main").classList.add("hidden");
}

function showAuthError(msg) {
  document.getElementById("auth-error").textContent = msg;
}

function enterChat(userId, role) {
  document.getElementById("auth-panel").classList.add("hidden");
  document.getElementById("main").classList.remove("hidden");
  document.getElementById("user-badge").textContent = `${userId} (${role})`;
  document.getElementById("chat-input").focus();
}

/* ---------- Chat ---------- */
async function sendMessage(event) {
  event.preventDefault();
  const input = document.getElementById("chat-input");
  const text = input.value.trim();
  if (!text) return;
  input.value = "";
  appendMessage("user", text);
  await doChat(text, false);
}

async function sendHintRequest() {
  appendMessage("user", "Can you give me a hint?");
  await doChat("Can you give me a hint?", false);
}

async function sendSolutionRequest() {
  appendMessage("user", "Show me the full solution.");
  await doChat("Show me the full solution.", true);
}

async function doChat(message, allowFullSolution) {
  const courseId = document.getElementById("course-select").value;
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  try {
    const res = await fetch(`${API}/chat`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        session_id: sessionId,
        course_id: courseId,
        message,
        allow_full_solution: allowFullSolution,
      }),
    });
    const data = await res.json();
    if (!res.ok) {
      appendMessage("assistant", `Error: ${data.detail || "Something went wrong."}`);
      return;
    }
    appendMessage("assistant", data.content, data.response_type);
    updateCitations(data.citations);
    updateConfidence(data.confidence);
    updateTrace(data.retrieval_trace);
  } catch (e) {
    appendMessage("assistant", "Network error. Please try again.");
  }
}

function appendMessage(role, text, responseType) {
  const container = document.getElementById("messages");
  const div = document.createElement("div");
  div.className = `message ${role}`;

  let badgeHtml = "";
  if (role === "assistant" && responseType) {
    badgeHtml = `<span class="response-badge ${responseType}">${responseType}</span>`;
  }

  const paragraphs = text.split("\n").filter((l) => l.trim()).map((l) => `<p>${escapeHtml(l)}</p>`).join("");
  div.innerHTML = `<div class="bubble">${badgeHtml}${paragraphs}</div>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function updateCitations(citations) {
  const list = document.getElementById("citations-list");
  if (!citations || citations.length === 0) {
    list.innerHTML = '<p class="empty-state">No citations for this response.</p>';
    return;
  }
  list.innerHTML = citations
    .map(
      (c) => `
    <div class="citation-card">
      <span class="doc">${escapeHtml(c.doc_id)}</span>
      <span class="page">p. ${c.page}</span>
      <div class="snippet">${escapeHtml(c.snippet)}</div>
    </div>`
    )
    .join("");
}

function updateConfidence(conf) {
  const pct = Math.round(conf * 100);
  const fill = document.getElementById("confidence-fill");
  fill.style.width = `${pct}%`;
  if (conf >= 0.7) fill.style.background = "var(--green)";
  else if (conf >= 0.5) fill.style.background = "var(--orange)";
  else fill.style.background = "var(--red)";
  document.getElementById("confidence-value").textContent = `${pct}%`;
}

function updateTrace(trace) {
  if (!trace) return;
  document.getElementById("trace-info").innerHTML = [
    `<strong>Query:</strong> ${escapeHtml(trace.query)}`,
    trace.rewrite ? `<strong>Rewrite:</strong> ${escapeHtml(trace.rewrite)}` : "",
    `<strong>Candidates:</strong> ${trace.candidate_count}`,
    `<strong>Selected:</strong> ${trace.selected_chunk_ids.length}`,
    `<strong>Latency:</strong> ${trace.latency_ms}ms`,
  ]
    .filter(Boolean)
    .join("<br/>");
}

function escapeHtml(str) {
  const d = document.createElement("div");
  d.textContent = str;
  return d.innerHTML;
}
