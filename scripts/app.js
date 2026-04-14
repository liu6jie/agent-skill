const $ = (id) => document.getElementById(id);

const state = {
  img: null,
  imgName: null,
  zoom: 1,
  rotate: 0,
  offsetX: 0,
  offsetY: 0,
  brightness: 0,
  contrast: 0,
  saturation: 0,
  hue: 0,
  sharpen: 0,
  blur: 0,
  bgColor: '#111827',
  aspect: 'free',
  exportFormat: 'image/png',
  exportQuality: 0.92,
  wmText: '',
  wmSize: 36,
  wmAlpha: 0.35,
  wmColor: '#ffffff',
  wmPos: 'br'
};

const canvas = $('canvas');
const ctx = canvas.getContext('2d');
const statusEl = $('status');

function setStatus(text) {
  statusEl.textContent = text;
}

function applyFilters() {
  const b = 100 + Number(state.brightness);
  const c = 100 + Number(state.contrast);
  const s = 100 + Number(state.saturation);
  const h = Number(state.hue);
  const blur = Number(state.blur);
  ctx.filter = `brightness(${b}%) contrast(${c}%) saturate(${s}%) hue-rotate(${h}deg) blur(${blur}px)`;
}

function clearCanvas() {
  ctx.save();
  ctx.filter = 'none';
  ctx.fillStyle = state.bgColor;
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.restore();
}

function computeCanvasSize() {
  const maxW = 1400;
  const maxH = 980;

  if (!state.img) {
    canvas.width = 1200;
    canvas.height = 900;
    return;
  }

  const imgW = state.img.naturalWidth || state.img.width;
  const imgH = state.img.naturalHeight || state.img.height;

  let w = Math.min(maxW, imgW);
  let h = Math.round((w / imgW) * imgH);
  if (h > maxH) {
    h = maxH;
    w = Math.round((h / imgH) * imgW);
  }

  if (state.aspect !== 'free') {
    const [a, b] = state.aspect.split(':').map(Number);
    if (a > 0 && b > 0) {
      const target = a / b;
      const current = w / h;
      if (current > target) w = Math.round(h * target);
      else h = Math.round(w / target);
    }
  }

  canvas.width = Math.max(320, w);
  canvas.height = Math.max(240, h);
}

function drawWatermark() {
  const text = (state.wmText || '').trim();
  if (!text) return;

  const pad = 18;
  let x = canvas.width - pad;
  let y = canvas.height - pad;
  let align = 'right';
  let baseline = 'bottom';

  switch (state.wmPos) {
    case 'bl':
      x = pad;
      y = canvas.height - pad;
      align = 'left';
      baseline = 'bottom';
      break;
    case 'tr':
      x = canvas.width - pad;
      y = pad;
      align = 'right';
      baseline = 'top';
      break;
    case 'tl':
      x = pad;
      y = pad;
      align = 'left';
      baseline = 'top';
      break;
    case 'center':
      x = canvas.width / 2;
      y = canvas.height / 2;
      align = 'center';
      baseline = 'middle';
      break;
    default:
      break;
  }

  ctx.save();
  ctx.filter = 'none';
  ctx.globalAlpha = Number(state.wmAlpha);
  ctx.fillStyle = state.wmColor;
  ctx.font = `700 ${Number(state.wmSize)}px ui-sans-serif, system-ui, -apple-system, "Segoe UI", "Microsoft YaHei"`;
  ctx.textAlign = align;
  ctx.textBaseline = baseline;
  ctx.fillText(text, x, y);
  ctx.restore();
}

