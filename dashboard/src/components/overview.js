// Overview page: hex map hero, construction-age bars, watch list and deprivation.
// All cards are driven by one indicator switch; hover / click / search select a council.
import * as d3 from "npm:d3@7.9.2";
import {AGE, IND, NO_DATA, RAMP, f1, fInt, mountRail} from "./common.js";

let state, D, HEX, byCode;


const colour = () => {
  const vals = D.councils.map(c => c[state.ind]).filter(v => v != null).sort(d3.ascending);
  return d3.scaleQuantize().domain([vals[0], d3.quantile(vals, 0.98)]).range(RAMP);
};
const eligible = () => D.councils.filter(c => c.n_homes >= 500 && c[state.ind] != null);
const top5 = () => eligible().sort((a, b) => b[state.ind] - a[state.ind]).slice(0, 5);

function render() {
  if (!D) return;
  const k = state.ind, eng = D.england[k];
  if (!state.sel) state.sel = top5()[0].lad24cd;
  d3.select("#seg").selectAll("button").attr("aria-pressed", d => d === k);
  d3.select("#map-sub").text(`Share of social homes ${IND[k].phrase} · one hexagon per council`);
  d3.select("#eng-avg").text(`${f1(eng)}%`);
  renderMap(); renderAge(); renderWatch(); renderDep();
}

function renderMap() {
  const k = state.ind, wrap = document.getElementById("map"), w = wrap.clientWidth, h = wrap.clientHeight;
  d3.select("#open-council").attr("href", `./areas?council=${state.hover || state.sel}`);
  const svg = d3.select(wrap).select("svg").attr("viewBox", `0 0 ${w} ${h}`);
  const proj = d3.geoMercator().fitExtent([[10, 10], [w - 10, h - 70]], HEX);
  const path = d3.geoPath(proj), col = colour();
  const sel = state.hover || state.sel;

  svg.selectAll("path.hex").data(HEX.features, d => d.properties.lad24cd).join("path")
    .attr("class", d => "hex" + (d.properties.lad24cd === sel ? " sel" : ""))
    .attr("d", path)
    .attr("fill", d => { const v = byCode.get(d.properties.lad24cd)?.[k]; return v == null ? NO_DATA : col(v); })
    .on("mouseenter", (e, d) => { state.hover = d.properties.lad24cd; renderMap(); })
    .on("mouseleave", () => { state.hover = null; renderMap(); })
    .on("click", (e, d) => { state.sel = d.properties.lad24cd; state.hover = null; render(); })
    .filter(d => d.properties.lad24cd === sel).raise();

  // Callout + leader line, kept inside the card
  const f = HEX.features.find(d => d.properties.lad24cd === sel), c = byCode.get(sel);
  const [cx, cy] = path.centroid(f);
  const box = document.getElementById("callout");
  const rank = eligible().sort((a, b) => b[k] - a[k]).findIndex(x => x.lad24cd === sel);
  const delta = c[k] - D.england[k];
  box.innerHTML = `<div class="n">${c.lad24nm}</div><div class="r">${c.region_name} · ${fInt(c.n_homes)} social homes</div>
    <div class="v">${c[k] == null ? "–" : f1(c[k]) + "%"}</div>
    <div class="d ${delta >= 0 ? "up" : "down"}">${delta >= 0 ? "+" : ""}${f1(delta)} pts vs England${rank >= 0 ? ` · #${rank + 1} of ${eligible().length}` : ""}</div>`;
  const bw = box.offsetWidth, bh = box.offsetHeight;
  let bx = cx + 40, by = cy - bh - 30;
  if (bx + bw > w - 8) bx = cx - bw - 40;
  if (by < 8) by = cy + 30;
  box.style.left = `${bx}px`; box.style.top = `${by}px`;
  const ax = bx > cx ? bx : bx + bw, ay = by > cy ? by : by + bh;
  svg.selectAll("line.lead").data([0]).join("line").attr("class", "lead")
    .attr("x1", cx).attr("y1", cy).attr("x2", ax).attr("y2", ay).attr("stroke", "#1B1D21").attr("stroke-width", 1.2);
  svg.selectAll("circle.lead").data([0]).join("circle").attr("class", "lead")
    .attr("cx", cx).attr("cy", cy).attr("r", 3.5).attr("fill", "#1B1D21");

  const dom = col.domain();
  d3.select("#leg-bar").selectAll("span").data(RAMP).join("span").style("background", d => d);
  d3.select("#leg-max").text(`${f1(dom[1])}%+`);
  d3.select("#leg-min").text(`${f1(dom[0])}%`);
  d3.select("#leg-bar").style("flex-direction", "row");
}

