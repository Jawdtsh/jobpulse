const pty = require("node-pty");
const { exec } = require("child_process");

const term = pty.spawn("powershell.exe", ["-NoLogo"], {
  name: "xterm-256color",
  cols: 120,
  rows: 30,
  cwd: process.cwd(),
  env: process.env
});

// ====== CONFIG ======
const IDLE_TIME = 5000;        // انتهاء الرد
const MAX_PROCESS_TIME = 120000; // تعليق (2 دقيقة)

// ====== STATE ======
let state = "IDLE"; // IDLE | PROCESSING
let lastOutputTime = Date.now();
let processStartTime = null;
let hasUserSentCommand = false; // 🔥 أهم متغير

// ====== SOUND ======
function playSound() {
  exec(
    'powershell -c (New-Object Media.SoundPlayer "C:\\Windows\\Media\\notify.wav").PlaySync();'
  );
}

// ====== OUTPUT ======
term.onData((data) => {
  process.stdout.write(data);

  lastOutputTime = Date.now();

  // 🔥 إذا في output بعد ما المستخدم أرسل أمر → processing
  if (hasUserSentCommand && state === "IDLE") {
    state = "PROCESSING";
    processStartTime = Date.now();
  }
});

// ====== INPUT ======
process.stdin.setRawMode(true);
process.stdin.resume();

process.stdin.on("data", (data) => {
  term.write(data);

  // 🔥 أول ما المستخدم يكتب Enter → اعتبر في طلب
  if (data.toString().includes("\r")) {
    hasUserSentCommand = true;
  }
});

// ====== WATCHER ======
setInterval(() => {
  const now = Date.now();

  // ====== انتهاء طبيعي ======
  if (
    hasUserSentCommand &&
    state === "PROCESSING" &&
    now - lastOutputTime > IDLE_TIME
  ) {
    state = "IDLE";
    hasUserSentCommand = false;

    playSound(); // 🔔 مرة وحدة فقط
  }

  // ====== كشف التعليق ======
  if (
    hasUserSentCommand &&
    state === "PROCESSING" &&
    processStartTime &&
    now - processStartTime > MAX_PROCESS_TIME
  ) {
    state = "IDLE";
    hasUserSentCommand = false;

    console.log("\n⚠️ Possible hang detected\n");
    playSound();
  }
}, 1000);

// ====== START OPCODE ======
setTimeout(() => {
  term.write("opencode\r");
}, 500);