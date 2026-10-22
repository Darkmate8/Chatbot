// Cafe Chat page: consent screen, then chat. Nothing is stored in the browser:
// the chat_id lives only in memory, so a reload starts a new anonymous chat.

const CAFES = {
  hashtag: "Hashtag",
  coffee_nation: "Coffee Nation",
  juice_press: "Juice Press",
  barsha: "Barsha",
};

// Fixed greetings from PRODUCT.md. Shown by the page, not stored.
const GREETING_WITH_CAFE = "Hi! I'm an AI, here to hear about your time at {cafe_name}. How has it been?";
const GREETING_NO_CAFE = "Hi! I'm an AI, here to hear about the cafes at FLAME. Which cafe are you at, or thinking about?";

const CONSENT_VERSION = document.body.dataset.consentVersion;
// Keeps clips short and cheap; 60 s of speech is far under the backend's 2 MB cap.
const MAX_RECORD_SECONDS = 60;
// What MediaRecorder can make: webm (Chrome, Firefox), mp4 (Safari), ogg. Must
// match ALLOWED_AUDIO_TYPES in backend/main.py (a test keeps them equal).
const RECORDING_TYPES = ["audio/webm", "audio/mp4", "audio/ogg"];
const param = new URLSearchParams(location.search).get("cafe");
const cafe = param in CAFES ? param : "unknown";
const chatId = randomUUID();
// "voice" once a transcript is in the box (even if the student edits it), back to
// "text" when the box is cleared or sent.
let inputMode = "text";

const $ = (id) => document.getElementById(id);

// crypto.randomUUID only works on https or localhost; fall back for plain-http
// testing on a phone over the local network.
function randomUUID() {
  if (crypto.randomUUID) return crypto.randomUUID();
  const b = crypto.getRandomValues(new Uint8Array(16));
  b[6] = (b[6] & 0x0f) | 0x40;
  b[8] = (b[8] & 0x3f) | 0x80;
  const h = [...b].map((x) => x.toString(16).padStart(2, "0")).join("");
  return `${h.slice(0, 8)}-${h.slice(8, 12)}-${h.slice(12, 16)}-${h.slice(16, 20)}-${h.slice(20)}`;
}

function addBubble(role, text) {
  const el = document.createElement("div");
  el.className = `bubble bubble-${role}`;
  el.textContent = text;
  $("log").appendChild(el);
  el.scrollIntoView({ behavior: "smooth", block: "end" });
  return el;
}

function setBusy(busy) {
  $("message").disabled = busy;
  $("send").disabled = busy;
  $("mic").disabled = busy;
}

async function send(text, mode) {
  addBubble("user", text);
  const typing = addBubble("bot", "");
  typing.classList.add("typing");
  typing.append(...[1, 2, 3].map(() => document.createElement("span")));
  typing.setAttribute("aria-label", "The bot is typing");
  setBusy(true);
  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ chat_id: chatId, cafe, message: text, consent_version: CONSENT_VERSION, input_mode: mode }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const { reply } = await res.json();
    typing.remove();
    addBubble("bot", reply);
  } catch {
    typing.remove();
    addBubble("error", "Sorry, that didn't go through. Your message is back in the box, so you can try again.");
    $("message").value = text;
    inputMode = mode;
  } finally {
    setBusy(false);
    $("message").focus();
  }
}

function startChat() {
  $("consent").hidden = true;
  $("chat").hidden = false;
  const greeting = cafe === "unknown" ? GREETING_NO_CAFE : GREETING_WITH_CAFE.replace("{cafe_name}", CAFES[cafe]);
  addBubble("bot", greeting);
  $("message").focus();
}

$("cafe-line").textContent = cafe === "unknown" ? "All campus cafes" : CAFES[cafe];
$("agree").addEventListener("click", startChat);
$("decline").addEventListener("click", () => {
  $("consent").hidden = true;
  $("declined").hidden = false;
});

$("composer").addEventListener("submit", (e) => {
  e.preventDefault();
  const text = $("message").value.trim();
  if (!text) return;
  const mode = inputMode;
  $("message").value = "";
  inputMode = "text";
  autoGrow();
  send(text, mode);
});

// Enter sends, Shift+Enter makes a new line.
$("message").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
    e.preventDefault();
    $("composer").requestSubmit();
  }
});

function autoGrow() {
  const box = $("message");
  box.style.height = "auto";
  box.style.height = `${Math.min(box.scrollHeight, 140)}px`;
}
$("message").addEventListener("input", () => {
  if (!$("message").value.trim()) inputMode = "text";
  autoGrow();
});

// Voice: tap the mic to record, tap again (or wait 60 s) to stop. The clip is
// sent to /transcribe and the words land in the text box to edit before sending.
// The recording only lives in memory and is dropped once transcribed.
let recorder = null;

function canRecord() {
  return Boolean(navigator.mediaDevices?.getUserMedia && window.MediaRecorder);
}

