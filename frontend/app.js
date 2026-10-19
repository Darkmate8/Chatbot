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
const param = new URLSearchParams(location.search).get("cafe");
const cafe = param in CAFES ? param : "unknown";
const chatId = randomUUID();

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
}

async function send(text) {
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
      body: JSON.stringify({ chat_id: chatId, cafe, message: text, consent_version: CONSENT_VERSION }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const { reply } = await res.json();
    typing.remove();
    addBubble("bot", reply);
  } catch {
    typing.remove();
    addBubble("error", "Sorry, that didn't go through. Your message is back in the box, so you can try again.");
    $("message").value = text;
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
  $("message").value = "";
  autoGrow();
  send(text);
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
$("message").addEventListener("input", autoGrow);
