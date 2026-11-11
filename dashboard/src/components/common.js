// Shared constants and building blocks for every dashboard page.
import * as d3 from "npm:d3@7.9.2";

export const IND = {
  risk: { short: "Damp risk", noun: "estimated damp risk", phrase: "are estimated to have damp",
          why: "Model estimate from building characteristics, calibrated to published survey damp rates" },
  pct_wall_uninsulated: { short: "Uninsulated walls", noun: "uninsulated walls", phrase: "have uninsulated walls",
                          why: "Damp is 2–3× as common with uninsulated walls" },
  pct_epc_efg: { short: "Rated E–G", noun: "rated EPC E–G", phrase: "are rated EPC E–G",
                 why: "Damp is ~4× as common in homes rated E–G" },
  pct_not_full_glazing: { short: "Single glazing", noun: "not fully double glazed", phrase: "aren't fully double glazed",
                          why: "Damp is twice as common without full double glazing" },
  pct_electric_heating: { short: "Electric heating", noun: "electric heating", phrase: "use electric heating",
                          why: "Electric heating is often costly to run" },
};
export const AGE = { "pre1919": "Pre-1919", "1919-1944": "1919–44", "1945-1964": "1945–64", "1965-1980": "1965–80",
                     "1981-1990": "1981–90", "post1990": "Post-1990" };
export const RAMP = ["#FBE7D7", "#F6C7A4", "#F0A06A", "#E07A35", "#B4530F"];
export const NO_DATA = "#D9DBE0";
export const C = { text: "#1B1D21", muted: "#5E636B", accent: "#F07B2B", accentText: "#B4530F",
                   cool: "#8E9BF5", coolText: "#4C5BC7", edge: "#A3A8B0", grey: "#C9CDD3" };
export const f1 = d3.format(".1f"), fInt = d3.format(",");
export const pct = v => v == null ? "–" : `${f1(v)}%`;

/** Turn {col: [values]} (compact JSON from the Python loaders) back into an array of row objects. */
export function rowsFromColumns(cols) {
  const keys = Object.keys(cols), n = cols[keys[0]].length;
  return Array.from({length: n}, (_, i) => Object.fromEntries(keys.map(k => [k, cols[k][i]])));
}

/** Quantized orange scale, capped at the 98th percentile so one extreme area doesn't wash out the rest. */
export function colourScale(values) {
  const v = values.filter(x => x != null).sort(d3.ascending);
  return d3.scaleQuantize().domain([v[0] ?? 0, d3.quantile(v, 0.98) ?? 1]).range(RAMP);
}

/** Indicator pill switch: renders buttons into `el` and calls onChange(key). */
export function indicatorSwitch(el, current, onChange, keys = Object.keys(IND)) {
  d3.select(el).selectAll("button").data(keys).join("button")
    .text(k => IND[k].short)
    .attr("aria-pressed", k => k === current)
    .on("click", (e, k) => onChange(k));
}

/** Left icon rail, shared by every page. */
const PAGES = [
  ["overview", "./", "Overview", '<rect x="3" y="3" width="7" height="9" rx="2"/><rect x="14" y="3" width="7" height="5" rx="2"/><rect x="14" y="12" width="7" height="9" rx="2"/><rect x="3" y="16" width="7" height="5" rx="2"/>'],
  ["areas", "./areas", "Areas", '<path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2-6-2z"/><path d="M9 4v14M15 6v14"/>'],
  ["drivers", "./drivers", "Drivers", '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>'],
  ["deprivation", "./deprivation", "Deprivation", '<path d="M12 3v18M5 7h14M5 7l-3 7a4 4 0 0 0 6 0L5 7zM19 7l-3 7a4 4 0 0 0 6 0l-3-7z"/>'],
  ["method", "./method", "Method", '<path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 2 3h10a2 2 0 0 0 2-3l-5-9V3"/>'],
];
export function mountRail(active) {
  const el = document.getElementById("rail");
  if (!el) return;
  el.innerHTML = `<div class="logo" aria-hidden="true"><svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z"/></svg></div>`
    + PAGES.map(([key, href, label, icon]) =>
      `<a href="${href}" title="${label}"${key === active ? ' class="on" aria-current="page"' : ""}>`
      + `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${icon}</svg>`
      + `<span class="sr">${label}</span></a>`).join("");
}

