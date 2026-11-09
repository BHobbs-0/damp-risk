// Deprivation page: indicators across IMD 2025 deciles (average + middle 50% of neighbourhoods),
// headline gap, and a scatter of every MSOA (deprivation score vs indicator) with a trend line.
import * as d3 from "npm:d3@7.9.2";
import {C, IND, f1, fInt, indicatorSwitch, mountRail, onResize, pct, rowsFromColumns} from "./common.js";

let D, M, state;

function render() {
  indicatorSwitch("#seg", state.ind, k => { state.ind = k; render(); });
  renderDeciles(); renderGap(); renderScatter();
}

function renderDeciles() {
  const k = state.ind, rows = D.by_decile, el = document.getElementById("dec-chart");
  const w = el.clientWidth, h = el.clientHeight, m = {t: 24, b: 40, l: 34};
  const top3 = new Set([...rows].sort((a, b) => b[k] - a[k]).slice(0, 3).map(r => r.decile));
  const x = d3.scaleBand().domain(rows.map(r => r.decile)).range([m.l, w]).paddingInner(0.35);
  const y = d3.scaleLinear().domain([0, d3.max(rows, r => r[`${k}_q3`]) * 1.12]).nice().range([h - m.b, m.t]);
  const svg = d3.select(el).selectAll("svg").data([0]).join("svg").attr("viewBox", `0 0 ${w} ${h}`)
    .attr("role", "img").attr("aria-label", `${IND[k].noun} by deprivation decile`);

  svg.selectAll("g.yax").data([0]).join("g").attr("class", "yax")
    .call(g => g.selectAll("line").data(y.ticks(4)).join("line").attr("x1", m.l).attr("x2", w)
      .attr("y1", d => y(d)).attr("y2", d => y(d)).attr("stroke", "rgba(27,29,33,.06)"))
    .call(g => g.selectAll("text").data(y.ticks(4)).join("text").attr("class", "xlab").attr("x", 0)
      .attr("y", d => y(d) + 4).text(d => `${d}%`));

  svg.selectAll("rect.iqr").data(rows, r => r.decile).join("rect").attr("class", "iqr").attr("rx", 10)
    .attr("x", r => x(r.decile)).attr("width", x.bandwidth())
    .attr("fill", r => top3.has(r.decile) ? "rgba(240,123,43,.16)" : "rgba(255,255,255,.75)")
    .attr("stroke", r => top3.has(r.decile) ? "rgba(240,123,43,.35)" : "rgba(27,29,33,.08)")
    .transition().duration(450).attr("y", r => y(r[`${k}_q3`])).attr("height", r => y(r[`${k}_q1`]) - y(r[`${k}_q3`]));

  const line = d3.line().x(r => x(r.decile) + x.bandwidth() / 2).y(r => y(r[k])).curve(d3.curveMonotoneX);
  svg.selectAll("path.mean").data([rows]).join("path").attr("class", "mean").attr("fill", "none")
    .attr("stroke", C.text).attr("stroke-width", 1.5).attr("opacity", .55).transition().duration(450).attr("d", line);
  svg.selectAll("circle.mean").data(rows, r => r.decile).join("circle").attr("class", "mean").attr("r", 6)
    .attr("stroke", "#fff").attr("stroke-width", 2).attr("cx", r => x(r.decile) + x.bandwidth() / 2)
    .attr("fill", r => top3.has(r.decile) ? C.accent : "#8A9099")
    .transition().duration(450).attr("cy", r => y(r[k]));
  svg.selectAll("text.vlab").data(rows, r => r.decile).join("text").attr("class", "vlab").attr("text-anchor", "middle")
    .attr("x", r => x(r.decile) + x.bandwidth() / 2)
    .style("fill", r => top3.has(r.decile) ? C.accentText : C.text)
    .transition().duration(450).attr("y", r => y(r[`${k}_q3`]) - 8).text(r => `${f1(r[k])}%`);
  svg.selectAll("text.dx").data(rows, r => r.decile).join("text").attr("class", "dx xlab").attr("text-anchor", "middle")
    .attr("x", r => x(r.decile) + x.bandwidth() / 2).attr("y", h - 20).text(r => r.decile);
  svg.selectAll("text.ends").data([[1, "Most deprived"], [10, "Least deprived"]]).join("text").attr("class", "ends xlab")
    .attr("text-anchor", d => d[0] === 1 ? "start" : "end").attr("y", h - 3)
    .attr("x", d => d[0] === 1 ? x(1) : x(10) + x.bandwidth()).text(d => d[1]);
  d3.select("#dec-sub").text(`% of social homes ${IND[k].phrase} · dot: average · band: middle 50% of neighbourhoods`);
}

