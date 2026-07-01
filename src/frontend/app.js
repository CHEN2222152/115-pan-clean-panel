const API = "";

async function api(path, method, body) {
  const opts = { method, headers: { "Content-Type": "application/json" } };
  if (body) opts.body = JSON.stringify(body);
  const r = await fetch(API + path, opts);
  return r.json();
}

function showResult(el, type, msg) {
  el.className = "result " + type;
  el.textContent = typeof msg === "string" ? msg : JSON.stringify(msg, null, 2);
  el.style.display = "block";
  setTimeout(() => { el.style.display = "none"; }, 8000);
}

async function loadStatus() {
  const cookieRes = await api("/api/cookies", "GET");
  const statusEl = document.getElementById("cookieStatus");
  const hintEl = document.getElementById("cookieHint");
  if (cookieRes.configured) {
    statusEl.textContent = "🟢 Cookie 已配置";
    statusEl.className = "ok";
    hintEl.style.display = "block";
    document.getElementById("cookieInput").placeholder = "Cookie 已保存，无需重新粘贴（如需更新请粘贴新 Cookie 后点保存）";
  } else {
    statusEl.textContent = "🔴 Cookie 未配置";
    statusEl.className = "";
    hintEl.style.display = "none";
    document.getElementById("cookieInput").placeholder = "UID=xxx; CID=xxx; SEID=xxx";
  }

  const schedRes = await api("/api/schedule", "GET");
  const schedEl = document.getElementById("scheduleStatus");
  if (schedRes.enabled) {
    schedEl.textContent = "🟢 定时任务已启用 (下次执行: " + (schedRes.next_run || "未知") + ")";
    schedEl.className = "ok";
  } else {
    schedEl.textContent = "⏸️ 定时任务未启用";
    schedEl.className = "";
  }
}

async function saveCookies() {
  const raw = document.getElementById("cookieInput").value.trim();
  const resultEl = document.getElementById("verifyResult");
  if (!raw) { showResult(resultEl, "error", "请输入 Cookie 字符串"); return; }

  const cookies = {};
  raw.split(";").forEach(pair => {
    const parts = pair.trim().split("=");
    if (parts.length >= 2) cookies[parts[0].trim()] = parts.slice(1).join("=").trim();
  });

  if (!cookies.UID) { showResult(resultEl, "error", "Cookie 中未找到 UID，请检查格式"); return; }

  const res = await api("/api/cookies", "POST", { cookies });
  if (res.success) {
    showResult(resultEl, "success", "✅ Cookie 已保存（重启容器也不会丢）");
    loadStatus();
    document.getElementById("cookieInput").value = "";
  } else {
    showResult(resultEl, "error", res.error || "保存失败");
  }
}

async function verifyCookies() {
  const resultEl = document.getElementById("verifyResult");
  const res = await api("/api/verify", "POST");
  if (res.success) {
    showResult(resultEl, "success", "✅ Cookie 有效，登录用户: " + res.user);
  } else {
    showResult(resultEl, "error", "❌ " + (res.error || "验证失败"));
  }
}

async function cleanReceived() {
  const resultEl = document.getElementById("cleanResult");
  resultEl.className = "result info";
  resultEl.textContent = "⏳ 正在清理最近接收...";
  resultEl.style.display = "block";
  const res = await api("/api/clean/received", "POST");
  showResult(resultEl, res.success ? "success" : "error", res.success ? "✅ " + res.message : "❌ " + (res.error || "清理失败"));
  loadLogs();
}

async function cleanRecycle() {
  const resultEl = document.getElementById("cleanResult");
  resultEl.className = "result info";
  resultEl.textContent = "⏳ 正在清空回收站...";
  resultEl.style.display = "block";
  const res = await api("/api/clean/recycle", "POST");
  showResult(resultEl, res.success ? "success" : "error", res.success ? "✅ " + res.message : "❌ " + (res.error || "清空失败"));
  loadLogs();
}

async function cleanAll() {
  if (!confirm("确定要一键全部清理吗？将清理所有最近接收文件并清空回收站！")) return;
  const resultEl = document.getElementById("cleanResult");
  resultEl.className = "result info";
  resultEl.textContent = "⏳ 正在执行全部清理...";
  resultEl.style.display = "block";
  const res = await api("/api/clean/all", "POST");
  showResult(resultEl, "success", res.success ? "✅ 清理完成:\n" + res.message : "❌ 清理失败");
  loadLogs();
}

async function enableSchedule() {
  const cron = document.getElementById("cronInput").value.trim();
  const infoEl = document.getElementById("scheduleInfo");
  if (!cron || cron.split(/\s+/).length !== 5) {
    showResult(infoEl, "error", "请输入有效的 5 段 Cron 表达式（如 0 3 * * *）"); return;
  }
  const res = await api("/api/schedule", "POST", { enabled: true, cron });
  showResult(infoEl, "success", "✅ 定时任务已启用\nCron: " + res.cron + "\n下次执行: " + res.next_run);
  loadStatus();
}

async function disableSchedule() {
  const infoEl = document.getElementById("scheduleInfo");
  const res = await api("/api/schedule", "POST", { enabled: false });
  showResult(infoEl, "info", "⏸️ 定时任务已禁用");
  loadStatus();
}

async function loadLogs() {
  const logArea = document.getElementById("logArea");
  logArea.textContent = "⏳ 加载中...";
  const res = await api("/api/logs?n=100", "GET");
  logArea.textContent = res.logs && res.logs.length > 0 ? res.logs.join("\n") : "暂无日志";
}

loadStatus();
loadLogs();
