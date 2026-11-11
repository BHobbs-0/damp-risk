---
title: Deprivation
---

<div class="app">
<nav class="rail" id="rail" aria-label="Sections"></nav>
<div class="main">
<header class="page-head">
  <div class="titles">
    <div class="kicker">Damp risk atlas · Social housing in England</div>
    <h1>Deprivation</h1>
  </div>
  <div class="seg" role="group" aria-label="Indicator" id="seg"></div>
  <span class="status" title="Estimated from building characteristics, calibrated to published English Housing Survey damp rates"><span class="dot"></span>Estimated risk · calibrated to EHS</span>
</header>
<section class="bento">
  <article class="card dp-a" aria-labelledby="dec-title">
    <div class="card-head">
      <div><h2 id="dec-title">By deprivation decile</h2><div class="sub" id="dec-sub"></div></div>
      <span class="pill">IMD 2025</span>
    </div>
    <div class="chart grow" id="dec-chart"></div>
  </article>
  <article class="card dp-b" aria-labelledby="gap-title">
    <div class="card-head">
      <div><h2 id="gap-title"></h2><div class="sub">Most vs least deprived 10% of neighbourhoods</div></div>
    </div>
    <div class="gap">
      <div class="big"><span id="gap-big"></span><small> pts</small></div>
      <div class="big-cap" id="gap-cap"></div>
    </div>
    <div class="gap-pair">
      <div class="tile hl"><div class="l">Most deprived 10%</div><div class="v" id="gap-a"></div></div>
      <div class="tile"><div class="l">Least deprived 10%</div><div class="v" id="gap-b"></div></div>
    </div>
    <div class="big-cap" id="gap-peak" style="margin-top:12px"></div>
  </article>
  <article class="card dp-c" aria-labelledby="sc-title">
    <div class="card-head">
      <div><h2 id="sc-title">Every neighbourhood</h2><div class="sub" id="sc-sub"></div></div>
      <span class="pill"><span class="sw" style="background:var(--accent)"></span>Trend</span>
    </div>
    <div class="chart grow" id="sc-chart"><div class="tip" id="sc-tip"></div></div>
  </article>
  <article class="card dp-d" aria-labelledby="why-title">
    <div class="card-head">
      <div><h2 id="why-title">Why this matters</h2></div>
      <span class="pill">Context</span>
    </div>
    <div class="prose">
      <p>Damp and mould harm health, especially for children and older people. Households in deprived areas are also less able to heat their homes, and under-heating makes condensation worse.</p>
      <p>Where poor building conditions cluster in deprived neighbourhoods, the risks compound.</p>
      <p><b>After modelling</b>, this page will show <b>estimated damp risk</b> by decile, and how concentrated predicted cases are in the most deprived areas.</p>
    </div>
  </article>
</section>
<div class="foot">Deciles rank England's neighbourhoods (LSOAs) by the Index of Multiple Deprivation 2025; 1 = most deprived 10%. LSOAs and MSOAs with fewer than 10 social homes are excluded.</div>
</div>
</div>

```js
import {mountDeprivation} from "./components/deprivation.js";
const data = await FileAttachment("data/deprivation.json").json();
mountDeprivation(data, invalidation);
```