function drawSharpenIfNeeded() {
  const amount = Number(state.sharpen);
  if (!state.img || amount <= 0) return;

  const w = canvas.width;
  const h = canvas.height;
  const src = ctx.getImageData(0, 0, w, h);
  const dst = ctx.createImageData(w, h);

  const s = src.data;
  const d = dst.data;

  const k = [0, -1, 0, -1, 5, -1, 0, -1, 0];
  const clamp = (v) => (v < 0 ? 0 : v > 255 ? 255 : v);

  for (let y = 1; y < h - 1; y++) {
    for (let x = 1; x < w - 1; x++) {
      const i = (y * w + x) * 4;
      for (let c = 0; c < 3; c++) {
        let acc = 0;
        let ki = 0;
        for (let oy = -1; oy <= 1; oy++) {
          for (let ox = -1; ox <= 1; ox++) {
            const ii = ((y + oy) * w + (x + ox)) * 4 + c;
            acc += s[ii] * k[ki++];
          }
        }
        const base = s[i + c];
        const out = base + (acc - base) * amount;
        d[i + c] = clamp(out);
      }
      d[i + 3] = s[i + 3];
    }
  }

  ctx.putImageData(dst, 0, 0);
}

function render() {
  computeCanvasSize();
  clearCanvas();
  if (!state.img) return;

  const imgW = state.img.naturalWidth || state.img.width;
  const imgH = state.img.naturalHeight || state.img.height;

  const cx = canvas.width / 2 + Number(state.offsetX);
  const cy = canvas.height / 2 + Number(state.offsetY);
  const angle = (Number(state.rotate) * Math.PI) / 180;

  ctx.save();
  applyFilters();
  ctx.translate(cx, cy);
  ctx.rotate(angle);
  ctx.scale(Number(state.zoom), Number(state.zoom));
  ctx.drawImage(state.img, -imgW / 2, -imgH / 2);
  ctx.restore();

  drawSharpenIfNeeded();
  drawWatermark();
}

async function loadImageFromBlob(blob, name = 'local') {
  const url = URL.createObjectURL(blob);
  const img = new Image();
  img.decoding = 'async';
  await new Promise((resolve, reject) => {
    img.onload = () => resolve();
    img.onerror = () => reject(new Error('图片加载失败'));
    img.src = url;
  });
  URL.revokeObjectURL(url);

  state.img = img;
  state.imgName = name;
  setStatus(`已加载：${name}（${img.naturalWidth}×${img.naturalHeight}）`);
  render();
}

async function loadAssetManifest() {
  const select = $('assetSelect');
  select.innerHTML = '';

  const opt0 = document.createElement('option');
  opt0.value = '';
  opt0.textContent = '选择 assets 里的图片…';
  select.appendChild(opt0);

  try {
    const res = await fetch('/assets/manifest.json', { cache: 'no-store' });
    if (!res.ok) throw new Error('manifest.json 不存在或无法读取');
    const data = await res.json();
    const images = Array.isArray(data.images) ? data.images : [];
    for (const name of images) {
      const opt = document.createElement('option');
      opt.value = name;
      opt.textContent = name;
      select.appendChild(opt);
    }
    if (images.length > 0) {
      select.value = images[0];
      setStatus(`已发现 assets 图片：${images.length} 张（已选中 ${images[0]}，点“从 assets 加载”即可）`);
    } else {
      setStatus('assets/manifest.json 已读取，但 images 为空');
    }
  } catch {
    const opt = document.createElement('option');
    opt.value = '';
    opt.textContent = '（未找到 assets/manifest.json）';
    select.appendChild(opt);
    setStatus('未找到 assets/manifest.json（请先创建并填写 images）');
  }
}

function bindSlider(id, key) {
  const el = $(id);
  el.addEventListener('input', () => {
    state[key] = Number(el.value);
    render();
  });
}

function resetControls() {
  const defaults = {
    zoom: 1,
    rotate: 0,
    offsetX: 0,
    offsetY: 0,
    brightness: 0,
    contrast: 0,
    saturation: 0,
    hue: 0,
    sharpen: 0,
    blur: 0,
    bgColor: '#111827',
    aspect: 'free',
    exportFormat: 'image/png',
    exportQuality: 0.92,
    wmText: '',
    wmSize: 36,
    wmAlpha: 0.35,
    wmColor: '#ffffff',
    wmPos: 'br'
  };

  Object.assign(state, defaults);

  $('zoom').value = String(defaults.zoom);
  $('rotate').value = String(defaults.rotate);
  $('offsetX').value = String(defaults.offsetX);
  $('offsetY').value = String(defaults.offsetY);
  $('brightness').value = String(defaults.brightness);
  $('contrast').value = String(defaults.contrast);
  $('saturation').value = String(defaults.saturation);
  $('hue').value = String(defaults.hue);
  $('sharpen').value = String(defaults.sharpen);
  $('blur').value = String(defaults.blur);
  $('bgColor').value = defaults.bgColor;
  $('aspect').value = defaults.aspect;
  $('exportFormat').value = defaults.exportFormat;
  $('exportQuality').value = String(defaults.exportQuality);
  $('wmText').value = defaults.wmText;
  $('wmSize').value = String(defaults.wmSize);
  $('wmAlpha').value = String(defaults.wmAlpha);
  $('wmColor').value = defaults.wmColor;
  $('wmPos').value = defaults.wmPos;

  render();
}

