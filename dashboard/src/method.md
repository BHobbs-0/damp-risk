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
  <span class="status" title="Areas are described by EPC building indicators until the damp model is trained"><span class="dot"></span>Building indicators · model coming</span>
</header>
<section class="bento">
  <article class="card me-a" aria-labelledby="steps-title">
    <div class="card-head">
      <div><h2 id="steps-title">Approach</h2><div class="sub">Learn from homes surveyors inspected, then apply it to every social home</div></div>
      <span class="pill">5 steps</span>
    </div>
    <div class="steps">
      <div class="step on"><span class="num">1</span><div><b>Prepare 2.86m EPC records</b><br><span class="big-cap">Latest certificate per home, social rented, England; 99.98% placed in a neighbourhood. <span class="good">Done</span></span></div></div>
      <div class="step"><span class="num">2</span><div><b>Train on the English Housing Survey</b><br><span class="big-cap">Surveyors record damp. Use only features in both datasets: dwelling type, age, wall and roof insulation, glazing, heating, energy efficiency, floor area, region.</span></div></div>
      <div class="step"><span class="num">3</span><div><b>Calibrate</b><br><span class="big-cap">Adjust probabilities so averages over an area mean what they say.</span></div></div>
      <div class="step"><span class="num">4</span><div><b>Score and aggregate</b><br><span class="big-cap">Estimate risk for every home, then summarise by neighbourhood and council. No address-level results.</span></div></div>
      <div class="step"><span class="num">5</span><div><b>Validate</b><br><span class="big-cap">Check predicted rates against published survey figures (7% of social homes had damp in 2024).</span></div></div>
    </div>
  </article>
  <article class="card me-b" aria-labelledby="data-title">
    <div class="card-head">
      <div><h2 id="data-title">Data</h2><div class="sub">All public; survey microdata under the UK Data Service End User Licence</div></div>
      <span class="pill" id="me-latest"></span>
    </div>
    <table class="tbl">
      <tr><td>English Housing Survey: housing stock data</td><td>Training labels (surveyor-recorded damp) and features</td></tr>
      <tr><td>Energy Performance Certificates, England</td><td id="me-homes">Social homes to score</td></tr>
      <tr><td>ONS postcode lookup and LSOA 2021 boundaries</td><td>Placing homes in neighbourhoods; maps</td></tr>
      <tr><td>English Indices of Deprivation 2025</td><td>Deprivation context</td></tr>
    </table>
    <div class="tiles" id="me-stats"></div>
  </article>
  <article class="card me-c" aria-labelledby="perf-title">
    <div class="card-head">
      <div><h2 id="perf-title">Model performance</h2><div class="sub">Baseline vs logistic regression vs LightGBM</div></div>
      <span class="pill">Week 2</span>
    </div>
    <div class="tiles two">
      <div class="tile"><div class="l">PR-AUC</div><div class="v">–</div><div class="s">Headline metric</div></div>
      <div class="tile"><div class="l">Top-10% capture</div><div class="v">–</div><div class="s">Damp cases found</div></div>
      <div class="tile"><div class="l">ROC-AUC</div><div class="v">–</div><div class="s">For comparison</div></div>
      <div class="tile"><div class="l">Brier score</div><div class="v">–</div><div class="s">Calibration</div></div>
    </div>
  </article>
  <article class="card me-d" aria-labelledby="lim-title">
    <div class="card-head">
      <div><h2 id="lim-title">Limitations</h2><div class="sub">What the estimates can't tell you</div></div>
    </div>
    <div class="prose">
      <ul>
        <li><b>A risk indicator, not a diagnosis.</b> Building characteristics only; occupancy, heating habits, overcrowding, leaks and repair condition aren't in the EPC.</li>
        <li><b>Coverage.</b> Homes without an EPC, or without tenure recorded, are missing; <span id="me-old"></span> of certificates pre-date 2015.</li>
        <li><b>Harmonisation.</b> EPC and survey categories don't align exactly (e.g. age bands).</li>
        <li><b>Area-level only.</b> No addresses; areas with fewer than 10 homes are hidden.</li>
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
mountRail("method");
document.getElementById("me-homes").textContent = `${fInt(m.n_homes)} social homes to score`;
document.getElementById("me-old").textContent = `${m.pct_cert_before_2015}%`;
document.getElementById("me-latest").textContent = `Certificates to ${m.latest_certificate}`;
document.getElementById("me-stats").innerHTML = [
  ["Social homes", `${(m.n_homes / 1e6).toFixed(2)}m`, "latest EPC per home"],
  ["Placed in a neighbourhood", "99.98%", "via postcode"],
  ["Neighbourhoods", fInt(m.n_msoas), `across ${m.n_las} councils`],
  ["Certificates before 2015", `${m.pct_cert_before_2015}%`, "may miss later retrofit"],
].map(([l, v, s]) => `<div class="tile"><div class="l">${l}</div><div class="v" style="font-size:28px">${v}</div><div class="s">${s}</div></div>`).join("");
```