function renderAge() {
  const k = state.ind, rows = D.by_age, eng = D.england[k];
  const hi = d3.maxIndex(rows, r => r[k]), lo = d3.minIndex(rows, r => r[k]);
  d3.select("#age-title").text(`${AGE[rows[hi].age_band]} homes stand out`);
  d3.select("#age-sub").text(`% of social homes ${IND[k].phrase}, by construction age`);
  d3.select("#age-big").html(`${f1(rows[hi][k])}<small>%</small>`);
  d3.select("#age-cap").text(`of ${AGE[rows[hi].age_band].toLowerCase()} homes, vs ${f1(eng)}% overall`);

  const el = document.getElementById("age-chart"), w = el.clientWidth, h = el.clientHeight;
  const m = { t: 26, b: 26 };
  const x = d3.scaleBand().domain(rows.map(r => r.age_band)).range([0, w]).paddingInner(0.18);
  const y = d3.scaleLinear().domain([0, d3.max(rows, r => r[k]) * 1.08]).range([h - m.b, m.t]);
  const svg = d3.select(el).selectAll("svg").data([0]).join("svg").attr("viewBox", `0 0 ${w} ${h}`)
    .attr("role", "img").attr("aria-label", `Bar chart: ${IND[k].noun} by construction age`);
  const defs = svg.selectAll("defs").data([0]).join("defs");
  [["g-n", "#FFFFFF", "rgba(255,255,255,0.25)"], ["g-a", "#F07B2B", "rgba(240,123,43,0.12)"],
   ["g-c", "#8E9BF5", "rgba(142,155,245,0.12)"]].forEach(([id, a, b]) => {
    const g = defs.selectAll(`#${id}`).data([0]).join("linearGradient").attr("id", id).attr("x1", 0).attr("x2", 0).attr("y1", 0).attr("y2", 1);
    g.selectAll("stop").data([a, b]).join("stop").attr("offset", (d, i) => i).attr("stop-color", d => d);
  });
  const kind = i => i === hi ? "a" : i === lo ? "c" : "n";
  const edge = { a: "#F07B2B", c: "#8E9BF5", n: "#A3A8B0" };
  const g = svg.selectAll("g.b").data(rows, r => r.age_band).join(enter => {
    const g = enter.append("g").attr("class", "b");
    g.append("path").attr("class", "body"); g.append("rect").attr("class", "top");
    g.append("text").attr("class", "vlab").attr("text-anchor", "middle");
    g.append("text").attr("class", "xlab").attr("text-anchor", "middle");
    return g;
  });
  g.each(function (r, i) {
    const s = d3.select(this), bx = x(r.age_band), bw = x.bandwidth(), top = y(r[k]), base = h - m.b, rad = 8;
    const bh = Math.max(0, base - top);
    s.select("path.body").transition().duration(450)
      .attr("d", `M${bx},${base} V${top + rad} Q${bx},${top} ${bx + rad},${top} H${bx + bw - rad} Q${bx + bw},${top} ${bx + bw},${top + rad} V${base} Z`)
      .attr("fill", `url(#g-${kind(i)})`);
    s.select("rect.top").transition().duration(450).attr("x", bx + 4).attr("width", bw - 8).attr("y", top).attr("height", 2.5)
      .attr("rx", 1.25).attr("fill", edge[kind(i)]);
    s.select("text.vlab").transition().duration(450).attr("x", bx + bw / 2).attr("y", top - 9).text(`${f1(r[k])}%`)
      .style("fill", kind(i) === "a" ? "#B4530F" : kind(i) === "c" ? "#4C5BC7" : "#1B1D21");
    s.select("text.xlab").attr("x", bx + bw / 2).attr("y", h - 6).text(AGE[r.age_band]);
  });
  const ly = y(eng);
  svg.selectAll("line.avg").data([0]).join("line").attr("class", "avg").attr("x1", 0).attr("x2", w)
    .transition().duration(450).attr("y1", ly).attr("y2", ly)
    .attr("stroke", "#1B1D21").attr("stroke-dasharray", "3 4").attr("stroke-width", 1).attr("opacity", 0.45);
  svg.selectAll("text.avg").data([0]).join("text").attr("class", "avg xlab").attr("text-anchor", "end")
    .transition().duration(450).attr("x", w).attr("y", ly - 6).text(`England ${f1(eng)}%`);
}

