/* Roleta de Filmes — front-end */

const WHEEL_COLORS = [
  "#1565c0", "#00bfa5", "#0d47a1", "#00e0a4",
  "#1e88e5", "#1de9b6", "#0277bd", "#26c6da",
];

const state = {
  movies: [],          // lista completa (com metadados)
  includeSeries: true,
  selectedGenres: new Set(),
  pool: [],            // itens atualmente na roleta
  rotation: 0,         // rotação acumulada do canvas (graus)
  spinning: false,
};

let api = null;        // window.pywebview.api quando pronto

/* ----------------------- utilidades ----------------------- */
const $ = (sel) => document.querySelector(sel);

function toast(msg, ms = 2600) {
  const el = $("#toast");
  el.textContent = msg;
  el.classList.remove("hidden");
  clearTimeout(toast._t);
  toast._t = setTimeout(() => el.classList.add("hidden"), ms);
}

/* ----------------------- carga inicial ----------------------- */
async function init() {
  api = window.pywebview.api;
  state.movies = await api.get_movies();
  render();

  // Enriquecimento em segundo plano (sinopse, gênero, tipo, etc.).
  if (await api.tmdb_configured()) {
    const res = await api.enrich_all();
    if (res && res.items) {
      state.movies = res.items;
      render();
    }
  } else {
    toast("Configure a chave do TMDB no arquivo .env para ver sinopse e onde assistir.");
  }
}

/* ----------------------- filtragem ----------------------- */
function computePool() {
  state.pool = state.movies.filter((m) => {
    if (m.watched) return false;
    if (!state.includeSeries && m.media_type === "tv") return false;
    if (state.selectedGenres.size > 0) {
      const has = (m.genres || []).some((g) => state.selectedGenres.has(g));
      if (!has) return false;
    }
    return true;
  });
}

function allGenres() {
  const set = new Set();
  state.movies.forEach((m) => (m.genres || []).forEach((g) => set.add(g)));
  return [...set].sort((a, b) => a.localeCompare(b, "pt-BR"));
}

/* ----------------------- render ----------------------- */
function render() {
  computePool();
  drawWheel();
  renderGenres();
  renderList();
  $("#pool-info").textContent =
    `${state.pool.length} de ${state.movies.length} títulos na roleta`;
  $("#spin").disabled = state.pool.length === 0 || state.spinning;
}

/* ----------------------- roleta (canvas) ----------------------- */
function drawWheel() {
  const canvas = $("#wheel");
  const ctx = canvas.getContext("2d");

  // Renderiza na resolução real da tela (Retina) para o texto não ficar borrado.
  const dpr = window.devicePixelRatio || 1;
  const W = canvas.clientWidth || 520;   // tamanho lógico (CSS px)
  if (canvas.width !== Math.round(W * dpr)) {
    canvas.width = Math.round(W * dpr);
    canvas.height = Math.round(W * dpr);
  }
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0); // trabalha em coordenadas lógicas

  const cx = W / 2;
  const cy = W / 2;
  const r = W / 2 - 6;
  ctx.clearRect(0, 0, W, W);

  const n = state.pool.length;
  if (n === 0) {
    ctx.fillStyle = "rgba(255,255,255,0.08)";
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#a7c7d6";
    ctx.font = "16px -apple-system, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("Nenhum título no filtro", cx, cy);
    return;
  }

  const arc = (Math.PI * 2) / n;
  for (let i = 0; i < n; i++) {
    const start = i * arc - Math.PI / 2;
    const end = start + arc;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, r, start, end);
    ctx.closePath();
    ctx.fillStyle = WHEEL_COLORS[i % WHEEL_COLORS.length];
    ctx.fill();
    ctx.strokeStyle = "rgba(255,255,255,0.10)";
    ctx.lineWidth = 1;
    ctx.stroke();

    // texto
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(start + arc / 2);
    ctx.textAlign = "right";
    ctx.fillStyle = "#ffffff";
    ctx.font = `${n > 24 ? 10 : n > 14 ? 12 : 14}px -apple-system, sans-serif`;
    const label = truncate(state.pool[i].title, n > 20 ? 16 : 24);
    ctx.fillText(label, r - 14, 5);
    ctx.restore();
  }

  // miolo
  ctx.beginPath();
  ctx.arc(cx, cy, r * 0.22, 0, Math.PI * 2);
  ctx.fillStyle = "rgba(7,34,58,0.9)";
  ctx.fill();
}

