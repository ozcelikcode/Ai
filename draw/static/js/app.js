// Araç çubuğu, pan/zoom, çizim, silgi, seçim ve undo/redo içeren tuval mantığı
// Not: Karmaşık yerlerde Türkçe yorum eklenmiştir.

// Lucide init
window.addEventListener('DOMContentLoaded', () => {
  if (window.lucide) lucide.createIcons();
  // Araç çubuğu konumu ölçümüne bağlı sabitleme
  const tools = document.getElementById('tools');
  if (tools) {
    tools.style.opacity = '1';
    tools.style.pointerEvents = 'auto';
  }
  positionOverlays();
  // Kalem kalınlığı butonları
  const penGroup = document.getElementById('penWidthGroup');
  const penPopover = document.getElementById('penWidthPopover');
  const penWrapper = document.getElementById('penWidthWrapper');
  const pencilBtn = document.getElementById('tool-pencil');
  const colorGroup = document.getElementById('penColorGroup');
  if (penGroup) {
    penGroup.addEventListener('click', (e) => {
      const target = e.target.closest('[data-penw]');
      if (!target) return;
      const w = target.getAttribute('data-penw');
      setPenWidth(w);
      // Seçim sonrası popover'ı kapat
      if (penPopover) penPopover.classList.add('hidden');
    });
    // Varsayılan (standart) seçimi uygula
    setPenWidth(3);
  }
  if (colorGroup) {
    colorGroup.addEventListener('click', (e) => {
      const target = e.target.closest('[data-pencolor]');
      if (!target) return;
      const c = target.getAttribute('data-pencolor');
      setPenColor(c);
      if (penPopover) penPopover.classList.add('hidden');
    });
  }
  // Kalem butonu: sağ tık veya çift tık ile popover aç
  function showPenPopover() {
    if (!penPopover) return;
    penPopover.classList.remove('hidden');
  }
  function hidePenPopover() {
    if (!penPopover) return;
    penPopover.classList.add('hidden');
  }
  if (pencilBtn) {
    pencilBtn.addEventListener('contextmenu', (e) => {
      e.preventDefault();
      showPenPopover();
    });
    pencilBtn.addEventListener('dblclick', (e) => {
      e.preventDefault();
      showPenPopover();
    });
  }
  // Dışarı tıklayınca kapat
  document.addEventListener('mousedown', (e) => {
    if (!penWrapper || !penPopover) return;
    if (penPopover.classList.contains('hidden')) return;
    const t = e.target;
    if (t instanceof Element && !penWrapper.contains(t)) {
      hidePenPopover();
    }
  });
  // ESC ile kapat
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') hidePenPopover();
  });
});

const canvas = document.getElementById('board');
const ctx = canvas.getContext('2d', { willReadFrequently: true });
const dpr = Math.max(window.devicePixelRatio || 1, 1);
let isRendering = false;
let needsRender = false;
// Basit canvas sistemi

const state = {
  tool: 'pencil', // sadece pencil ve eraser
  isPointerDown: false,
  pointer: { x: 0, y: 0 },
  // Kalem kalınlığı (px) - Apple Pencil benzeri
  penWidth: 3, // Standart kalınlığı artırdık
  penColor: '#111827',
  // Basit şekil modeli: sadece path'ler
  paths: [],
  history: [],
  future: [],
  // Apple Pencil benzeri çizim durumu
  isDrawing: false,
  currentStroke: [],
  // Gelişmiş stabilizasyon için
  lastVelocity: 0,
  smoothedPoints: [],
  // Basit smoothing için
  smoothnessLevel: 0.2 // Basit ve responsive
};

function resizeCanvas() {
  const rect = canvas.getBoundingClientRect();
  canvas.width = Math.floor(rect.width * dpr);
  canvas.height = Math.floor(rect.height * dpr);
  // Scale'i sadece bir kez, setTransform ile ayarla
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  requestRender();
}
window.addEventListener('resize', resizeCanvas);
window.addEventListener('resize', positionOverlays);

// Artık koordinat dönüştürme gerekmez - direkt canvas koordinatları kullanacağız

function pushHistory() {
  state.history.push(JSON.stringify({ paths: state.paths }));
  if (state.history.length > 200) state.history.shift();
  state.future.length = 0;
}

function undo() {
  if (state.history.length === 0) return;
  const snapshot = state.history.pop();
  state.future.push(JSON.stringify({ paths: state.paths }));
  const prev = JSON.parse(snapshot);
  state.paths = prev.paths || [];
  requestRender();
}

function redo() {
  if (state.future.length === 0) return;
  const snapshot = state.future.pop();
  state.history.push(JSON.stringify({ paths: state.paths }));
  const next = JSON.parse(snapshot);
  state.paths = next.paths || [];
  requestRender();
}

function requestRender() {
  if (isRendering) { needsRender = true; return; }
  isRendering = true; needsRender = false;
  window.requestAnimationFrame(() => {
    render();
    isRendering = false;
    if (needsRender) requestRender();
  });
}

