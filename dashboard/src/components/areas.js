// Areas page: one council's neighbourhoods (MSOAs) on a map, its key figures vs England,
// an indicator comparison and its housing mix. Council comes from ?council= or the search box.
import * as d3 from "npm:d3@7.9.2";
import {AGE, C, IND, NO_DATA, RAMP, f1, fInt, indicatorSwitch, mountRail, onResize, pct, rowsFromColumns} from "./common.js";

const LABELS = {
  semi_detached: "Semi-detached", mid_terrace: "Mid-terrace", end_terrace: "End-terrace", detached: "Detached",
  flat: "Flat", bungalow: "Bungalow", house_unknown: "House (other)", gas: "Gas boiler", community: "Community heating",
  electric_storage: "Storage heaters", electric_direct: "Direct electric", heat_pump: "Heat pump",
  other_fuel: "Oil, LPG or solid fuel", other: "Other", unknown: "Not recorded", ...AGE,
};
const MIX = {age_band: "Age", dwelling_type: "Type", heating: "Heating", epc_band: "EPC band"};
const COMPARE = [...Object.keys(IND), "pct_pre1919"];
const NAME = {...Object.fromEntries(Object.entries(IND).map(([k, v]) => [k, v.short])), pct_pre1919: "Built before 1919"};

let D, S, state, byLad, shapesByLad;

function decode(shape, scale) {
  const ring = r => {
    let x = r[0], y = r[1];
    const pts = [[x / scale, y / scale]];
    for (let i = 2; i < r.length; i += 2) { x += r[i]; y += r[i + 1]; pts.push([x / scale, y / scale]); }
    return pts;
  };
  return {type: "Feature", id: shape.id, properties: {id: shape.id},
          geometry: {type: "MultiPolygon", coordinates: shape.p.map(poly => poly.map(ring))}};
}

function council() { return D.councils.find(c => c.lad24cd === state.lad); }

function render() {
  const c = council(), k = state.ind;
  const msoas = byLad.get(state.lad) ?? [];
  indicatorSwitch("#seg", k, key => { state.ind = key; state.sel = null; render(); });
  d3.select("#council-name").text(c.lad24nm).classed("long", c.lad24nm.length > 18);
  d3.select("#council-meta").text(`${c.region_name} · ${fInt(c.n_homes)} social homes · ~${fInt(Math.round(c.expected_cases))} estimated to have damp`);
  renderMap(msoas); renderStrip(c); renderTiles(c); renderCompare(c); renderMix();
}

function renderStrip(c) {
  const k = state.ind, el = document.getElementById("strip"), w = el.clientWidth, h = el.clientHeight;
  const all = D.councils.filter(x => x[k] != null && x.n_homes >= 500);
  const ranked = [...all].sort((a, b) => b[k] - a[k]), rank = ranked.findIndex(x => x.lad24cd === c.lad24cd);
  d3.select("#rank-text").html(rank >= 0
    ? `<b>${c.lad24nm}</b> ranks <b>#${rank + 1} of ${ranked.length}</b> councils for ${IND[k].noun} (${pct(c[k])})`
    : `<b>${c.lad24nm}</b>: ${pct(c[k])} ${IND[k].noun} (fewer than 500 social homes, not ranked)`);
  const x = d3.scaleLinear().domain([0, d3.max(all, d => d[k]) * 1.02]).range([6, w - 6]);
  const mid = h / 2 - 4, jitter = i => ((i * 37) % 11 - 5) * (h / 40);
  const svg = d3.select(el).selectAll("svg").data([0]).join("svg").attr("viewBox", `0 0 ${w} ${h}`)
    .attr("role", "img").attr("aria-label", `Where ${c.lad24nm} sits among all councils`);
  svg.selectAll("line.base").data([0]).join("line").attr("class", "base").attr("x1", 0).attr("x2", w)
    .attr("y1", mid).attr("y2", mid).attr("stroke", "rgba(27,29,33,.08)");
  svg.selectAll("circle.c").data(all, d => d.lad24cd).join("circle").attr("class", "c").attr("r", 3.2)
    .attr("fill", "#C9CDD3").attr("opacity", .9)
    .transition().duration(400).attr("cx", d => x(d[k])).attr("cy", (d, i) => mid + jitter(i));
  const e = D.england[k];
  svg.selectAll("line.eng").data([e]).join("line").attr("class", "eng").attr("stroke", C.text)
    .attr("stroke-dasharray", "3 3").attr("opacity", .5).attr("y1", 4).attr("y2", h - 14)
    .transition().duration(400).attr("x1", d => x(d)).attr("x2", d => x(d));
  svg.selectAll("text.eng").data([e]).join("text").attr("class", "eng xlab").attr("text-anchor", "middle")
    .attr("y", h - 2).transition().duration(400).attr("x", d => x(d)).text(d => `England ${pct(d)}`);
  const sel = svg.selectAll("g.sel").data([c]).join(en => {
    const g = en.append("g").attr("class", "sel");
    g.append("circle").attr("r", 7).attr("fill", C.accent).attr("stroke", "#fff").attr("stroke-width", 2.5);
    return g;
  });
  sel.raise().transition().duration(400).attr("transform", d => `translate(${x(d[k])},${mid})`);
}