function truncate(str, max) {
  return str.length > max ? str.slice(0, max - 1) + "…" : str;
}

/* ----------------------- girar ----------------------- */
function spin() {
  if (state.spinning || state.pool.length === 0) return;
  state.spinning = true;
  $("#spin").disabled = true;

  const n = state.pool.length;
  const arc = 360 / n;
  const winner = Math.floor(Math.random() * n);

  // O ponteiro está no topo. O centro da fatia 'winner' (medido em sentido horário
  // a partir do topo) está em winner*arc + arc/2. Para colocá-lo sob o ponteiro a
  // rotação final precisa ser ≡ -(centro) (mód 360).
  // Calculamos o giro ADICIONAL a partir da posição atual da roleta, para que o
  // resultado bata com a fatia sorteada em qualquer giro (não só no primeiro).
  const targetCenter = winner * arc + arc / 2;
  const fullSpins = 5 * 360; // voltas completas só para dar emoção
  const currentMod = ((state.rotation % 360) + 360) % 360;
  const needed = (((-targetCenter - currentMod) % 360) + 360) % 360;

  state.rotation += fullSpins + needed;
  const wheel = $("#wheel");
  wheel.style.transform = `rotate(${state.rotation}deg)`;

  const onEnd = () => {
    wheel.removeEventListener("transitionend", onEnd);
    state.spinning = false;
    $("#spin").disabled = false;
    showResult(state.pool[winner]);
  };
  wheel.addEventListener("transitionend", onEnd);
}

/* ----------------------- cartão de resultado ----------------------- */
async function showResult(item) {
  // Busca detalhes atualizados (enriquece sob demanda se faltar).
  let data = item;
  try {
    const fresh = await api.get_details(item.id);
    if (fresh) data = fresh;
  } catch (e) { /* usa o que já temos */ }

  $("#result-title").textContent = data.title;

  const poster = $("#result-poster");
  if (data.poster) { poster.src = data.poster; poster.style.display = ""; }
  else { poster.removeAttribute("src"); poster.style.display = "none"; }

  // tags: tipo + gêneros
  const tags = $("#result-tags");
  tags.innerHTML = "";
  if (data.media_type) {
    const t = document.createElement("span");
    t.className = "tag type";
    t.textContent = data.media_type === "tv" ? "Série" : "Filme";
    tags.appendChild(t);
  }
  (data.genres || []).forEach((g) => {
    const t = document.createElement("span");
    t.className = "tag";
    t.textContent = g;
    tags.appendChild(t);
  });

  $("#result-overview").textContent =
    data.overview || "Sinopse não encontrada no TMDB.";

  // provedores
  const prov = $("#result-providers");
  prov.innerHTML = "";
  if ((data.providers || []).length === 0) {
    const e = document.createElement("span");
    e.className = "empty";
    e.textContent = "Sem streaming listado no Brasil — tente o Stremio. 👇";
    prov.appendChild(e);
  } else {
    data.providers.forEach((p) => {
      const d = document.createElement("div");
      d.className = "provider";
      if (p.logo) {
        const img = document.createElement("img");
        img.src = p.logo;
        d.appendChild(img);
      }
      const span = document.createElement("span");
      span.textContent = p.name;
      d.appendChild(span);
      prov.appendChild(d);
    });
  }

  // trailer
  const trailerBtn = $("#btn-trailer");
  if (data.trailer_url) {
    trailerBtn.disabled = false;
    trailerBtn.onclick = () => api.open_url(data.trailer_url);
  } else {
    trailerBtn.disabled = true;
    trailerBtn.onclick = null;
  }

  $("#btn-stremio").onclick = () => api.open_stremio(data);

  $("#btn-watch").onclick = async () => {
    await api.set_watched(data.id, true);
    const m = state.movies.find((x) => x.id === data.id);
    if (m) m.watched = true;
    $("#result-overlay").classList.add("hidden");
    render();
    toast(`Bom filme! "${data.title}" saiu da roleta. 🍿`);
  };

  $("#result-overlay").classList.remove("hidden");
}