function setRecording(on) {
  $("mic").classList.toggle("recording", on);
  $("mic").setAttribute("aria-pressed", String(on));
  $("mic").setAttribute("aria-label", on ? "Stop recording" : "Record a voice message");
  $("send").disabled = on;
}

// The voice strip replaces the text box: "recording", "transcribing", or null to hide it.
function showVoice(mode) {
  $("voice").hidden = !mode;
  $("message").hidden = Boolean(mode);
  $("voice").dataset.mode = mode || "";
}

// Live wave drawn from the mic level, so the student can see it is recording and
// hearing them. Runs only in this page; the audio goes nowhere until they stop.
function startWave(audioCtx, stream) {
  const analyser = audioCtx.createAnalyser();
  analyser.fftSize = 512;
  audioCtx.createMediaStreamSource(stream).connect(analyser);
  const samples = new Uint8Array(analyser.fftSize);
  const canvas = $("wave");
  const g = canvas.getContext("2d");
  const color = getComputedStyle(document.body).getPropertyValue("--accent").trim();
  const still = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const started = Date.now();
  let level = 0;
  let phase = 0;
  let frame;

  function draw() {
    const dpr = window.devicePixelRatio || 1;
    const w = canvas.clientWidth;
    const h = canvas.clientHeight;
    if (canvas.width !== Math.round(w * dpr)) {
      canvas.width = Math.round(w * dpr);
      canvas.height = Math.round(h * dpr);
    }
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    g.clearRect(0, 0, w, h);

    analyser.getByteTimeDomainData(samples);
    let sum = 0;
    for (const s of samples) sum += ((s - 128) / 128) ** 2;
    const loudness = Math.min(1, Math.sqrt(sum / samples.length) * 5);
    level += (loudness - level) * 0.25; // smooth, so the wave swells instead of jittering
    if (!still) phase += 0.12;

    // Three overlapping waves; a small minimum keeps them moving in silence.
    const amp = (h / 2 - 2) * Math.max(level, 0.08);
    for (const [cycles, scale, alpha, speed] of [[2, 1, 1, 1], [3, 0.6, 0.5, -1.3], [1.5, 0.4, 0.3, 0.7]]) {
      g.beginPath();
      for (let x = 0; x <= w; x += 2) {
        const taper = Math.sin((Math.PI * x) / w); // ends pinned to the middle line
        const y = h / 2 + Math.sin((x / w) * cycles * 2 * Math.PI + phase * speed) * amp * scale * taper;
        x ? g.lineTo(x, y) : g.moveTo(x, y);
      }
      g.strokeStyle = color;
      g.globalAlpha = alpha;
      g.lineWidth = 2;
      g.stroke();
    }
    g.globalAlpha = 1;

    const secs = Math.floor((Date.now() - started) / 1000);
    $("voice-time").textContent = `${Math.floor(secs / 60)}:${String(secs % 60).padStart(2, "0")}`;
    frame = requestAnimationFrame(draw);
  }

  draw();
  return () => {
    cancelAnimationFrame(frame);
    audioCtx.close();
  };
}

async function startRecording() {
  // Made before the mic prompt: Safari only lets audio start straight from a tap.
  const audioCtx = new AudioContext();
  let stream;
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch {
    audioCtx.close();
    addBubble("error", "The microphone is blocked. You can allow it in your browser settings, or type instead.");
    return;
  }
  audioCtx.resume();
  showVoice("recording");
  const stopWave = startWave(audioCtx, stream);
  const mimeType = RECORDING_TYPES.find((t) => MediaRecorder.isTypeSupported(t));
  recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
  const chunks = [];
  const timer = setTimeout(() => recorder.stop(), MAX_RECORD_SECONDS * 1000);
  recorder.addEventListener("dataavailable", (e) => chunks.push(e.data));
  recorder.addEventListener("stop", () => {
    clearTimeout(timer);
    stopWave();
    stream.getTracks().forEach((t) => t.stop()); // turns the phone's mic light off
    const type = recorder.mimeType;
    recorder = null;
    setRecording(false);
    transcribe(new Blob(chunks, { type }));
  });
  recorder.start();
  setRecording(true);
}

async function transcribe(audio) {
  const box = $("message");
  showVoice("transcribing");
  setBusy(true);
  try {
    if (!audio.size) throw new Error("empty recording");
    const res = await fetch("/transcribe", { method: "POST", headers: { "Content-Type": audio.type }, body: audio });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const { text } = await res.json();
    if (!text) {
      addBubble("error", "I didn't catch any words. Try again, or type instead.");
      return;
    }
    box.value = box.value.trim() ? `${box.value.trim()} ${text}` : text;
    inputMode = "voice";
  } catch {
    addBubble("error", "Sorry, I couldn't hear that. Please try again or type instead.");
  } finally {
    showVoice(null);
    setBusy(false);
    autoGrow();
    box.focus();
  }
}

$("mic").hidden = !canRecord();
$("mic").addEventListener("click", () => (recorder ? recorder.stop() : startRecording()));