function renderMap(msoas) {
  const k = state.ind, wrap = document.getElementById("map"), w = wrap.clientWidth, h = wrap.clientHeight;
  if (!shapesByLad.has(state.lad)) shapesByLad.set(state.lad, S.shapes.filter(s => s.lad === state.lad).map(s => decode(s, S.scale)));
  const features = shapesByLad.get(state.lad);
  const fc = {type: "FeatureCollection", features};
  const proj = d3.geoMercator().fitExtent([[12, 12], [w - 12, h - 64]], fc), path = d3.geoPath(proj);
  const byId = new Map(msoas.map(m => [m.msoa21cd, m]));
  const vals = msoas.map(m => m[k]).filter(v => v != null);
  const col = d3.scaleQuantize().domain(d3.extent(vals).map((v, i) => v ?? i)).range(RAMP);
  const sel = state.hover ?? state.sel;

  const svg = d3.select(wrap).select("svg").attr("viewBox", `0 0 ${w} ${h}`);
  svg.selectAll("path.area").data(features, d => d.id).join("path").attr("class", "area hexlike")
    .attr("d", path)
    .attr("fill", d => { const v = byId.get(d.id)?.[k]; return v == null ? NO_DATA : col(v); })
    .classed("sel", d => d.id === sel)
    .on("mouseenter", (e, d) => { state.hover = d.id; renderMap(msoas); })
    .on("mouseleave", () => { state.hover = null; renderMap(msoas); })
    .on("click", (e, d) => { state.sel = d.id; renderMap(msoas); })
    .filter(d => d.id === sel).raise();

  const box = document.getElementById("callout"), c = council();
  const m = sel ? byId.get(sel) : null, f = sel ? features.find(d => d.id === sel) : null;
  svg.selectAll(".lead").remove();
  if (m && f) {
    const [cx, cy] = path.centroid(f), delta = m[k] == null ? null : m[k] - c[k];
    box.style.display = "block";
    box.innerHTML = `<div class="n">${m.msoa21nm}</div><div class="r">${fInt(m.n_homes)} social homes</div>
      <div class="v">${pct(m[k])}</div>
      <div class="d ${delta >= 0 ? "up" : "down"}">${delta == null ? "Too few homes to show" : `${delta >= 0 ? "+" : ""}${f1(delta)} pts vs ${c.lad24nm}`}</div>`;
    const bw = box.offsetWidth, bh = box.offsetHeight;
    let bx = cx + 36, by = cy - bh - 26;
    if (bx + bw > w - 8) bx = cx - bw - 36;
    if (by < 8) by = cy + 26;
    box.style.left = `${bx}px`; box.style.top = `${by}px`;
    svg.append("line").attr("class", "lead").attr("x1", cx).attr("y1", cy).attr("x2", bx > cx ? bx : bx + bw)
      .attr("y2", by > cy ? by : by + bh).attr("stroke", C.text).attr("stroke-width", 1.2);
    svg.append("circle").attr("class", "lead").attr("cx", cx).attr("cy", cy).attr("r", 3.5).attr("fill", C.text);
  } else {
    box.style.display = "none";
  }
  d3.select("#council-avg").text(pct(c[k]));
  d3.select("#leg-bar").selectAll("span").data(RAMP).join("span").style("background", d => d);
  d3.select("#leg-max").text(vals.length ? pct(d3.max(vals)) : "");
  d3.select("#leg-min").text(vals.length ? pct(d3.min(vals)) : "");
  d3.select("#map-sub").text(`Share of social homes ${IND[k].phrase} · colours span this council's range`);
}

