/* Browser adapter only. Authoritative gameplay remains in the original Python. */
"use strict";
const byId = id => document.getElementById(id);
const queue = [];
let latest = null, started = false, ready = false, saved = null;
const saveKey = "pypvz.portrait.save.v1";
const controller = new AbortController();
const signal = controller.signal;
window.pvzStartRequested = false;
const media = matchMedia("(max-width: 900px)");

function enqueue(action, extra = {}) {
  if (!ready && action !== "home") return false;
  queue.push({action, ...extra});
  return true;
}
window.pvzDrain = () => JSON.stringify(queue.splice(0, 50));
window.pvzVisible = () => !document.hidden &&
  !byId("help-dialog").open && !byId("details-dialog").open;
window.pvzLoadSave = () => {
  try {
    saved = localStorage.getItem(saveKey);
    if (saved) localStorage.setItem(saveKey + ".backup", saved);
    return saved;
  } catch { warning("此浏览器无法持久保存进度，请通过“操作 / 存档”导出备份。"); return null; }
};
function warning(message) {
  byId("notice").textContent = message;
  byId("notice").hidden = false;
}
function downloadSave(value) {
  const blob = new Blob([JSON.stringify(value, null, 2)], {type: "application/json"});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = "pypvz-save.json"; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 5000);
}
window.pvzReceive = (kind, encoded) => {
  let data;
  try { data = JSON.parse(encoded); } catch { return; }
  if (kind === "status") byId("boot-status").textContent = data;
  if (kind === "progress") byId("boot-progress").value = data;
  if (kind === "warning") warning(data);
  if (kind === "failure") {
    byId("boot-screen").hidden = false;
    byId("boot-status").textContent = "游戏未能启动。请检查网络后重试；浏览器存档不会被删除。";
    byId("retry-button").hidden = false;
    byId("start-button").hidden = true;
    console.error(data);
    window.pvzError = data;
  }
  if (kind === "ready") {
    ready = true;
    byId("boot-progress").value = 100;
    byId("boot-screen").hidden = true;
    byId("canvas").focus({preventScroll: true});
  }
  if (kind === "save") {
    saved = JSON.stringify(data);
    try { localStorage.setItem(saveKey, saved); }
    catch { warning("本地存储不可用，离开前请导出存档。"); }
  }
  if (kind === "export") downloadSave(data);
  if (kind === "state") {
    latest = data; renderState();
  }
};

let cardSignature = "";
function renderState() {
  if (!latest) return;
  byId("game-title").textContent = latest.title;
  byId("game-ended").hidden = !latest.ended;
  byId("sound-button").textContent = latest.muted ? "声音：关" : "声音：开";
  byId("sound-button").setAttribute("aria-pressed", String(!latest.muted));
  const touch = media.matches && latest.cards.length > 0 && !latest.ended;
  byId("touch-controls").hidden = !touch;
  byId("sun-count").textContent = "阳光 " + latest.sun;
  byId("speed-button").textContent = latest.speed === 2 ? "关闭2倍速" : "开启2倍速";
  byId("speed-button").disabled = !latest.canSpeed;
  const signature = latest.cards.map(c => c.id).join("|");
  if (signature !== cardSignature) {
    cardSignature = signature;
    byId("card-strip").replaceChildren(...latest.cards.map(makeCard));
  }
  latest.cards.forEach(card => {
    const button = byId("card-strip").children[card.index];
    if (!button) return;
    button.dataset.ready = String(card.available);
    button.setAttribute("aria-pressed", String(card.selected));
    button.querySelector(".cooldown").textContent = card.remaining > 0 ? Math.ceil(card.remaining) + "秒" : "";
    button.setAttribute("aria-label", card.name + "，" + card.cost + "阳光" +
      (card.remaining > 0 ? "，冷却中" : ""));
  });
  byId("guide-panel").hidden = !(media.matches && latest.guide);
  if (latest.guide) {
    byId("guide-title").textContent = latest.guide.title;
    byId("guide-text").textContent = latest.guide.text;
    byId("guide-next").hidden = latest.guide.interactive;
  }
  byId("reward-panel").hidden = !(media.matches && latest.reward);
  if (latest.reward) byId("reward-text").textContent =
    latest.reward.names.length ? "获得：" + latest.reward.names.join("、") : "全员集结，准备进入无尽模式！";
}
function showCard(index) {
  const card = latest?.cards[index];
  if (!card) return;
  byId("detail-title").textContent = card.name;
  byId("detail-meta").textContent = card.cost + " 阳光 · 种植冷却 " + card.cooldown + " 秒";
  byId("detail-text").textContent = card.description.join("\n");
  byId("details-dialog").showModal();
}
function makeCard(card) {
  const button = document.createElement("button");
  button.className = "plant-card"; button.type = "button";
  const img = document.createElement("img"); img.src = card.image; img.alt = "";
  const name = document.createElement("span"); name.textContent = card.name;
  const price = document.createElement("span"); price.textContent = card.cost + " 阳光";
  const cooldown = document.createElement("span"); cooldown.className = "cooldown";
  button.append(img, name, price, cooldown);
  let timer, held = false, origin;
  button.addEventListener("pointerdown", event => {
    held = false; origin = [event.clientX, event.clientY];
    timer = setTimeout(() => { held = true; showCard(card.index); }, 500);
  });
  button.addEventListener("pointermove", event => {
    if (origin && Math.hypot(event.clientX - origin[0], event.clientY - origin[1]) > 10) clearTimeout(timer);
  });
  for (const event of ["pointerup", "pointercancel", "pointerleave"])
    button.addEventListener(event, () => clearTimeout(timer));
  button.addEventListener("contextmenu", event => event.preventDefault());
  button.addEventListener("click", () => {
    if (!held) enqueue("card", {index: card.index});
  });
  return button;
}
for (const button of document.querySelectorAll("[data-action]"))
  button.addEventListener("click", () => enqueue(button.dataset.action), {signal});