/* ----------------------- gêneros ----------------------- */
function renderGenres() {
  const box = $("#genre-chips");
  box.innerHTML = "";
  const genres = allGenres();
  if (genres.length === 0) {
    box.innerHTML = '<span class="providers empty">Aguardando dados do TMDB…</span>';
    return;
  }
  genres.forEach((g) => {
    const chip = document.createElement("button");
    chip.className = "chip" + (state.selectedGenres.has(g) ? " active" : "");
    chip.textContent = g;
    chip.onclick = () => {
      if (state.selectedGenres.has(g)) state.selectedGenres.delete(g);
      else state.selectedGenres.add(g);
      render();
    };
    box.appendChild(chip);
  });
}

/* ----------------------- lista (minha lista) ----------------------- */
function renderList() {
  const box = $("#movie-list");
  box.innerHTML = "";
  state.movies.forEach((m) => {
    const row = document.createElement("div");
    row.className = "movie-row" + (m.watched ? " watched" : "");

    const name = document.createElement("span");
    name.className = "name";
    name.textContent = m.title;
    row.appendChild(name);

    if (m.watched) {
      const seen = document.createElement("span");
      seen.className = "seen";
      seen.textContent = "visto";
      row.appendChild(seen);

      const back = document.createElement("button");
      back.className = "row-btn";
      back.textContent = "↩";
      back.title = "Devolver à roleta";
      back.onclick = async () => {
        await api.set_watched(m.id, false);
        m.watched = false;
        render();
        toast(`"${m.title}" voltou para a roleta!`);
      };
      row.appendChild(back);
    }

    const kind = document.createElement("span");
    if (m.media_type === "tv") { kind.className = "kind tv"; kind.textContent = "Série"; }
    else if (m.media_type === "movie") { kind.className = "kind"; kind.textContent = "Filme"; }
    else { kind.className = "kind unknown"; kind.textContent = "?"; }
    row.appendChild(kind);

    const fix = document.createElement("button");
    fix.className = "row-btn";
    fix.textContent = "✎";
    fix.title = "Corrigir o título vinculado no TMDB";
    fix.onclick = () => openPicker({ mode: "recast", itemId: m.id, title: m.title });
    row.appendChild(fix);

    const del = document.createElement("button");
    del.className = "row-del";
    del.textContent = "×";
    del.onclick = async () => {
      await api.remove_movie(m.id);
      state.movies = state.movies.filter((x) => x.id !== m.id);
      render();
    };
    row.appendChild(del);

    box.appendChild(row);
  });
}

/* ----------------------- eventos de UI ----------------------- */
function wireUI() {
  $("#spin").onclick = spin;

  $("#btn-close").onclick = () => api.close_app();
  $("#btn-min").onclick = () => api.minimize_app();

  $("#btn-panel").onclick = () => $("#side-panel").classList.remove("hidden");
  $("#panel-close").onclick = () => $("#side-panel").classList.add("hidden");
  $("#side-panel").onclick = (e) => {
    if (e.target.id === "side-panel") $("#side-panel").classList.add("hidden");
  };

  $("#result-close").onclick = () => $("#result-overlay").classList.add("hidden");
  $("#result-overlay").onclick = (e) => {
    if (e.target.id === "result-overlay") e.currentTarget.classList.add("hidden");
  };

  $("#toggle-series").onchange = (e) => {
    state.includeSeries = e.target.checked;
    render();
  };

  $("#genres-clear").onclick = () => {
    state.selectedGenres.clear();
    render();
  };

  $("#add-form").onsubmit = async (e) => {
    e.preventDefault();
    const input = $("#add-input");
    const title = input.value.trim();
    if (!title) return;
    input.value = "";
    openPicker({ mode: "add", title });
  };

  $("#picker-close").onclick = closePicker;
  $("#picker-overlay").onclick = (e) => {
    if (e.target.id === "picker-overlay") closePicker();
  };
  $("#picker-none").onclick = onPickerNone;
}