function renderTiles(c) {
  const e = D.england;
  const tiles = [
    ["Estimated damp risk", c.risk, e.risk, "%"],
    ["In England's riskiest 10%", c.pct_top10, 10, "%"],
    ["Uninsulated walls", c.pct_wall_uninsulated, e.pct_wall_uninsulated, "%"],
    ["Rated EPC E–G", c.pct_epc_efg, e.pct_epc_efg, "%"],
  ];
  d3.select("#tiles").selectAll("div.tile").data(tiles).join("div").attr("class", "tile")
    .classed("hl", ([, v, ev]) => v > ev)
    .html(([label, v, ev, u]) => {
      const better = v <= ev;
      const fmt = u ? d3.format("+.1f") : d3.format("+.0f");
      const diff = Math.abs(v - ev) < (u ? 0.05 : 0.5) ? "Same" : `${fmt(v - ev)}${u ? " pts" : ""}`;
      return `<div class="l">${label}</div><div class="v">${u ? f1(v) + "%" : Math.round(v)}</div>
        <div class="s"><span class="${better ? "good" : "bad"}">${diff}</span> vs England ${u ? f1(ev) + "%" : Math.round(ev)}</div>`;
    });
}

function renderCompare(c) {
  const e = D.england, max = d3.max(COMPARE, k => Math.max(c[k] ?? 0, e[k] ?? 0)) * 1.08;
  d3.select("#compare").selectAll("div.cmp").data(COMPARE).join("div").attr("class", "cmp")
    .classed("hl", k => c[k] > e[k])
    .html(k => `<span class="lab">${NAME[k]}</span>
      <span class="track"><span class="fill" style="width:${(c[k] / max) * 100}%"></span>
      <span class="mark" style="left:${(e[k] / max) * 100}%"></span></span>
      <span class="val">${pct(c[k])}</span>`);
}

function renderMix() {
  const feat = state.mix, lad = D.mix[state.lad]?.[feat] ?? {}, eng = D.mix.ENGLAND[feat];
  d3.select("#mix-seg").selectAll("button").data(Object.keys(MIX)).join("button").text(f => MIX[f])
    .attr("aria-pressed", f => f === feat).on("click", (e, f) => { state.mix = f; renderMix(); });
  let cats = Object.keys(eng);
  if (feat === "age_band") cats = Object.keys(AGE).filter(a => cats.includes(a));
  else if (feat === "epc_band") cats = cats.filter(x => x !== "unknown").sort();
  else cats.sort((a, b) => (eng[b] ?? 0) - (eng[a] ?? 0));
  cats = cats.filter(x => (lad[x] ?? 0) >= 0.5 || (eng[x] ?? 0) >= 0.5).slice(0, 7);
  const max = d3.max(cats, x => Math.max(lad[x] ?? 0, eng[x] ?? 0)) * 1.08 || 1;
  d3.select("#mix").selectAll("div.cmp").data(cats, d => d).join("div").attr("class", "cmp")
    .html(x => `<span class="lab">${LABELS[x] ?? x}</span>
      <span class="track"><span class="fill" style="width:${((lad[x] ?? 0) / max) * 100}%"></span>
      <span class="mark" style="left:${((eng[x] ?? 0) / max) * 100}%"></span></span>
      <span class="val">${f1(lad[x] ?? 0)}%</span>`);
}

export function mountAreas(areas, shapes, invalidation) {
  mountRail("areas");
  D = areas; S = shapes;
  const msoas = rowsFromColumns(D.msoas);
  byLad = d3.group(msoas, m => m.lad24cd);
  shapesByLad = new Map();

  const q = new URLSearchParams(location.search).get("council")?.toLowerCase();
  const start = D.councils.find(c => c.lad24cd.toLowerCase() === q || c.lad24nm.toLowerCase() === q)
    ?? D.councils.find(c => c.lad24nm === "Manchester");
  state = {ind: "risk", lad: start.lad24cd, sel: null, hover: null, mix: "age_band"};

  d3.select("#councils").selectAll("option").data(D.councils.map(c => c.lad24nm).sort()).join("option").attr("value", d => d);
  d3.select("#search").on("change", function () {
    const c = D.councils.find(c => c.lad24nm.toLowerCase() === this.value.trim().toLowerCase());
    if (!c) return;
    state.lad = c.lad24cd; state.sel = null; this.value = "";
    history.replaceState(null, "", `?council=${c.lad24cd}`);
    render();
  });
  onResize(document.querySelector(".bento"), render, invalidation);
  render();
}