byId("start-button").addEventListener("click", () => {
  started = true;
  if (window.MM) window.MM.UME = true;
  window.pvzStartRequested = true;
  byId("start-button").textContent = "正在开启，请稍候…";
  // SDL's own user-engagement handler receives this real pointer gesture.
}, {signal});
byId("retry-button").addEventListener("click", () => location.reload(), {signal});
byId("sound-button").addEventListener("click", () => enqueue("mute"), {signal});
byId("help-button").addEventListener("click", () => byId("help-dialog").showModal(), {signal});
byId("fullscreen-button").addEventListener("click", async () => {
  try {
    if (document.fullscreenElement) await document.exitFullscreen();
    else if (byId("game-shell").requestFullscreen) await byId("game-shell").requestFullscreen();
    else warning("此浏览器不支持全屏按钮，可将手机横屏以放大游戏。");
  } catch { warning("浏览器未允许全屏，可将手机横屏游玩。"); }
}, {signal});
byId("import-button").addEventListener("click", () => byId("save-file").click(), {signal});
byId("save-file").addEventListener("change", async event => {
  const file = event.target.files[0]; event.target.value = "";
  if (!file) return;
  if (file.size > 65536) { warning("存档文件过大，请选择导出的 JSON 存档。"); return; }
  try {
    const value = JSON.parse(await file.text());
    if (!value || Array.isArray(value) || typeof value !== "object") throw Error();
    if (confirm("导入会替换当前浏览器的进度并返回主菜单，当前对局不会保留。继续吗？")) {
      enqueue("import", {save: value}); byId("help-dialog").close();
    }
  } catch { warning("不是有效的 JSON 存档，当前存档未修改。"); }
}, {signal});
media.addEventListener("change", renderState, {signal});

// One pointer event -> one original pygame click, even on touch browsers that
// otherwise generate both touch and compatibility mouse events.
const canvas = byId("canvas");
let pointer = null;
canvas.addEventListener("pointerdown", event => {
  if (!ready || (event.button !== 0 && event.button !== 2)) return;
  event.preventDefault(); canvas.focus({preventScroll: true});
  pointer = event.pointerId;
  canvas.setPointerCapture(pointer);
  const rect = canvas.getBoundingClientRect();
  enqueue("pointer", {point: [(event.clientX - rect.left) * 800 / rect.width,
                              (event.clientY - rect.top) * 600 / rect.height],
                       button: event.button === 2 ? 3 : 1});
}, {signal});
canvas.addEventListener("pointerup", event => {
  if (pointer === event.pointerId) {
    if (canvas.hasPointerCapture(pointer)) canvas.releasePointerCapture(pointer);
    pointer = null;
  }
}, {signal});
for (const event of ["mousedown", "mouseup", "touchstart", "touchend", "contextmenu"])
  canvas.addEventListener(event, event => { event.preventDefault(); event.stopImmediatePropagation(); },
    {capture: true, passive: false, signal});
document.addEventListener("keydown", event => {
  if (event.target.closest("dialog, input") || !ready) return;
  if (event.key === "Escape") {
    event.preventDefault(); event.stopImmediatePropagation();
    enqueue(latest?.paused ? "resume" : "cancel");
  }
  if (event.key.toLowerCase() === "f") {
    event.preventDefault(); event.stopImmediatePropagation(); byId("fullscreen-button").click();
  }
}, {capture: true, signal});
// Pygbag runtime calls these hooks. Keep canvas coordinates CSS-managed.
window.custom_onload = async () => {};
window.custom_prerun = () => {};
window.custom_postrun = () => {};
window.__canvas_resized = () => {};

const modelContext = document.modelContext;
if (modelContext?.registerTool) {
  const tools = [{
    name: "read_game_state", title: "读取当前游戏状态",
    description: "Read the real browser game's current scene, cards, sun, guide and rewards.",
    inputSchema: {type: "object", properties: {}, additionalProperties: false},
    annotations: {readOnlyHint: true},
    execute: () => ({ready, state: latest})
  }, {
    name: "select_plant_card", title: "选择植物卡片",
    description: "Select a current card through the same game click as the visible card bar; this does not plant it.",
    inputSchema: {type: "object", properties: {index: {type: "integer", minimum: 0}}, required: ["index"], additionalProperties: false},
    annotations: {readOnlyHint: false},
    execute: async input => {
      if (!input || Object.keys(input).some(key => key !== "index") ||
          !Number.isInteger(input.index) || !latest?.cards[input.index]?.available)
        throw new Error("卡片不存在、阳光不足或仍在冷却。");
      enqueue("card", {index: input.index});
      await new Promise(resolve => setTimeout(resolve, 250));
      return {state: latest};
    }
  }];
  for (const tool of tools) Promise.resolve(modelContext.registerTool(tool, {signal})).catch(console.warn);
}
window.addEventListener("pagehide", event => { if (!event.persisted) controller.abort(); });