/**
 * Soft column bars in the house style: white bars with a grey top edge, the highest in orange and
 * the lowest in periwinkle, values labelled on top, and an optional dashed reference line.
 * rows: [{key, label, value}]
 */
export function softBars(el, rows, {reference = null, referenceLabel = "", highlight = true, suffix = "%"} = {}) {
  const w = el.clientWidth, h = el.clientHeight, m = {t: 26, b: 26};
  const hi = highlight ? d3.maxIndex(rows, r => r.value) : -1, lo = highlight ? d3.minIndex(rows, r => r.value) : -1;
  const x = d3.scaleBand().domain(rows.map(r => r.key)).range([0, w]).paddingInner(0.18);
  const y = d3.scaleLinear().domain([0, d3.max(rows, r => r.value) * 1.1 || 1]).range([h - m.b, m.t]);
  const svg = d3.select(el).selectAll("svg").data([0]).join("svg").attr("viewBox", `0 0 ${w} ${h}`);
  const defs = svg.selectAll("defs").data([0]).join("defs");
  [["g-n", "#FFFFFF", "rgba(255,255,255,0.25)"], ["g-a", C.accent, "rgba(240,123,43,0.12)"],
   ["g-c", C.cool, "rgba(142,155,245,0.12)"]].forEach(([id, a, b]) => {
    const g = defs.selectAll(`#${id}`).data([0]).join("linearGradient").attr("id", id).attr("x1", 0).attr("x2", 0).attr("y1", 0).attr("y2", 1);
    g.selectAll("stop").data([a, b]).join("stop").attr("offset", (d, i) => i).attr("stop-color", d => d);
  });
  const kind = i => i === hi ? "a" : i === lo ? "c" : "n";
  const edge = {a: C.accent, c: C.cool, n: C.edge}, ink = {a: C.accentText, c: C.coolText, n: C.text};
  const g = svg.selectAll("g.b").data(rows, r => r.key).join(enter => {
    const g = enter.append("g").attr("class", "b");
    g.append("path"); g.append("rect");
    g.append("text").attr("class", "vlab").attr("text-anchor", "middle");
    g.append("text").attr("class", "xlab").attr("text-anchor", "middle");
    return g;
  });
  g.each(function (r, i) {
    const s = d3.select(this), bx = x(r.key), bw = x.bandwidth(), top = y(r.value), base = h - m.b, rad = Math.min(8, bw / 3);
    s.select("path").transition().duration(450)
      .attr("d", `M${bx},${base} V${top + rad} Q${bx},${top} ${bx + rad},${top} H${bx + bw - rad} Q${bx + bw},${top} ${bx + bw},${top + rad} V${base} Z`)
      .attr("fill", `url(#g-${kind(i)})`);
    s.select("rect").transition().duration(450).attr("x", bx + 4).attr("width", Math.max(0, bw - 8)).attr("y", top)
      .attr("height", 2.5).attr("rx", 1.25).attr("fill", edge[kind(i)]);
    s.select("text.vlab").transition().duration(450).attr("x", bx + bw / 2).attr("y", top - 9)
      .text(`${f1(r.value)}${suffix}`).style("fill", ink[kind(i)]);
    s.select("text.xlab").attr("x", bx + bw / 2).attr("y", h - 6).text(r.label);
  });
  const refData = reference == null ? [] : [reference];
  svg.selectAll("line.avg").data(refData).join("line").attr("class", "avg").attr("x1", 0).attr("x2", w)
    .attr("y1", d => y(d)).attr("y2", d => y(d)).attr("stroke", C.text).attr("stroke-dasharray", "3 4").attr("opacity", 0.45);
  svg.selectAll("text.avg").data(refData).join("text").attr("class", "avg xlab").attr("text-anchor", "end")
    .attr("x", w).attr("y", d => y(d) - 6).text(referenceLabel);
  return svg;
}

/** Re-render on resize; disconnect when Framework re-runs the cell. */
export function onResize(target, render, invalidation) {
  const ro = new ResizeObserver(() => render());
  ro.observe(target);
  invalidation?.then(() => ro.disconnect());
}