function render() {
  const rect = canvas.getBoundingClientRect();
  
  // Canvas'ı temizle
  ctx.clearRect(0, 0, rect.width, rect.height);

  // 1) TÜM tamamlanmış path'leri çiz (değişmez)
  for (const path of state.paths) {
    if (path && path.points && path.points.length > 0) {
      drawSmoothPath(ctx, path);
    }
  }

  // 2) Canlı çizilen stroke'u ayrı olarak üstte göster
  if (state.isDrawing && state.smoothedPoints && state.smoothedPoints.length > 1) {
    drawCurrentStroke(ctx);
  }
}

// Yumuşak path çizimi - keskinlik önlenir
function drawSmoothPath(ctx, path) {
  if (!path.points || path.points.length === 0) return;
  
  ctx.save();
  ctx.strokeStyle = path.color || '#111827';
  ctx.lineWidth = path.width || 3;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  
  if (path.points.length === 1) {
    // Tek nokta - küçük bir daire çiz
    ctx.beginPath();
    ctx.arc(path.points[0].x, path.points[0].y, (path.width || 3) / 2, 0, Math.PI * 2);
    ctx.fill();
  } else if (path.points.length === 2) {
    // İki nokta - düz çizgi
    ctx.beginPath();
    ctx.moveTo(path.points[0].x, path.points[0].y);
    ctx.lineTo(path.points[1].x, path.points[1].y);
    ctx.stroke();
  } else {
    // Çok noktalı - basit quadratic curves
    ctx.beginPath();
    ctx.moveTo(path.points[0].x, path.points[0].y);
    
    for (let i = 1; i < path.points.length - 1; i++) {
      const current = path.points[i];
      const next = path.points[i + 1];
      const midX = (current.x + next.x) / 2;
      const midY = (current.y + next.y) / 2;
      ctx.quadraticCurveTo(current.x, current.y, midX, midY);
    }
    
    // Son noktaya bağlan
    const lastPoint = path.points[path.points.length - 1];
    ctx.lineTo(lastPoint.x, lastPoint.y);
    ctx.stroke();
  }
  
  ctx.restore();
}

// Canlı çizim için - daha responsif
function drawCurrentStroke(ctx) {
  if (!state.smoothedPoints || state.smoothedPoints.length === 0) return;
  
  ctx.save();
  ctx.strokeStyle = state.penColor;
  ctx.lineWidth = state.penWidth;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  ctx.globalAlpha = 0.9; // Hafif şeffaflık
  
  if (state.smoothedPoints.length === 1) {
    // Tek nokta
    ctx.beginPath();
    ctx.arc(state.smoothedPoints[0].x, state.smoothedPoints[0].y, state.penWidth / 2, 0, Math.PI * 2);
    ctx.fill();
  } else if (state.smoothedPoints.length === 2) {
    // İki nokta
    ctx.beginPath();
    ctx.moveTo(state.smoothedPoints[0].x, state.smoothedPoints[0].y);
    ctx.lineTo(state.smoothedPoints[1].x, state.smoothedPoints[1].y);
    ctx.stroke();
  } else {
    // Yumuşak canlı çizgi - basit quadratic
    ctx.beginPath();
    ctx.moveTo(state.smoothedPoints[0].x, state.smoothedPoints[0].y);
    
    for (let i = 1; i < state.smoothedPoints.length - 1; i++) {
      const current = state.smoothedPoints[i];
      const next = state.smoothedPoints[i + 1];
      const midX = (current.x + next.x) / 2;
      const midY = (current.y + next.y) / 2;
      ctx.quadraticCurveTo(current.x, current.y, midX, midY);
    }
    
    // Son noktaya bağlan
    const lastPoint = state.smoothedPoints[state.smoothedPoints.length - 1];
    ctx.lineTo(lastPoint.x, lastPoint.y);
    ctx.stroke();
  }
  
  ctx.restore();
}

// Layer sistemini kaldırdık - direkt render ediyoruz

function setTool(tool) {
  state.tool = tool;
  document.querySelectorAll('.tool').forEach(b => b.classList.remove('bg-indigo-100', 'text-indigo-700'));
  const btn = document.querySelector(`[data-tool="${tool}"]`);
  if (btn) btn.classList.add('bg-indigo-100','text-indigo-700');
  updateCursor();
}

// Basit çizim başlatma
function startDrawing(canvasX, canvasY) {
  state.isDrawing = true;
  state.currentStroke = [{ x: canvasX, y: canvasY, timestamp: Date.now() }];
  state.smoothedPoints = [{ x: canvasX, y: canvasY }];
  state.lastVelocity = 0;
}

