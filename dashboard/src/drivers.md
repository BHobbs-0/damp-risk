---
title: Drivers
---

<div class="app">
<nav class="rail" id="rail" aria-label="Sections"></nav>
<div class="main">
<header class="page-head">
  <div class="titles">
    <div class="kicker">Damp risk atlas · Social housing in England</div>
    <h1>What drives damp?</h1>
  </div>
  <div class="seg" role="group" aria-label="Indicator" id="seg"></div>
  <span class="status" title="Estimated from building characteristics, calibrated to published English Housing Survey damp rates"><span class="dot"></span>Estimated risk · calibrated to EHS</span>
</header>
<section class="bento">
  <article class="card dr-a" aria-labelledby="ehs-title">
    <div class="card-head">
      <div><h2 id="ehs-title">What surveyors find</h2><div class="sub">% of homes with damp, by building characteristic · English Housing Survey 2023, all tenures</div></div>
      <span class="pill">Published</span>
    </div>
    <div class="gap">
      <div class="big"><span id="ehs-big"></span></div>
      <div class="big-cap">of social rented homes had a damp problem in 2024, recorded by trained surveyors</div>
    </div>
    <div class="chart grow" id="ehs-chart"></div>
    <div class="big-cap">Simple comparisons that don't control for other factors. The model will measure each one's effect while accounting for the others.</div>
  </article>
  <article class="card dr-b" aria-labelledby="age-title">
    <div class="card-head">
      <div><h2 id="age-title"></h2><div class="sub" id="age-sub"></div></div>
      <div style="display:flex;gap:6px">
        <span class="pill"><span class="sw" style="background:var(--accent)"></span>Highest</span>
        <span class="pill"><span class="sw" style="background:var(--cool)"></span>Lowest</span>
      </div>
    </div>
    <div class="chart grow" id="age-chart"></div>
  </article>
  <article class="card dr-c" aria-labelledby="on-title">
    <div class="card-head">
      <div><h2 id="on-title">Oldest vs newest</h2><div class="sub">Bar: pre-1919 homes · line: post-1990 homes</div></div>
    </div>
    <div class="cmps" id="oldnew"></div>
  </article>
  <article class="card dr-d" aria-labelledby="eff-title">
    <div class="card-head">
      <div><h2 id="eff-title">What the model learned</h2><div class="sub">Odds of damp vs a typical home, each effect net of the others</div></div>
      <span class="pill">Model</span>
    </div>
    <div class="effects" id="effects"></div>
  </article>
</section>
<div class="foot">Source for survey rates: English Housing Survey 2023 to 2024, Drivers and impacts of housing quality; 2024 to 2025 headline report · Building indicators: EPC register, social rented homes</div>
</div>
</div>

```js
import {mountDrivers} from "./components/drivers.js";
const data = await FileAttachment("data/drivers.json").json();
mountDrivers(data, invalidation);
```