function renderGap() {
  const k = state.ind, rows = D.by_decile, first = rows[0][k], last = rows[9][k];
  const peak = rows.reduce((a, b) => (b[k] > a[k] ? b : a));
  const gap = first - last;
  d3.select("#gap-big").text(`${gap >= 0 ? "+" : ""}${f1(gap)}`);
  d3.select("#gap-cap").text(gap >= 0
    ? `points higher in the most deprived 10% of neighbourhoods than the least deprived`
    : `points lower in the most deprived 10% of neighbourhoods than the least deprived`);
  d3.select("#gap-a").text(pct(first)); d3.select("#gap-b").text(pct(last));
  d3.select("#gap-peak").html(`Highest in decile <b>${peak.decile}</b> (${pct(peak[k])})`);
  d3.select("#gap-title").text(gap >= 0 ? "Worse where deprivation is higher" : "Worse in less deprived areas");
}

function renderScatter() {
  const k = state.ind, el = document.getElementById("sc-chart"), w = el.clientWidth, h = el.clientHeight;
  const m = {t: 10, r: 8, b: 28, l: 34};
  const pts = M.filter(d => d[k] != null);
  const x = d3.scaleLinear().domain([d3.max(pts, d => d.imd), 0]).nice().range([m.l, w - m.r]); // most deprived on the left
  const y = d3.scaleLinear().domain([0, d3.quantile(pts.map(d => d[k]).sort(d3.ascending), 0.995)]).nice()
    .range([h - m.b, m.t]).clamp(true);
  const svg = d3.select(el).selectAll("svg").data([0]).join("svg").attr("viewBox", `0 0 ${w} ${h}`)
    .attr("role", "img").attr("aria-label", `Neighbourhoods: deprivation score against ${IND[k].noun}`);

  svg.selectAll("g.grid").data([0]).join("g").attr("class", "grid")
    .call(g => g.selectAll("line").data(y.ticks(4)).join("line").attr("x1", m.l).attr("x2", w - m.r)
      .attr("y1", d => y(d)).attr("y2", d => y(d)).attr("stroke", "rgba(27,29,33,.06)"))
    .call(g => g.selectAll("text").data(y.ticks(4)).join("text").attr("class", "xlab").attr("x", 0)
      .attr("y", d => y(d) + 4).text(d => `${d}%`));
  svg.selectAll("circle.pt").data(pts, d => d.name).join("circle").attr("class", "pt").attr("r", 2)
    .attr("fill", "#8A9099").attr("opacity", .28).attr("cx", d => x(d.imd)).attr("cy", d => y(d[k]));

  // Trend: average within 25 equal-count bins of deprivation score
  const sorted = [...pts].sort((a, b) => b.imd - a.imd), size = Math.ceil(sorted.length / 25);
  const bins = d3.range(0, sorted.length, size).map(i => {
    const b = sorted.slice(i, i + size);
    return {imd: d3.mean(b, d => d.imd), v: d3.sum(b, d => d[k] * d.n_homes) / d3.sum(b, d => d.n_homes)};
  });
  svg.selectAll("path.trend").data([bins]).join("path").attr("class", "trend").attr("fill", "none")
    .attr("stroke", C.accent).attr("stroke-width", 3).attr("stroke-linecap", "round")
    .attr("d", d3.line().x(d => x(d.imd)).y(d => y(d.v)).curve(d3.curveBasis));
  svg.selectAll("text.ax").data([[m.l, "Most deprived", "start"], [w - m.r, "Least deprived", "end"]]).join("text")
    .attr("class", "ax xlab").attr("x", d => d[0]).attr("y", h - 6).attr("text-anchor", d => d[2]).text(d => d[1]);

  // Hover: nearest neighbourhood via Delaunay
  const delaunay = d3.Delaunay.from(pts, d => x(d.imd), d => y(d[k]));
  const tip = d3.select("#sc-tip");
  svg.on("mousemove", e => {
    const [mx, my] = d3.pointer(e), d = pts[delaunay.find(mx, my)];
    svg.selectAll("circle.hl").data([d]).join("circle").attr("class", "hl").attr("r", 5).attr("fill", C.accent)
      .attr("stroke", "#fff").attr("stroke-width", 2).attr("cx", x(d.imd)).attr("cy", y(d[k]));
    tip.style("display", "block").style("left", `${Math.min(x(d.imd) + 12, w - 180)}px`).style("top", `${Math.max(y(d[k]) - 50, 0)}px`)
      .html(`<b>${d.name}</b><br>${pct(d[k])} · ${fInt(d.n_homes)} homes · IMD score ${f1(d.imd)}`);
  }).on("mouseleave", () => { svg.selectAll("circle.hl").remove(); tip.style("display", "none"); });
  d3.select("#sc-sub").text(`${fInt(pts.length)} neighbourhoods · line: trend across deprivation`);
}

export function mountDeprivation(data, invalidation) {
  mountRail("deprivation");
  D = data; M = rowsFromColumns(data.msoas);
  state = {ind: "pct_wall_uninsulated"};
  onResize(document.querySelector(".bento"), render, invalidation);
  render();
}