/* ----------------------- seletor de candidatos ----------------------- */
let pickerCtx = null; // { mode: 'add'|'recast', title, itemId? }

async function openPicker(ctx) {
  pickerCtx = ctx;
  $("#side-panel").classList.add("hidden");
  $("#picker-title").textContent = ctx.title;
  const list = $("#picker-list");
  list.innerHTML = '<p class="picker-empty">Buscando no TMDB…</p>';
  $("#picker-overlay").classList.remove("hidden");

  const res = await api.search_candidates(ctx.title);
  if (!res || !res.ok) {
    list.innerHTML = `<p class="picker-empty">${(res && res.error) || "Erro ao buscar."}</p>`;
    return;
  }
  const cands = res.candidates || [];
  if (cands.length === 0) {
    list.innerHTML = '<p class="picker-empty">Nenhum resultado no TMDB para esse título.</p>';
    return;
  }
  list.innerHTML = "";
  cands.forEach((c) => {
    const btn = document.createElement("button");
    btn.className = "cand";
    btn.onclick = () => pickCandidate(c);

    const img = document.createElement("img");
    if (c.poster) img.src = c.poster;
    btn.appendChild(img);

    const body = document.createElement("div");
    body.className = "cand-body";
    const head = document.createElement("div");
    head.className = "cand-head";
    head.innerHTML =
      `<span class="cand-name"></span>` +
      (c.year ? `<span class="cand-year">(${c.year})</span>` : "") +
      `<span class="cand-kind ${c.media_type === "tv" ? "tv" : ""}">${c.media_type === "tv" ? "Série" : "Filme"}</span>`;
    head.querySelector(".cand-name").textContent = c.title;
    body.appendChild(head);
    if (c.overview) {
      const ov = document.createElement("p");
      ov.className = "cand-ov";
      ov.textContent = c.overview;
      body.appendChild(ov);
    }
    btn.appendChild(body);
    list.appendChild(btn);
  });
}

function closePicker() {
  $("#picker-overlay").classList.add("hidden");
  pickerCtx = null;
}

async function pickCandidate(candidate) {
  const ctx = pickerCtx;
  if (!ctx) return;
  if (ctx.mode === "add") {
    const res = await api.add_movie_choice(ctx.title, candidate);
    if (res && res.item) {
      state.movies.push(res.item);
      toast(res.warning || `"${res.item.title}" adicionado!`);
    } else {
      toast((res && res.error) || "Erro ao adicionar.");
    }
  } else if (ctx.mode === "recast") {
    const res = await api.recast_movie(ctx.itemId, candidate);
    if (res && res.ok) {
      const idx = state.movies.findIndex((m) => m.id === ctx.itemId);
      if (idx >= 0) state.movies[idx] = res.item;
      toast(`"${res.item.title}" corrigido!`);
    } else {
      toast((res && res.error) || "Erro ao corrigir.");
    }
  }
  closePicker();
  render();
}

async function onPickerNone() {
  // Adiciona sem vincular ao TMDB (só no modo "add").
  const ctx = pickerCtx;
  if (!ctx || ctx.mode !== "add") { closePicker(); return; }
  const res = await api.add_movie_choice(ctx.title, null);
  if (res && res.item) {
    state.movies.push(res.item);
    toast(`"${res.item.title}" adicionado (sem dados do TMDB).`);
  }
  closePicker();
  render();
}

/* ----------------------- bootstrap ----------------------- */
window.addEventListener("pywebviewready", () => {
  wireUI();
  init();
});

// Redesenha nítido ao redimensionar a janela.
let _resizeT;
window.addEventListener("resize", () => {
  clearTimeout(_resizeT);
  _resizeT = setTimeout(drawWheel, 120);
});
