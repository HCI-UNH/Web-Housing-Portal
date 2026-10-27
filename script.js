const API_BASE = "http://localhost:8006";

async function apiGet(path, fallback = []) {
  try {
    const resp = await fetch(API_BASE + path);
    if (!resp.ok) throw new Error(resp.status + " " + resp.statusText);
    return await resp.json();
  } catch (e) {
    showError("Could not reach API: " + e.message);
    return fallback;
  }
}

async function apiPost(path, body) {
  try {
    const resp = await fetch(API_BASE + path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    if (!resp.ok) {
      let detail = "";
      try { detail = (await resp.json()).detail; } catch (_) {}
      showError(detail || "Request failed: " + resp.status);
      return false;
    }
    clearError();
    return true;
  } catch (e) {
    showError("Could not reach API: " + e.message);
    return false;
  }
}

function showError(msg) { document.getElementById("error").textContent = msg; }
function clearError() { document.getElementById("error").textContent = ""; }

function el(tag, text) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  return node;
}

async function selectRoomType(roomTypeId) {
  if (await apiPost("/housing/select", { room_type_id: roomTypeId })) {
    renderAll();
  }
}

async function cancelHousing() {
  if (await apiPost("/housing/cancel")) {
    renderAll();
  }
}

async function renderRoomTypes() {
  const container = document.getElementById("room-types");
  const roomTypes = await apiGet("/room-types");
  container.replaceChildren();
  for (const rt of roomTypes) {
    const row = el("div");
    row.className = "row";
    row.appendChild(el("span",
      `${rt.building_name} - ${rt.name} - $${rt.price_per_term}/term - ${rt.spaces_open}/${rt.total_spaces} open`));

    const btn = el("button", "Select");
    btn.onclick = () => selectRoomType(rt.id);
    row.appendChild(btn);

    container.appendChild(row);
  }
}

async function renderMyHousing() {
  const container = document.getElementById("my-housing");
  const mine = await apiGet("/my-housing", null);
  container.replaceChildren();

  if (!mine) {
    container.appendChild(el("div", "You haven't selected housing yet."));
    return;
  }

  container.appendChild(el("div",
    `${mine.building_name} - ${mine.name} - $${mine.price_per_term}/term`));

  const btn = el("button", "Cancel");
  btn.onclick = cancelHousing;
  container.appendChild(btn);
}

async function renderAnnouncements() {
  const container = document.getElementById("announcements");
  const announcements = await apiGet("/announcements");
  container.replaceChildren();

  for (const a of announcements) {
    container.appendChild(el("div", a.title));
    container.appendChild(el("div", a.body));
    container.appendChild(document.createElement("hr"));
  }
}

function renderAll() {
  renderRoomTypes();
  renderMyHousing();
}

renderAll();
renderAnnouncements();
