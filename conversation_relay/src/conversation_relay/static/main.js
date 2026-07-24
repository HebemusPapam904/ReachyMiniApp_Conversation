import { listVoices, getCurrentVoice, applyVoice, describeError } from "./js/api.js";

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function fetchWithTimeout(url, options = {}, timeoutMs = 2000) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } finally {
    clearTimeout(id);
  }
}

async function fetchStatus() {
  const url = new URL("/status", window.location.origin);
  url.searchParams.set("_", Date.now().toString());
  const resp = await fetchWithTimeout(url, {}, 2000);
  if (!resp.ok) return null;
  return await resp.json();
}

function render(st) {
  const modeTitle = document.getElementById("mode-title");
  const chip = document.getElementById("chip");
  const detail = document.getElementById("detail");

  const mode = st.hf_connection_mode === "local" ? "Local endpoint" : "Hugging Face (hosted, free)";
  modeTitle.textContent = mode;

  if (st.backend_connected) {
    chip.textContent = "Connected";
    chip.className = "chip chip-ok";
  } else if (st.backend_connection_state === "waiting_for_config") {
    chip.textContent = "Waiting for config";
    chip.className = "chip";
  } else if (st.backend_connection_state === "connecting") {
    chip.textContent = "Connecting…";
    chip.className = "chip";
  } else {
    chip.textContent = st.backend_connection_state || "Unknown";
    chip.className = "chip";
  }

  if (st.hf_connection_mode === "local") {
    detail.textContent = st.hf_direct_host
      ? `Targeting your own backend at ${st.hf_direct_host}:${st.hf_direct_port}.`
      : "Local mode selected, but no HF_REALTIME_WS_URL is configured yet.";
  } else {
    detail.textContent = "Using the free Hugging Face-hosted realtime backend. No API key required.";
  }

  if (st.backend_error) {
    detail.textContent += ` (${st.backend_error})`;
  }
}

async function poll() {
  const st = await fetchStatus();
  if (!st) return;
  document.getElementById("panel").classList.remove("hidden");
  render(st);
}

async function initVoicePicker() {
  const panel = document.getElementById("voice-panel");
  const select = document.getElementById("voice-select");
  const status = document.getElementById("voice-status");

  try {
    const [voices, current] = await Promise.all([listVoices(), getCurrentVoice()]);
    select.innerHTML = voices.map((v) => `<option value="${v}">${v}</option>`).join("");
    select.value = current.voice;
    panel.classList.remove("hidden");
  } catch (e) {
    // No active conversation session yet (e.g. app not fully started); leave the panel hidden.
    return;
  }

  select.addEventListener("change", async () => {
    status.textContent = "Applying…";
    status.className = "status";
    try {
      await applyVoice(select.value);
      status.textContent = "Voice updated.";
      status.className = "status ok";
    } catch (e) {
      status.textContent = describeError(e);
      status.className = "status error";
    }
  });
}

async function init() {
  const loading = document.getElementById("loading");
  await poll();
  loading.classList.add("hidden");
  setInterval(poll, 2000);
  initVoicePicker();
}

window.addEventListener("DOMContentLoaded", init);