function addDrawingPoint(canvasX, canvasY) {
  if (!state.isDrawing) return;
  
  const now = Date.now();
  const lastPoint = state.currentStroke[state.currentStroke.length - 1];
  
  // BASİT APPROACH: Sadece temel kontroller
  const dx = canvasX - lastPoint.x;
  const dy = canvasY - lastPoint.y;
  const distance = Math.sqrt(dx * dx + dy * dy);
  
  // Minimum mesafe kontrolü - çok yakın noktaları atla
  if (distance < 1.5) return;
  
  // Maksimum mesafe kontrolü - çok büyük atlamaları önle
  if (distance > 50) return; // Çok büyük atlamaları tamamen reddet
  
  // Hız hesaplama - basit
  const timeDelta = Math.max(now - lastPoint.timestamp, 1);
  const velocity = distance / timeDelta;
  state.lastVelocity = velocity;
  
  // SADECE GEREKLİ NOKTALARI EKLE - manipülasyon yok
  const newPoint = { x: canvasX, y: canvasY, timestamp: now, velocity: velocity };
  state.currentStroke.push(newPoint);
  
  // Basit smoothing güncelleme
  addToSmoothedPoints(canvasX, canvasY);
}

// Optimized smoothing - keskinliği önler ama kendi kendine çizim yapmaz
function addToSmoothedPoints(x, y) {
  // İlk nokta
  if (state.smoothedPoints.length === 0) {
    state.smoothedPoints.push({ x, y });
    return;
  }
  
  const lastSmoothed = state.smoothedPoints[state.smoothedPoints.length - 1];
  
  // DENGELI SMOOTHING - keskinlik önlenir ama responsive kalır
  let smoothingFactor = 0.4; // Biraz daha fazla smoothing
  
  // Hızlı hareket durumunda daha az smoothing (mouse sync için)
  const distance = Math.sqrt((x - lastSmoothed.x) ** 2 + (y - lastSmoothed.y) ** 2);
  if (distance > 20) {
    smoothingFactor = 0.2; // Hızlı hareket = az smoothing
  }
  
  const smoothedX = lastSmoothed.x + (x - lastSmoothed.x) * (1 - smoothingFactor);
  const smoothedY = lastSmoothed.y + (y - lastSmoothed.y) * (1 - smoothingFactor);
  
  state.smoothedPoints.push({ x: smoothedX, y: smoothedY });
}

// KARMAŞIK STABİLİZASYON SİSTEMİ KALDIRILDI
// Kendi kendine çizim sorununa neden oluyordu

// KARMAŞIK STABİLİZASYON FONKSİYONLARI KALDIRILDI

// TÜM KARMAŞIK HAREKET TESPİT VE STABİLİZASYON FONKSİYONLARI KALDIRILDI

// KALAN KARMAŞIK FONKSİYONLAR DA KALDIRILDI


function finishDrawing() {
  if (!state.isDrawing || state.smoothedPoints.length < 2) {
    // Çizim geçersizse tüm temp datayı temizle
    state.isDrawing = false;
    state.currentStroke = [];
    state.smoothedPoints = [];
    return;
  }
  
  // Stroke'u kaydet - smoothed points'in kopyasını kullan
  const newPath = {
    id: 'path-' + Date.now() + '-' + Math.random().toString(36).slice(2,5),
    points: [...state.smoothedPoints], // Array'in kopyasını al
    color: state.penColor,
    width: state.penWidth
  };
  
  // Path'i kaydet
  state.paths.push(newPath);
  
  // Canlı çizim durumunu tamamen temizle
  state.isDrawing = false;
  state.currentStroke = [];
  state.smoothedPoints = [];
}

// Bezier curve smoothing - Apple Pencil benzeri
function applyCurveSmoothing(points) {
  if (points.length < 3) return points;
  
  const smoothed = [];
  smoothed.push(points[0]); // İlk nokta
  
  for (let i = 1; i < points.length - 1; i++) {
    const prev = points[i - 1];
    const current = points[i];
    const next = points[i + 1];
    
    // Catmull-Rom spline benzeri yumuşatma
    const smoothX = (prev.x + 2 * current.x + next.x) / 4;
    const smoothY = (prev.y + 2 * current.y + next.y) / 4;
    
    smoothed.push({ x: smoothX, y: smoothY });
  }
  
  smoothed.push(points[points.length - 1]); // Son nokta
  return smoothed;
}

function hitTestPointOnPath(canvasX, canvasY, path) {
  const tolerance = Math.max(8, (path.width || state.penWidth || 2) * 1.5);
  for (let i = 1; i < path.points.length; i++) {
    const a = path.points[i-1]; 
    const b = path.points[i];
    const dist = pointSegmentDistance({x: canvasX, y: canvasY}, a, b);
    if (dist <= tolerance) return true;
  }
  return false;
}

function pointSegmentDistance(p, a, b) {
  const abx = b.x - a.x; const aby = b.y - a.y;
  const apx = p.x - a.x; const apy = p.y - a.y;
  const ab2 = abx*abx + aby*aby;
  let t = ab2 ? (apx*abx + apy*aby)/ab2 : 0;
  t = Math.max(0, Math.min(1, t));
  const cx = a.x + t*abx; const cy = a.y + t*aby;
  const dx = p.x - cx; const dy = p.y - cy;
  return Math.hypot(dx, dy);
}

