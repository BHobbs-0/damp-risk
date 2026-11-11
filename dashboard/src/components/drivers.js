// Drivers page: published survey damp rates by building characteristic, EPC indicators by
// construction age, oldest vs newest homes, and what the model will add.
import * as d3 from "npm:d3@7.9.2";
import {AGE, C, IND, f1, indicatorSwitch, mountRail, onResize, pct, softBars} from "./common.js";

let D, state;

function render() {
  indicatorSwitch("#seg", state.ind, k => { state.ind = k; render(); });
  renderEhs(); renderAge(); renderOldNew(); renderEffects();
}

/** Diverging bars on a log scale around 1x: right/orange raises the odds, left/periwinkle lowers them. */
function renderEffects() {
  const rows = D.effects.slice(0, 7), lim = Math.log(2.5);
  const pos = r => 50 + (Math.max(-lim, Math.min(lim, Math.log(r.odds_ratio))) / lim) * 50;
  d3.select("#effects").selectAll("div.eff").data(rows).join("div").attr("class", "eff")
    .classed("up", r => r.odds_ratio > 1)
    .html(r => {
      const p = pos(r), left = Math.min(50, p), width = Math.abs(p - 50);
      return `<span class="lab"><b>${r.feature}</b> ${r.category}</span>
        <span class="track"><span class="mid"></span><span class="fill" style="left:${left}%;width:${width}%"></span></span>
        <span class="val">×${r.odds_ratio.toFixed(2)}</span>`;
    });
}

function renderEhs() {
  const el = document.getElementById("ehs-chart"), w = el.clientWidth, h = el.clientHeight;
  const rows = D.ehs.flatMap(g => {
    const worst = d3.max(g.items, d => d[1]);
    return [{type: "group", label: g.group}, ...g.items.map(([label, v]) => ({type: "bar", label, v, worst: v === worst}))];
  });
  const rowH = h / rows.length, labelW = Math.min(170, w * 0.36);
  const x = d3.scaleLinear().domain([0, 13]).range([labelW, w - 44]);
  const svg = d3.select(el).selectAll("svg").data([0]).join("svg").attr("viewBox", `0 0 ${w} ${h}`)
    .attr("role", "img").attr("aria-label", "Damp rate by building characteristic, English Housing Survey 2023");
  const g = svg.selectAll("g.r").data(rows).join(enter => {
    const g = enter.append("g").attr("class", "r");
    g.append("text").attr("class", "lab"); g.append("rect").attr("class", "bg"); g.append("rect").attr("class", "bar");
    g.append("text").attr("class", "val");
    return g;
  }).attr("transform", (d, i) => `translate(0,${i * rowH})`);
  g.select("text.lab").attr("x", d => d.type === "group" ? 0 : 14).attr("y", rowH * 0.62)
    .attr("font-size", d => d.type === "group" ? 13 : 12.5).attr("font-weight", d => d.type === "group" ? 600 : 400)
    .attr("fill", d => d.type === "group" ? C.text : C.muted).text(d => d.label);
  const bh = Math.min(16, rowH * 0.55);
  g.select("rect.bg").attr("x", labelW).attr("y", (rowH - bh) / 2).attr("height", bh).attr("rx", bh / 2)
    .attr("width", d => d.type === "bar" ? x(13) - labelW : 0).attr("fill", "rgba(27,29,33,.05)");
  g.select("rect.bar").attr("x", labelW).attr("y", (rowH - bh) / 2).attr("height", bh).attr("rx", bh / 2)
    .attr("fill", d => d.worst ? C.accent : "#B9BEC6").attr("width", d => d.type === "bar" ? x(d.v) - labelW : 0);
  g.select("text.val").attr("x", d => d.type === "bar" ? x(d.v) + 8 : 0).attr("y", rowH * 0.62).attr("font-size", 12.5)
    .attr("font-weight", 600).attr("fill", d => d.worst ? C.accentText : C.text).text(d => d.type === "bar" ? `${d.v}%` : "");
}

function renderAge() {
  const k = state.ind, rows = D.by_age, eng = D.england[k];
  const hi = rows.reduce((a, b) => (b[k] > a[k] ? b : a));
  d3.select("#age-title").text(`${AGE[hi.age_band]} homes stand out`);
  d3.select("#age-sub").text(`% of social homes ${IND[k].phrase}, by construction age (EPC)`);
  softBars(document.getElementById("age-chart"), rows.map(r => ({key: r.age_band, label: AGE[r.age_band], value: r[k]})),
    {reference: eng, referenceLabel: `England ${pct(eng)}`});
}

function renderOldNew() {
  const old = D.by_age.find(r => r.age_band === "pre1919"), neu = D.by_age.find(r => r.age_band === "post1990");
  const keys = Object.keys(IND), max = d3.max(keys, k => Math.max(old[k], neu[k])) * 1.08;
  d3.select("#oldnew").selectAll("div.cmp").data(keys).join("div").attr("class", "cmp")
    .classed("hl", k => old[k] > neu[k])
    .html(k => `<span class="lab">${IND[k].short}</span>
      <span class="track"><span class="fill" style="width:${(old[k] / max) * 100}%"></span>
      <span class="mark" style="left:${(neu[k] / max) * 100}%"></span></span>
      <span class="val">${pct(old[k])}</span>`);
}

export function mountDrivers(data, invalidation) {
  mountRail("drivers");
  D = data;
  state = {ind: "risk"};
  d3.select("#ehs-big").text(`${D.ehs_social_2024}%`);
  onResize(document.querySelector(".bento"), render, invalidation);
  render();
}
