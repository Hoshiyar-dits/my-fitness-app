// Shared helpers for every page: token storage, API calls, navbar, small UI utils.

const TOKEN_KEY = "fitness_token";

function getToken() {
  try { return localStorage.getItem(TOKEN_KEY); } catch { return null; }
}

function setToken(token) {
  try { localStorage.setItem(TOKEN_KEY, token); } catch { /* ignore */ }
}

function logout() {
  try { localStorage.removeItem(TOKEN_KEY); } catch { /* ignore */ }
  window.location.href = "index.html";
}

function requireAuth() {
  if (!getToken()) window.location.href = "index.html";
}

// FastAPI returns { detail: "..." } or, for validation errors, { detail: [{ loc, msg }, ...] }
function errorMessage(body, fallback) {
  if (!body || !body.detail) return fallback;
  if (typeof body.detail === "string") return body.detail;
  if (Array.isArray(body.detail)) {
    return body.detail.map(e => `${(e.loc || []).slice(1).join(".")}: ${e.msg}`).join("; ");
  }
  return fallback;
}

async function api(path, { method = "GET", body } = {}) {
  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(path, { method, headers, body: body !== undefined ? JSON.stringify(body) : undefined });

  if (res.status === 401 && path !== "/login") {
    logout();
    throw new Error("Session expired, please log in again");
  }
  if (res.status === 204) return null;

  let data = null;
  try { data = await res.json(); } catch { /* empty body */ }
  if (!res.ok) {
    const err = new Error(errorMessage(data, `Request failed (${res.status})`));
    err.status = res.status;
    throw err;
  }
  return data;
}

function renderNav(active) {
  const links = [
    ["dashboard.html", "Dashboard"],
    ["log.html", "Log activity"],
    ["chat.html", "AI coach"],
  ];
  document.getElementById("nav").innerHTML = `
    <nav class="navbar navbar-expand-md navbar-dark bg-primary mb-4">
      <div class="container">
        <a class="navbar-brand fw-semibold" href="dashboard.html">FitTrack</a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navMenu">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navMenu">
          <ul class="navbar-nav me-auto">
            ${links.map(([href, label]) => `
              <li class="nav-item"><a class="nav-link ${href === active ? "active" : ""}" href="${href}">${label}</a></li>
            `).join("")}
          </ul>
          <span class="navbar-text text-white me-3" id="navUser"></span>
          <button class="btn btn-outline-light btn-sm" onclick="logout()">Log out</button>
        </div>
      </div>
    </nav>`;
  api("/user/me").then(u => {
    document.getElementById("navUser").textContent = `Hi, ${u.first_name || u.email}`;
  }).catch(() => {});
}

function showAlert(containerId, message, type = "danger") {
  const el = document.getElementById(containerId);
  el.innerHTML = `
    <div class="alert alert-${type} alert-dismissible fade show" role="alert">
      ${escapeHtml(message)}
      <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    </div>`;
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text == null ? "" : String(text);
  return div.innerHTML;
}

// Local date as YYYY-MM-DD (toISOString would use UTC and can be off by a day)
function todayStr() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function formatDay(isoDate, opts = { weekday: "short", month: "short", day: "numeric" }) {
  const [y, m, d] = isoDate.split("-").map(Number);
  return new Date(y, m - 1, d).toLocaleDateString(undefined, opts);
}

// Turn form fields into an object, dropping empty optional fields
function formData(form) {
  const out = {};
  for (const [key, value] of new FormData(form).entries()) {
    if (value === "") continue;
    const input = form.elements[key];
    out[key] = input && input.type === "number" ? Number(value) : value;
  }
  return out;
}