function onPointerDown(e) {
  const rect = canvas.getBoundingClientRect();
  state.pointer.x = e.clientX - rect.left; 
  state.pointer.y = e.clientY - rect.top;
  state.isPointerDown = true;

  if (state.tool === 'pencil') {
    pushHistory();
    startDrawing(state.pointer.x, state.pointer.y);
    requestRender();
  } else if (state.tool === 'eraser') {
    pushHistory();
    const before = state.paths.length;
    state.paths = state.paths.filter(p => !hitTestPointOnPath(state.pointer.x, state.pointer.y, p));
    const after = state.paths.length;
    if (before !== after) requestRender();
  }
}

function onPointerMove(e) {
  const rect = canvas.getBoundingClientRect();
  state.pointer.x = e.clientX - rect.left; 
  state.pointer.y = e.clientY - rect.top;

  if (!state.isPointerDown) return;

  if (state.tool === 'pencil') {
    addDrawingPoint(state.pointer.x, state.pointer.y);
    requestRender();
    scheduleAutosave();
  } else if (state.tool === 'eraser') {
    // sürükleyerek silme
    const before = state.paths.length;
    state.paths = state.paths.filter(p => !hitTestPointOnPath(state.pointer.x, state.pointer.y, p));
    const after = state.paths.length;
    if (before !== after) {
      requestRender();
      scheduleAutosave();
    }
  }
}

function onPointerUp() {
  state.isPointerDown = false;
  
  // Çizim bittiğinde stroke'u tamamla
  if (state.tool === 'pencil') {
    finishDrawing();
    requestRender();
  }
}

// Zoom işlemleri devre dışı bırakıldı

// Keyboard shortcuts (basitleştirildi)
window.addEventListener('keydown', (e) => {
  if (e.key.toLowerCase() === 'p') { setTool('pencil'); }
  if (e.key.toLowerCase() === 'e') { setTool('eraser'); }
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z') { e.preventDefault(); undo(); }
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'y') { e.preventDefault(); redo(); }
});

// UI wiring (basitleştirildi)
document.getElementById('tool-pencil')?.addEventListener('click', () => setTool('pencil'));
document.getElementById('tool-eraser')?.addEventListener('click', () => setTool('eraser'));
document.getElementById('undo')?.addEventListener('click', undo);
document.getElementById('redo')?.addEventListener('click', redo);
document.getElementById('btnMenu')?.addEventListener('click', () => {
  const el = document.getElementById('sideMenu');
  if (el) el.classList.toggle('hidden');
});

// Menu actions
document.getElementById('menuNew')?.addEventListener('click', (e) => {
  e.preventDefault();
  if (state.paths.length > 0) {
    document.getElementById('confirmNewModal')?.classList.remove('hidden');
  } else {
    state.paths = []; state.history = []; state.future = []; state.selection.clear(); render();
  }
});
document.getElementById('confirmNewCancel')?.addEventListener('click', () => {
  document.getElementById('confirmNewModal')?.classList.add('hidden');
});
document.getElementById('confirmNewOk')?.addEventListener('click', () => {
  document.getElementById('confirmNewModal')?.classList.add('hidden');
  state.paths = []; state.history = []; state.future = []; state.selection.clear(); render();
});

document.getElementById('menuSaveImage')?.addEventListener('click', async (e) => {
  e.preventDefault();
  const dataUrl = exportCanvasToImage();
  const a = document.createElement('a');
  a.href = dataUrl; a.download = `sketch-${Date.now()}.png`;
  document.body.appendChild(a); a.click(); a.remove();
});