function renderWatch() {
  const k = state.ind, col = colour(), eng = D.england[k];
  const hexPath = "M17 2 L30 9.5 L30 24.5 L17 32 L4 24.5 L4 9.5 Z";
  const rows = d3.select("#rows").selectAll("button.row").data(top5(), c => c.lad24cd).join(enter => {
    const b = enter.append("button").attr("class", "row");
    b.append("svg").attr("class", "hexicon").attr("viewBox", "0 0 34 34").append("path").attr("d", hexPath);
    const mid = b.append("div"); mid.append("div").attr("class", "n"); mid.append("div").attr("class", "r");
    const right = b.append("div"); right.append("div").attr("class", "v"); right.append("div").attr("class", "dd");
    return b;
  });
  rows.order().classed("sel", c => c.lad24cd === state.sel)
    .attr("aria-pressed", c => c.lad24cd === state.sel)
    .on("click", (e, c) => { state.sel = c.lad24cd; render(); })
    .on("mouseenter", (e, c) => { state.hover = c.lad24cd; renderMap(); })
    .on("mouseleave", () => { state.hover = null; renderMap(); });
  rows.select("svg path").attr("fill", c => col(c[k]));
  rows.select(".n").text(c => c.lad24nm);
  rows.select(".r").text(c => `${c.region_name} · ${fInt(c.n_homes)} homes`);
  rows.select(".v").text(c => `${f1(c[k])}%`);
  rows.select(".dd").text(c => `+${f1(c[k] - eng)} pts`);
}

function renderDep() {
  const k = state.ind, rows = D.by_decile, el = document.getElementById("dep-chart");
  const first = rows.find(r => r.decile === 1)[k], last = rows.find(r => r.decile === 10)[k];
  d3.select("#dep-big").text(`${f1(first)}%`);
  d3.select("#dep-cap").text(`in the most deprived 10% of neighbourhoods, vs ${f1(last)}% in the least deprived`);
  const w = el.clientWidth, h = el.clientHeight, m = { t: 6, b: 22 };
  const top3 = new Set([...rows].sort((a, b) => b[k] - a[k]).slice(0, 3).map(r => r.decile));
  const x = d3.scaleBand().domain(rows.map(r => r.decile)).range([0, w]).paddingInner(0.28);
  const lo = d3.min(rows, r => r[k]) * 0.7;
  const y = d3.scaleLinear().domain([lo, d3.max(rows, r => r[k])]).range([h - m.b, m.t]);
  const svg = d3.select(el).selectAll("svg").data([0]).join("svg").attr("viewBox", `0 0 ${w} ${h}`)
    .attr("role", "img").attr("aria-label", `Bar chart: ${IND[k].noun} by deprivation decile`);
  svg.selectAll("rect.d").data(rows, r => r.decile).join("rect").attr("class", "d").attr("rx", 6)
    .attr("x", r => x(r.decile)).attr("width", x.bandwidth())
    .transition().duration(450).attr("y", r => y(r[k])).attr("height", r => h - m.b - y(r[k]))
    .attr("fill", r => top3.has(r.decile) ? "#F07B2B" : "#C9CDD3");
  svg.selectAll("title").remove();
  svg.selectAll("rect.d").append("title").text(r => `Decile ${r.decile}: ${f1(r[k])}%`);
  svg.selectAll("text.e").data([[1, "Most deprived", "start"], [10, "Least", "end"]]).join("text").attr("class", "e xlab")
    .attr("x", d => d[0] === 1 ? x(1) : x(10) + x.bandwidth()).attr("y", h - 4).attr("text-anchor", d => d[2]).text(d => d[1]);
}

/** Mount the page onto the markup in index.md. `invalidation` (from Framework) tidies up on reload. */
export function mountOverview(data, hex, invalidation) {
  mountRail("overview");
  D = data; HEX = hex;
  state = { ind: "risk", sel: null, hover: null };
  byCode = new Map(D.councils.map(c => [c.lad24cd, c]));
  d3.select("#councils").selectAll("option").data(D.councils.map(c => c.lad24nm).sort()).join("option").attr("value", d => d);
  d3.select("#search").on("change", function () {
    const c = D.councils.find(c => c.lad24nm.toLowerCase() === this.value.trim().toLowerCase());
    if (c) { state.sel = c.lad24cd; render(); }
  });
  d3.select("#seg").selectAll("button").data(Object.keys(IND)).join("button")
    .text(k => IND[k].short).on("click", (e, k) => { state.ind = k; state.sel = null; render(); });
  const observer = new ResizeObserver(() => render());
  observer.observe(document.querySelector(".bento"));
  invalidation?.then(() => observer.disconnect());
  render();
}
