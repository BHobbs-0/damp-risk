---
title: Areas
---

<div class="app">
<nav class="rail" id="rail" aria-label="Sections"></nav>
<div class="main">
<header class="page-head">
  <div class="titles">
    <div class="kicker" id="council-meta">Damp risk atlas · Areas</div>
    <h1 id="council-name">Areas</h1>
  </div>
  <div class="seg" role="group" aria-label="Indicator" id="seg"></div>
  <label class="search">
    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
    <span class="sr">Choose a council</span>
    <input id="search" list="councils" placeholder="Choose a council…" autocomplete="off">
    <datalist id="councils"></datalist>
  </label>
  <span class="status" title="Estimated from building characteristics, calibrated to published English Housing Survey damp rates"><span class="dot"></span>Estimated risk · calibrated to EHS</span>
</header>
<section class="bento">
  <article class="card hero" aria-labelledby="map-title">
    <div class="card-head">
      <div><h2 id="map-title">Neighbourhoods</h2><div class="sub" id="map-sub"></div></div>
      <span class="pill">MSOAs</span>
    </div>
    <div class="map-wrap" id="map">
      <svg role="img" aria-label="Map of the council's neighbourhoods"></svg>
      <div class="callout" id="callout" aria-live="polite"></div>
      <div class="chip"><div class="l">Council average</div><div class="v" id="council-avg"></div></div>
      <div class="legend"><span id="leg-max"></span><div class="bar" id="leg-bar"></div><span id="leg-min"></span></div>
    </div>
  </article>
  <article class="card age" aria-labelledby="tiles-title">
    <div class="card-head">
      <div><h2 id="tiles-title">Key figures</h2><div class="sub">Compared with all social homes in England</div></div>
      <span class="pill"><span class="sw" style="background:var(--accent)"></span>Above England</span>
    </div>
    <div class="rank-text" id="rank-text"></div>
    <div class="strip" id="strip"></div>
    <div class="tiles" id="tiles"></div>
  </article>
  <article class="card watch" aria-labelledby="cmp-title">
    <div class="card-head">
      <div><h2 id="cmp-title">Vs England</h2><div class="sub">Bar: this council · line: England</div></div>
    </div>
    <div class="cmps" id="compare"></div>
  </article>
  <article class="card dep" aria-labelledby="mix-title">
    <div class="card-head">
      <div><h2 id="mix-title">Housing mix</h2><div class="sub">% of social homes · line: England</div></div>
      <div class="seg sm" role="group" aria-label="Housing feature" id="mix-seg"></div>
    </div>
    <div class="cmps" id="mix"></div>
  </article>
</section>
<div class="foot">Neighbourhoods are Middle-layer Super Output Areas (MSOAs); those with fewer than 10 social homes are grey · Contains OS data © Crown copyright and database right</div>
</div>
</div>

```js
import {mountAreas} from "./components/areas.js";
const areas = await FileAttachment("data/areas.json").json();
const shapes = await FileAttachment("data/msoa_shapes.json").json();
mountAreas(areas, shapes, invalidation);
```