document.getElementById('menuSave')?.addEventListener('click', async (e) => {
  e.preventDefault();
  try {
    const payload = { data: { paths: state.paths, view: state.view }, preview: exportCanvasToImage() };
    const res = await fetch('/api/save', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    if (!res.ok) {
      if (res.status === 401) { window.location.href = '/login'; return; }
      throw new Error('Save failed');
    }
    const j = await res.json();
    const input = document.getElementById('saveLinkInput');
    if (input) input.value = j.url;
    document.getElementById('saveLinkModal')?.classList.remove('hidden');
    document.getElementById('btnCopyLink')?.addEventListener('click', () => {
      if (input) { input.select(); document.execCommand('copy'); }
    }, { once: true });
    document.getElementById('btnCloseSaveLink')?.addEventListener('click', () => {
      document.getElementById('saveLinkModal')?.classList.add('hidden');
    }, { once: true });
  } catch (err) {
    console.error(err);
    alert('Save failed');
  }
});

// Pointer events
canvas.addEventListener('pointerdown', onPointerDown);
window.addEventListener('pointermove', onPointerMove);
window.addEventListener('pointerup', onPointerUp);
// Wheel eventi devre dışı - zoom yok

// Init
function init() {
  resizeCanvas();
  setTool('pencil');
  // Board data ön-yükleme: backend'den veya storage'dan
  tryLoadBoardFromBootstrapOrStorage();
}
init();

// Pan sistemi kaldırıldı

// Üst başlık ve araç çubuğu boyuna göre dinamik yerleşim
function positionOverlays() {
  const header = document.querySelector('header');
  const tools = document.getElementById('tools');
  const boardWrapper = document.getElementById('boardWrapper');
  const headerBottom = header ? header.getBoundingClientRect().bottom : 72;
  const toolsTop = Math.max(96, headerBottom + 12);
  if (tools) tools.style.top = toolsTop + 'px';
  // Tuval artık full-screen; üstte boşluk bırakmıyoruz
  if (boardWrapper) boardWrapper.style.inset = '0 0 0 0';
}

// İmleç yönetimi (basitleştirildi)
function updateCursor() {
  if (state.tool === 'pencil') {
    const ring = createRingCursor(state.penWidth * 2, state.penColor || '#6366f1');
    canvas.style.cursor = ring;
    return;
  }
  if (state.tool === 'eraser') {
    const ring = createRingCursor(14, '#ef4444');
    canvas.style.cursor = ring;
    return;
  }
  canvas.style.cursor = 'default';
}

function createRingCursor(size, color) {
  // Ensure OS cursor constraints by embedding the dot in a larger canvas
  const s = Math.max(1, Math.round(size));
  const canvasSize = Math.max(32, s + 6);
  const cx = Math.floor(canvasSize / 2);
  const cy = Math.floor(canvasSize / 2);
  let svg;
  if (s <= 4) {
    // For very thin strokes, use a filled dot so it remains visible
    const r = s / 2;
    svg = `<svg xmlns='http://www.w3.org/2000/svg' width='${canvasSize}' height='${canvasSize}' viewBox='0 0 ${canvasSize} ${canvasSize}'>
<circle cx='${cx}' cy='${cy}' r='${r}' fill='${color}' />
</svg>`;
  } else {
    const stroke = Math.max(2, Math.round(s * 0.18));
    const r = Math.max(0.5, s / 2 - stroke / 2);
    svg = `<svg xmlns='http://www.w3.org/2000/svg' width='${canvasSize}' height='${canvasSize}' viewBox='0 0 ${canvasSize} ${canvasSize}'>
<circle cx='${cx}' cy='${cy}' r='${r}' fill='none' stroke='${color}' stroke-width='${stroke}' />
</svg>`;
  }
  const encoded = (typeof window !== 'undefined' && window.btoa) ? window.btoa(svg) : btoa(svg);
  const url = `url("data:image/svg+xml;base64,${encoded}") ${cx} ${cy}, auto`;
  return url;
}

// Kalem kalınlığı ayarı ve UI güncellemesi
function setPenWidth(value) {
  const newWidth = Number(value) || 2;
  state.penWidth = newWidth;
  // UI'da seçili durumu güncelle
  const buttons = document.querySelectorAll('#penWidthGroup [data-penw]');
  buttons.forEach((btn) => {
    btn.classList.remove('bg-indigo-100', 'text-indigo-700');
  });
  const active = document.querySelector(`#penWidthGroup [data-penw="${newWidth}"]`);
  if (active) active.classList.add('bg-indigo-100', 'text-indigo-700');
  if (state.tool === 'pencil') updateCursor();
}

function setPenColor(color) {
  state.penColor = color || '#111827';
  // UI highlight for selected color
  const buttons = document.querySelectorAll('#penColorGroup [data-pencolor]');
  buttons.forEach((btn) => btn.classList.remove('ring-indigo-400'));
  const active = document.querySelector(`#penColorGroup [data-pencolor="${state.penColor}"]`);
  if (active) active.classList.add('ring-indigo-400');
  if (state.tool === 'pencil') updateCursor();
}

// Basit yumuşatma (EMA)
function smoothPoints(points, alpha = 0.45) {
  if (!points || points.length < 3) return points;
  const out = [{ x: points[0].x, y: points[0].y }];
  for (let i = 1; i < points.length; i++) {
    const prev = out[i - 1];
    const p = points[i];
    out.push({
      x: prev.x * (1 - alpha) + p.x * alpha,
      y: prev.y * (1 - alpha) + p.y * alpha,
    });
  }
  return out;
}

// --- Selection overlay rendering & hit testing ---
function drawSelectionOverlay(ctx) {
  const bounds = getSelectionBounds();
  if (!bounds) return;
  const pad = 6 / state.view.scale;
  const x = bounds.minX - pad;
  const y = bounds.minY - pad;
  const w = (bounds.maxX - bounds.minX) + pad * 2;
  const h = (bounds.maxY - bounds.minY) + pad * 2;

  ctx.save();
  ctx.strokeStyle = 'rgba(99,102,241,0.7)';
  // Sabit ekran kalınlığı: 1.5px
  ctx.lineWidth = 1.5 / state.view.scale;
  // Sabit ekran tire aralıkları
  ctx.setLineDash([6 / state.view.scale, 4 / state.view.scale]);
  ctx.strokeRect(x, y, w, h);
  ctx.setLineDash([]);

  // Handles (corner squares ~10px screen)
  const hs = 10 / state.view.scale;
  const handles = [
    { key: 'tl', cx: x, cy: y },
    { key: 'tr', cx: x + w, cy: y },
    { key: 'bl', cx: x, cy: y + h },
    { key: 'br', cx: x + w, cy: y + h },
  ];
  ctx.fillStyle = '#ffffff';
  ctx.strokeStyle = '#6366f1';
  ctx.lineWidth = 1.5 / state.view.scale;
  for (const hnd of handles) {
    ctx.fillRect(hnd.cx - hs/2, hnd.cy - hs/2, hs, hs);
    ctx.strokeRect(hnd.cx - hs/2, hnd.cy - hs/2, hs, hs);
  }

  // Delete icon (red circle with X) near top-right
  const delSize = 14 / state.view.scale;
  const delCx = x + w + delSize; // a bit outside
  const delCy = y - delSize;
  ctx.beginPath();
  ctx.fillStyle = '#ef4444';
  ctx.strokeStyle = '#b91c1c';
  ctx.lineWidth = 1.5 / state.view.scale;
  ctx.arc(delCx, delCy, delSize/2, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();
  ctx.beginPath();
  ctx.strokeStyle = '#ffffff';
  ctx.lineWidth = 2 / state.view.scale;
  ctx.moveTo(delCx - delSize*0.2, delCy - delSize*0.2);
  ctx.lineTo(delCx + delSize*0.2, delCy + delSize*0.2);
  ctx.moveTo(delCx + delSize*0.2, delCy - delSize*0.2);
  ctx.lineTo(delCx - delSize*0.2, delCy + delSize*0.2);
  ctx.stroke();
  ctx.restore();
}

function exportCanvasToImage() {
  const rect = canvas.getBoundingClientRect();
  const out = document.createElement('canvas');
  out.width = Math.floor(rect.width * dpr);
  out.height = Math.floor(rect.height * dpr);
  const octx = out.getContext('2d');
  octx.scale(dpr, dpr);
  octx.fillStyle = '#ffffff';
  octx.fillRect(0, 0, rect.width, rect.height);
  for (const p of state.paths) drawSimplePath(octx, p);
  return out.toDataURL('image/png');
}

// Selection sistemini kaldırdık

// Dinamik kalem kalınlığı: hız ve uzun basma etkisi
function computeDynamicWidth(nowMs, screenX, screenY) {
  const base = state.penWidth || 2;
  // Ekran pikselinde hareket hızı (px/ms)
  let speed = 0;
  if (state.lastPointerTimeMs) {
    const dt = Math.max(1, nowMs - state.lastPointerTimeMs);
    const dx = screenX - state.lastPointerScreen.x;
    const dy = screenY - state.lastPointerScreen.y;
    speed = Math.hypot(dx, dy) / dt; // px per ms
  }
  state.lastPointerTimeMs = nowMs;
  state.lastPointerScreen = { x: screenX, y: screenY };
  // Hız düşükse kalın, hızlıysa tabana geri dön (ince değil, normal):
  // speed ~0 -> ~1.5, orta -> ~1.0, yüksek -> ~0.95 (ani incelme yok)
  const factorSpeed = 0.95 + 0.55 * Math.exp(-speed * 0.04);
  // Uzun basma (0..1) -> ekstra kalınlık
  const factorHold = 1 + 1.0 * state.longPressBoost;
  // Tavanı sınırlı (abartı yok): tabanın 2.2x'ine kadar
  const width = Math.max(1, Math.min(base * 2.2, base * factorSpeed * factorHold));
  return width;
}

// Kalınlık yumuşatma: ani hızlanmalarda keskin farkı eritmek için düşük-geçiren filtre
function smoothWidth(targetW) {
  const alphaGrow = 0.35;  // kalınlaşırken daha hızlı yaklaş
  const alphaShrink = 0.18; // incelirken daha yavaş in (keskin fark olmasın)
  const prev = state.prevSmoothedW || targetW;
  const alpha = targetW > prev ? alphaGrow : alphaShrink;
  const smoothed = prev * (1 - alpha) + targetW * alpha;
  state.prevSmoothedW = smoothed;
  return smoothed;
}

// Apple Pencil benzeri yumuşak çizim fonksiyonu
function drawSimplePath(ctx, path) {
  if (!path.points || path.points.length < 2) return;
  
  ctx.strokeStyle = path.color || '#111827';
  ctx.lineWidth = path.width || 3;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  
  drawSmoothCurve(ctx, path.points);
}

// Canlı çizilen stroke'u gerçek zamanlı yumuşak göster
function drawCurrentStroke(ctx) {
  if (state.smoothedPoints.length < 2) return;
  
  ctx.strokeStyle = state.penColor;
  ctx.lineWidth = state.penWidth;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  
  // Canlı çizim için daha responsive smoothing
  drawRealTimeSmooth(ctx, state.smoothedPoints);
}

// Ultra yumuşak gerçek zamanlı çizim
function drawRealTimeSmooth(ctx, points) {
  if (points.length < 2) return;
  
  ctx.beginPath();
  ctx.moveTo(points[0].x, points[0].y);
  
  if (points.length === 2) {
    ctx.lineTo(points[1].x, points[1].y);
  } else {
    // Catmull-Rom spline benzeri ultra yumuşak çizim
    drawUltraSmoothPath(ctx, points);
  }
  
  ctx.stroke();
}

// Ultra yumuşak path çizimi - köşeleri tamamen ortadan kaldırır
function drawUltraSmoothPath(ctx, points) {
  if (points.length < 3) return;
  
  // İlk noktadan başla
  let prevPoint = points[0];
  ctx.moveTo(prevPoint.x, prevPoint.y);
  
  // Her 3 nokta için cubic bezier curve kullan
  for (let i = 1; i < points.length - 2; i++) {
    const currentPoint = points[i];
    const nextPoint = points[i + 1];
    
    // Control points - kontrollü tension ile sapma önleme
    const baseTension = 0.25; // Tension azaltıldı
    const maxControlDistance = 25; // Control point'lerin maksimum uzaklığı
    
    let controlPoint1X, controlPoint1Y;
    let controlPoint2X, controlPoint2Y;
    
    if (i > 1) {
      const prevPrevPoint = points[i - 1];
      const deltaX = (currentPoint.x - prevPrevPoint.x) * baseTension;
      const deltaY = (currentPoint.y - prevPrevPoint.y) * baseTension;
      
      // Control point uzaklığını sınırla
      const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
      if (distance > maxControlDistance) {
        const scale = maxControlDistance / distance;
        controlPoint1X = prevPoint.x + deltaX * scale;
        controlPoint1Y = prevPoint.y + deltaY * scale;
      } else {
        controlPoint1X = prevPoint.x + deltaX;
        controlPoint1Y = prevPoint.y + deltaY;
      }
    } else {
      const deltaX = (currentPoint.x - prevPoint.x) * baseTension;
      const deltaY = (currentPoint.y - prevPoint.y) * baseTension;
      controlPoint1X = prevPoint.x + deltaX;
      controlPoint1Y = prevPoint.y + deltaY;
    }
    
    if (i < points.length - 2) {
      const nextNextPoint = points[i + 2];
      const deltaX = (nextNextPoint.x - prevPoint.x) * baseTension;
      const deltaY = (nextNextPoint.y - prevPoint.y) * baseTension;
      
      // Control point uzaklığını sınırla
      const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
      if (distance > maxControlDistance) {
        const scale = maxControlDistance / distance;
        controlPoint2X = currentPoint.x - deltaX * scale;
        controlPoint2Y = currentPoint.y - deltaY * scale;
      } else {
        controlPoint2X = currentPoint.x - deltaX;
        controlPoint2Y = currentPoint.y - deltaY;
      }
    } else {
      const deltaX = (currentPoint.x - prevPoint.x) * baseTension;
      const deltaY = (currentPoint.y - prevPoint.y) * baseTension;
      controlPoint2X = currentPoint.x - deltaX;
      controlPoint2Y = currentPoint.y - deltaY;
    }
    
    // Cubic bezier curve çiz
    ctx.bezierCurveTo(
      controlPoint1X, controlPoint1Y,
      controlPoint2X, controlPoint2Y,
      currentPoint.x, currentPoint.y
    );
    
    prevPoint = currentPoint;
  }
  
  // Son noktaya yumuşak geçiş
  const lastPoint = points[points.length - 1];
  const secondLastPoint = points[points.length - 2];
  
  ctx.quadraticCurveTo(
    secondLastPoint.x + (lastPoint.x - secondLastPoint.x) * 0.3,
    secondLastPoint.y + (lastPoint.y - secondLastPoint.y) * 0.3,
    lastPoint.x,
    lastPoint.y
  );
}

// Final path için ultra yumuşak çizim
function drawSmoothCurve(ctx, points) {
  if (points.length < 2) return;
  
  ctx.beginPath();
  
  if (points.length === 2) {
    ctx.moveTo(points[0].x, points[0].y);
    ctx.lineTo(points[1].x, points[1].y);
  } else {
    // Ultra smooth final rendering
    drawUltraSmoothPath(ctx, points);
  }
  
  ctx.stroke();
}

// ensurePath2D artık gerekli değil - basit çizim sistemi kullanıyoruz

// Eşit aralık için yeniden örnekleme (genişlikler arası lineer interpolasyon)
function resamplePointsVar(pts, step) {
  if (pts.length < 3) return pts;
  const out = [ { x: pts[0].x, y: pts[0].y, w: pts[0].w } ];
  let acc = 0;
  for (let i = 1; i < pts.length; i++) {
    let ax = pts[i-1].x, ay = pts[i-1].y, aw = pts[i-1].w;
    const bx = pts[i].x, by = pts[i].y, bw = pts[i].w;
    let dx = bx - ax, dy = by - ay;
    let dist = Math.hypot(dx, dy);
    if (dist === 0) continue;
    while (acc + dist >= step) {
      const t = (step - acc) / dist;
      const nx = ax + dx * t;
      const ny = ay + dy * t;
      const nw = aw + (bw - aw) * t; // lineer
      out.push({ x: nx, y: ny, w: nw });
      ax = nx; ay = ny; aw = nw;
      dx = bx - ax; dy = by - ay; dist = Math.hypot(dx, dy);
      acc = 0;
    }
    acc += dist;
  }
  const last = pts[pts.length - 1];
  out.push({ x: last.x, y: last.y, w: last.w });
  return out;
}

// Chaikin smoothing (varying width)
function chaikinSmoothVar(pts, iterations = 1) {
  let arr = pts;
  for (let k = 0; k < iterations; k++) {
    if (arr.length < 3) return arr;
    const next = [ arr[0] ];
    for (let i = 0; i < arr.length - 1; i++) {
      const p0 = arr[i];
      const p1 = arr[i+1];
      const q = {
        x: 0.75 * p0.x + 0.25 * p1.x,
        y: 0.75 * p0.y + 0.25 * p1.y,
        w: 0.75 * p0.w + 0.25 * p1.w,
      };
      const r = {
        x: 0.25 * p0.x + 0.75 * p1.x,
        y: 0.25 * p0.y + 0.75 * p1.y,
        w: 0.25 * p0.w + 0.75 * p1.w,
      };
      next.push(q, r);
    }
    next.push(arr[arr.length - 1]);
    // Nokta sayısı patlamasın diye her 2 noktadan birini al (downsample)
    arr = next.filter((_, idx) => idx % 2 === 0);
  }
  return arr;
}

// Finalize path: sadece bbox'u hesapla, koordinatları değiştirme
function finalizePath(p) {
  if (!p || !p.points || p.points.length === 0) return;
  // Sadece bbox'u yeniden hesapla, noktaları değiştirme
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  for (const pt of p.points) {
    if (pt.x < minX) minX = pt.x; if (pt.y < minY) minY = pt.y;
    if (pt.x > maxX) maxX = pt.x; if (pt.y > maxY) maxY = pt.y;
  }
  p.bbox = { minX, minY, maxX, maxY };
}

// --- Autosave to LocalStorage (çerez yerine) ---
const STORAGE_KEY = 'sb_autosave_v1';
let autosaveTimer = null;

function saveBoardToStorage() {
  try {
    const payload = { paths: state.paths, view: state.view };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
  } catch (err) {
    console.warn('LocalStorage autosave failed', err);
  }
}

function scheduleAutosave() {
  clearTimeout(autosaveTimer);
  autosaveTimer = setTimeout(saveBoardToStorage, 500);
}

function clearBoardStorage() {
  try { localStorage.removeItem(STORAGE_KEY); } catch {}
}

function clearAutosaveCookies() {
  try {
    const COOKIE_PREFIX = 'sb_autosave_';
    // count cookie
    document.cookie = `${COOKIE_PREFIX}count=; path=/; max-age=0; samesite=lax`;
    document.cookie = `${COOKIE_PREFIX}ts=; path=/; max-age=0; samesite=lax`;
    // numbered parts 0..N (delete generously up to 200)
    for (let i = 0; i < 200; i++) {
      document.cookie = `${COOKIE_PREFIX}${i}=; path=/; max-age=0; samesite=lax`;
    }
  } catch {}
}

function loadBoardFromStorage() {
  try {
    const s = localStorage.getItem(STORAGE_KEY);
    if (!s) return null;
    return JSON.parse(s);
  } catch { return null; }
}

function migrateCookieAutosaveToStorage() {
  try {
    const COOKIE_PREFIX = 'sb_autosave_';
    const countMatch = document.cookie.match(/(?:^|; )sb_autosave_count=([^;]*)/);
    if (!countMatch) return;
    const count = Number(decodeURIComponent(countMatch[1] || '0')) || 0;
    if (!count) return;
    let enc = '';
    for (let i = 0; i < count; i++) {
      const m = document.cookie.match(new RegExp('(?:^|; )' + `${COOKIE_PREFIX}${i}`.replace(/[.$?*|{}()\[\]\\\/\+^]/g, '\\$&') + '=([^;]*)'));
      if (m) enc += m[1];
    }
    if (enc) {
      const jsonStr = decodeURIComponent(enc);
      localStorage.setItem(STORAGE_KEY, jsonStr);
    }
  } catch {}
  // ardından sadece çerezleri temizle
  clearAutosaveCookies();
}

function tryLoadBoardFromBootstrapOrStorage() {
  // Önce varsa çerezi storage'a taşı (ilk yükleme)
  migrateCookieAutosaveToStorage();
  if (window.BOARD_DATA) {
    try {
      const data = typeof window.BOARD_DATA === 'string' ? JSON.parse(window.BOARD_DATA) : window.BOARD_DATA;
      if (data?.paths) state.paths = data.paths;
      if (data?.view) state.view = data.view;
      render();
      return;
    } catch {}
  }
  const restored = loadBoardFromStorage();
  if (restored) {
    if (restored.paths) state.paths = restored.paths;
    if (restored.view) state.view = restored.view;
    render();
  }
}

