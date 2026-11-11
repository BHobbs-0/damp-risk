---
title: Method
---

<div class="app">
<nav class="rail" id="rail" aria-label="Sections"></nav>
<div class="main">
<header class="page-head">
  <div class="titles">
    <div class="kicker">Damp risk atlas · Social housing in England</div>
    <h1>How it works</h1>
  </div>
  <span class="status" title="Estimated from building characteristics, calibrated to published English Housing Survey damp rates"><span class="dot"></span>Estimated risk · calibrated to EHS</span>
</header>
<section class="bento">
  <article class="card me-a" aria-labelledby="steps-title">
    <div class="card-head">
      <div><h2 id="steps-title">Approach</h2><div class="sub">Calibrate a model to published survey damp rates, then apply it to every social home</div></div>
      <span class="pill">5 steps</span>
    </div>
    <div class="steps">
      <div class="step on"><span class="num">1</span><div><b>Prepare 2.86m EPC records</b><br><span class="big-cap">Latest certificate per home, social rented, England; 99.98% placed in a neighbourhood.</span></div></div>
      <div class="step on"><span class="num">2</span><div><b>Collect published damp rates</b><br><span class="big-cap">English Housing Survey damp rates for social homes by age, type, floor area and energy rating (2023–24). Survey microdata access was declined, so only open, published figures are used.</span></div></div>
      <div class="step on"><span class="num">3</span><div><b>Calibrate a logistic model</b><br><span class="big-cap">Choose coefficients so that, applied to the real mix of homes, the model reproduces every published rate at once. Overlapping effects (old homes are often poorly rated) aren't double-counted.</span></div></div>
      <div class="step on"><span class="num">4</span><div><b>Score and aggregate</b><br><span class="big-cap" id="me-score">Estimate risk for every home, then summarise by neighbourhood and council. No address-level results.</span></div></div>
      <div class="step on"><span class="num">5</span><div><b>Validate</b><br><span class="big-cap">Predict breakdowns the model never saw (region, deprivation) and leave each fitted breakdown out in turn.</span></div></div>
    </div>
  </article>
  <article class="card me-b" aria-labelledby="data-title">
    <div class="card-head">
      <div><h2 id="data-title">Data</h2><div class="sub">All open data, Open Government Licence v3.0</div></div>
      <span class="pill" id="me-latest"></span>
    </div>
    <table class="tbl">
      <tr><td>English Housing Survey damp tables (DA5101, DA5102)</td><td>Published damp rates for social homes, used to calibrate and validate</td></tr>
      <tr><td>Energy Performance Certificates, England</td><td id="me-homes">Social homes to score</td></tr>
      <tr><td>ONS postcode lookup and LSOA 2021 boundaries</td><td>Placing homes in neighbourhoods; maps</td></tr>
      <tr><td>English Indices of Deprivation 2025</td><td>Deprivation context and validation</td></tr>
    </table>
    <div class="tiles" id="me-stats"></div>
  </article>
  <article class="card me-c" aria-labelledby="perf-title">
    <div class="card-head">
      <div><h2 id="perf-title">How well it works</h2><div class="sub">Average error in percentage points</div></div>
      <span class="pill">Validation</span>
    </div>
    <div class="tiles two" id="me-perf"></div>
  </article>
  <article class="card me-d" aria-labelledby="lim-title">
    <div class="card-head">
      <div><h2 id="lim-title">Limitations</h2><div class="sub">What the estimates can't tell you</div></div>
    </div>
    <div class="prose">
      <ul>
        <li><b>Risk indicator, not diagnosis.</b> Buildings only: occupancy, heating habits, leaks and repairs aren't in the EPC.</li>
        <li><b>Regional gaps</b> beyond buildings (e.g. the East of England's lower rate) aren't captured.</li>
        <li><b>Additive effects</b>, no interactions; categories matched approximately.</li>
        <li><b>Coverage.</b> Homes without an EPC are missing; <span id="me-old"></span> of certificates pre-date 2015.</li>
      </ul>
    </div>
  </article>
</section>
<div class="foot">Contains public sector information licensed under the Open Government Licence v3.0 · Contains OS data © Crown copyright and database right · Royal Mail data © Royal Mail copyright and database right</div>
</div>
</div>

```js
import {mountRail, fInt} from "./components/common.js";
const m = await FileAttachment("data/method.json").json();
const v = m.validation;
mountRail("method");
document.getElementById("me-homes").textContent = `${fInt(m.n_homes)} social homes to score`;
document.getElementById("me-old").textContent = `${m.pct_cert_before_2015}%`;
document.getElementById("me-latest").textContent = `Certificates to ${m.latest_certificate}`;
document.getElementById("me-score").textContent =
  `Estimate risk for all ${fInt(m.n_homes)} homes (average ${m.risk}%, about ${fInt(Math.round(m.expected_cases))} homes), then summarise by neighbourhood and council. No address-level results.`;
document.getElementById("me-stats").innerHTML = [
  ["Social homes", `${(m.n_homes / 1e6).toFixed(2)}m`, "latest EPC per home"],
  ["Placed in a neighbourhood", "99.98%", "via postcode"],
  ["Neighbourhoods", fInt(m.n_msoas), `across ${m.n_las} councils`],
  ["Certificates before 2015", `${m.pct_cert_before_2015}%`, "may miss later retrofit"],
].map(([l, val, s]) => `<div class="tile"><div class="l">${l}</div><div class="v" style="font-size:28px">${val}</div><div class="s">${s}</div></div>`).join("");
const loo = ["age", "type", "area", "eer"].map(f => v[`leave_out_${f}`]);
const beats = loo.filter(x => x.mae_pts < x.baseline_mae_pts).length;
document.getElementById("me-perf").innerHTML = [
  ["Fit to published rates", `${v.fit.mae_pts}`, `${v.fit.categories} rates · baseline ${v.fit.baseline_mae_pts}`],
  ["Leave one out", `${beats} of ${loo.length}`, "beat the baseline"],
  ["Deprivation, unseen", `${v.held_out_imd_decile.mae_pts}`, `noise floor ${v.held_out_imd_decile.noise_floor_mae_pts}`],
  ["Region, unseen", `${v.held_out_region.mae_pts}`, `noise floor ~${v.held_out_region.noise_floor_mae_pts}`],
].map(([l, val, s]) => `<div class="tile"><div class="l">${l}</div><div class="v">${val}</div><div class="s">${s}</div></div>`).join("");
```
