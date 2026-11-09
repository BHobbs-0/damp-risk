---
title: Overview
---

<div class="app">
  <nav class="rail" aria-label="Sections">
    <div class="logo" aria-hidden="true">
      <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z"/></svg>
    </div>
    <a class="on" href="./" aria-current="page" title="Overview"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="9" rx="2"/><rect x="14" y="3" width="7" height="5" rx="2"/><rect x="14" y="12" width="7" height="9" rx="2"/><rect x="3" y="16" width="7" height="5" rx="2"/></svg><span class="sr">Overview</span></a>
    <a aria-disabled="true" title="Areas (coming soon)"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2-6-2z"/><path d="M9 4v14M15 6v14"/></svg><span class="sr">Areas</span></a>
    <a aria-disabled="true" title="Drivers (coming soon)"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/></svg><span class="sr">Drivers</span></a>
    <a aria-disabled="true" title="Deprivation (coming soon)"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v18M5 7h14M5 7l-3 7a4 4 0 0 0 6 0L5 7zM19 7l-3 7a4 4 0 0 0 6 0l-3-7z"/></svg><span class="sr">Deprivation</span></a>
    <a aria-disabled="true" title="Method (coming soon)"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 2 3h10a2 2 0 0 0 2-3l-5-9V3"/></svg><span class="sr">Method</span></a>
  </nav>
  <div class="main">
    <header class="page-head">
      <div class="titles">
        <div class="kicker">Damp risk atlas · Social housing in England</div>
        <h1>Overview</h1>
      </div>
      <div class="seg" role="group" aria-label="Indicator" id="seg"></div>
      <label class="search">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
        <span class="sr">Search councils</span>
        <input id="search" list="councils" placeholder="Search councils…" autocomplete="off">
        <datalist id="councils"></datalist>
      </label>
      <span class="status" title="Areas are described by EPC building indicators until the damp model is trained"><span class="dot"></span>Building indicators · model coming</span>
    </header>
    <section class="bento">
      <article class="card hero" aria-labelledby="map-title">
        <div class="card-head">
          <div><h2 id="map-title">Where it's most common</h2><div class="sub" id="map-sub"></div></div>
          <span class="pill" id="map-pill">296 councils</span>
        </div>
        <div class="map-wrap" id="map">
          <svg role="img" aria-label="Hex map of English councils"></svg>
          <div class="callout" id="callout" aria-live="polite"></div>
          <div class="chip"><div class="l">England average</div><div class="v" id="eng-avg"></div></div>
          <div class="legend"><span id="leg-max"></span><div class="bar" id="leg-bar"></div><span id="leg-min"></span></div>
        </div>
      </article>
      <article class="card age" aria-labelledby="age-title">
        <div class="card-head">
          <div><h2 id="age-title"></h2><div class="sub" id="age-sub"></div></div>
          <div style="display:flex;gap:6px">
            <span class="pill"><span class="sw" style="background:var(--accent)"></span>Highest</span>
            <span class="pill"><span class="sw" style="background:var(--cool)"></span>Lowest</span>
          </div>
        </div>
        <div class="age-body">
          <div class="age-left">
            <div><div class="big" id="age-big"></div><div class="big-cap" id="age-cap"></div></div>
            <a class="pill" aria-disabled="true" style="align-self:flex-start">Explore drivers <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M7 17 17 7M8 7h9v9"/></svg></a>
          </div>
          <div class="chart" id="age-chart"></div>
        </div>
      </article>
      <article class="card watch" aria-labelledby="watch-title">
        <div class="card-head">
          <div><h2 id="watch-title">Watch list</h2><div class="sub">Councils with 500+ social homes</div></div>
          <span class="pill">Top 5</span>
        </div>
        <div class="rows" id="rows"></div>
      </article>
      <article class="card dep" aria-labelledby="dep-title">
        <div class="card-head">
          <div><h2 id="dep-title">Deprivation</h2><div class="sub">By neighbourhood deprivation (IMD 2025 decile)</div></div>
          <span class="pill">10 deciles</span>
        </div>
        <div class="dep-top">
          <div><div class="big" id="dep-big" style="font-size:38px"></div><div class="big-cap" id="dep-cap"></div></div>
        </div>
        <div class="chart" id="dep-chart"></div>
      </article>
    </section>
    <div class="foot">Social rented homes in England with an EPC (latest per home) · Contains public sector information licensed under the OGL v3.0 · Contains OS data © Crown copyright and database right</div>
  </div>
</div>

```js
import {mountOverview} from "./components/overview.js";
const data = await FileAttachment("data/overview.json").json();
const hex = await FileAttachment("data/la_hex.json").json();
mountOverview(data, hex, invalidation);
```