function exportImage() {
  if (!state.img) {
    alert('请先加载图片');
    return;
  }
  const format = state.exportFormat;
  const base = (state.imgName || 'export').replace(/[^\w\-\.]+/g, '_');
  const ext = format === 'image/jpeg' ? 'jpg' : 'png';
  const filename = `${base}_edited.${ext}`;
  const quality = format === 'image/jpeg' ? Number(state.exportQuality) : undefined;

  const triggerDownload = (href) => {
    const a = document.createElement('a');
    a.download = filename;
    a.href = href;
    document.body.appendChild(a);
    a.click();
    a.remove();
  };

  // Prefer toBlob (more reliable + memory-friendly than dataURL)
  canvas.toBlob(
    (blob) => {
      try {
        if (!blob) {
          // Fallback
          const dataUrl = canvas.toDataURL(format, quality);
          triggerDownload(dataUrl);
          return;
        }
        const url = URL.createObjectURL(blob);
        triggerDownload(url);
        setTimeout(() => URL.revokeObjectURL(url), 10_000);
      } catch (e) {
        alert(`导出失败：${e?.message || String(e)}`);
      }
    },
    format,
    quality
  );
}

function init() {
  loadAssetManifest();

  $('btnPickFile').addEventListener('click', () => $('fileInput').click());
  $('fileInput').addEventListener('change', async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    await loadImageFromBlob(file, file.name);
  });

  $('btnLoadAsset').addEventListener('click', async () => {
    const name = $('assetSelect').value;
    if (!name) return;
    const res = await fetch(`/assets/${encodeURIComponent(name)}`, { cache: 'no-store' });
    if (!res.ok) {
      alert('加载失败：请检查 assets/ 文件名与 manifest.json 是否一致');
      return;
    }
    const blob = await res.blob();
    await loadImageFromBlob(blob, name);
  });

  $('btnReset').addEventListener('click', resetControls);
  $('btnExport').addEventListener('click', exportImage);

  bindSlider('zoom', 'zoom');
  bindSlider('rotate', 'rotate');
  bindSlider('offsetX', 'offsetX');
  bindSlider('offsetY', 'offsetY');
  bindSlider('brightness', 'brightness');
  bindSlider('contrast', 'contrast');
  bindSlider('saturation', 'saturation');
  bindSlider('hue', 'hue');
  bindSlider('sharpen', 'sharpen');
  bindSlider('blur', 'blur');

  $('bgColor').addEventListener('input', (e) => {
    state.bgColor = e.target.value;
    render();
  });
  $('aspect').addEventListener('change', (e) => {
    state.aspect = e.target.value;
    render();
  });
  $('exportFormat').addEventListener('change', (e) => {
    state.exportFormat = e.target.value;
  });
  $('exportQuality').addEventListener('input', (e) => {
    state.exportQuality = Number(e.target.value);
  });

  $('wmText').addEventListener('input', (e) => {
    state.wmText = e.target.value;
    render();
  });
  $('wmSize').addEventListener('input', (e) => {
    state.wmSize = Number(e.target.value);
    render();
  });
  $('wmAlpha').addEventListener('input', (e) => {
    state.wmAlpha = Number(e.target.value);
    render();
  });
  $('wmColor').addEventListener('input', (e) => {
    state.wmColor = e.target.value;
    render();
  });
  $('wmPos').addEventListener('change', (e) => {
    state.wmPos = e.target.value;
    render();
  });

  setStatus('未加载图片');
  render();
}

init();

