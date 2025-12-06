---
layout: page
title: Bernoulli Shift Map Visualization
description: Interactive visualization of the Bernoulli shift map demonstrating chaotic dynamics and sensitive dependence on initial conditions.
importance: 1
category: work
---

## Overview

This interactive visualization demonstrates the Bernoulli shift map. The map is defined by $$x_{t+1} = 2x_t \pmod 1,$$ which is equivalent to shifting the binary representation of a number one position to the right. This visualization shows how tiny perturbations in initial conditions lead to exponential divergence over time.

## Interactive Demo

<div class="viz-container">
<div class="controls">
<label>x₀: <span id="disp_x0">0.123</span></label>
<input type="range" id="inp_x0" min="0" max="1" step="0.001" value="0.123">
</div>
<div class="control-group">
<label>Perturbation (ε): <span id="disp_eps">0.0010</span></label>
<input type="range" id="inp_eps" min="0" max="0.01" step="0.0001" value="0.001">
<button id="playBtn">▶ Play</button>
<span id="timeDisplay">t = 0</span>
</div>

<div class="chart-wrapper">
<canvas id="trajChart"></canvas>
</div>
<div class="chart-wrapper">
<canvas id="errChart"></canvas>
</div>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<style>
.viz-container {
max-width: 800px;
margin: 20px auto;
}
.controls {
display: flex;
align-items: center;
gap: 15px;
margin-bottom: 20px;
flex-wrap: wrap;
}
.controls label {
font-weight: 600;
white-space: nowrap;
}
.controls input[type="range"] {
flex: 1;
min-width: 150px;
}
.controls button {
padding: 8px 20px;
background: #3182ce;
color: white;
border: none;
border-radius: 4px;
cursor: pointer;
}
.controls button:hover {
background: #2c5aa0;
}
.controls button:disabled {
background: #ccc;
cursor: not-allowed;
}
.chart-wrapper {
height: 250px;
margin-bottom: 20px;
}
</style>

<script>
// Wait for DOM and Chart.js to be ready
document.addEventListener('DOMContentLoaded', function() {
// Wait for Chart.js to load
function initVisualization() {
if (typeof Chart === 'undefined') {
setTimeout(initVisualization, 100);
return;
}

const ctxTraj = document.getElementById('trajChart');
const ctxErr = document.getElementById('errChart');

if (!ctxTraj || !ctxErr) {
console.error('Canvas elements not found');
return;
}

const ctxTraj2d = ctxTraj.getContext('2d');
const ctxErr2d = ctxErr.getContext('2d');
let chartTraj, chartErr;

// Store current values as variables
let currentX0 = 0.123;
let currentEps = 0.001;
let isPlaying = false;
let animationFrameId = null;
let currentStep = 0;
const maxSteps = 50;
let simulationData = null;

function runSimulation(x0, eps, steps=50) {
let t1 = [x0], t2 = [x0 + eps];
let diff = [Math.abs(eps)];
let labels = [0];
let s1 = x0, s2 = x0 + eps;

for (let i = 1; i <= steps; i++) {
s1 = (s1 * 2) % 1;
s2 = (s2 * 2) % 1;
t1.push(s1); t2.push(s2);
diff.push(Math.abs(s1 - s2));
labels.push(i);
}
return { labels, t1, t2, diff };
}

function updateCharts(data, upToStep = null) {
const step = upToStep !== null ? upToStep : data.labels.length - 1;
const labels = data.labels.slice(0, step + 1);
const t1 = data.t1.slice(0, step + 1);
const t2 = data.t2.slice(0, step + 1);
const diff = data.diff.slice(0, step + 1);

// Update trajectory chart
if (chartTraj) chartTraj.destroy();
chartTraj = new Chart(ctxTraj2d, {
type: 'line',
data: {
labels: labels,
datasets: [
{ label: 'Original', data: t1, borderColor: '#3182ce', borderWidth: 2, pointRadius: 0 },
{ label: 'Perturbed', data: t2, borderColor: '#e53e3e', borderWidth: 2, pointRadius: 0 }
]
},
options: {
responsive: true,
maintainAspectRatio: false,
animation: false,
scales: { 
y: { min: 0, max: 1 }, 
x: { display: true, title: { display: true, text: 'Time Step' } }
},
plugins: { 
legend: { display: true, position: 'top' }, 
title: { display: true, text: 'Trajectories' } 
}
}
});

// Update error/difference chart
if (chartErr) chartErr.destroy();
chartErr = new Chart(ctxErr2d, {
type: 'line',
data: {
labels: labels,
datasets: [{ 
label: 'Difference', 
data: diff, 
borderColor: '#4a5568', 
backgroundColor: 'rgba(74, 85, 104, 0.1)', 
borderWidth: 2, 
fill: true, 
pointRadius: 0 
}]
},
options: {
responsive: true,
maintainAspectRatio: false,
animation: false,
scales: { y: { min: 0, max: 1 } },
plugins: { legend: { display: false } }
}
});
}

function updateAll() {
// Get current slider values and update stored variables
const x0Input = document.getElementById('inp_x0');
const epsInput = document.getElementById('inp_eps');
if (!x0Input || !epsInput) return;

currentX0 = parseFloat(x0Input.value);
currentEps = parseFloat(epsInput.value);

// Update display values in real-time
const dispX0El = document.getElementById('disp_x0');
const dispEpsEl = document.getElementById('disp_eps');
if (dispX0El) dispX0El.textContent = currentX0.toFixed(3);
if (dispEpsEl) dispEpsEl.textContent = currentEps.toFixed(4);

// Run simulation with current variable values
simulationData = runSimulation(currentX0, currentEps);
currentStep = 0;

// Update charts to show full simulation
updateCharts(simulationData);
}

function animateStep() {
if (!isPlaying || !simulationData) return;

if (currentStep < maxSteps) {
updateCharts(simulationData, currentStep);
const timeDisplay = document.getElementById('timeDisplay');
if (timeDisplay) timeDisplay.textContent = `t = ${currentStep}`;
currentStep++;
animationFrameId = setTimeout(animateStep, 100);
} else {
stopAnimation();
}
}

function startAnimation() {
if (isPlaying) return;
isPlaying = true;
currentStep = 0;
const playBtn = document.getElementById('playBtn');
if (playBtn) {
playBtn.textContent = '⏸ Pause';
playBtn.disabled = false;
}
if (!simulationData) {
updateAll();
}
animateStep();
}

function stopAnimation() {
isPlaying = false;
if (animationFrameId) {
clearTimeout(animationFrameId);
animationFrameId = null;
}
const playBtn = document.getElementById('playBtn');
if (playBtn) {
playBtn.textContent = '▶ Play';
playBtn.disabled = false;
}
}

function toggleAnimation() {
if (isPlaying) {
stopAnimation();
} else {
startAnimation();
}
}

// Attach event listeners to sliders
const inpX0 = document.getElementById('inp_x0');
const inpEps = document.getElementById('inp_eps');
const stepSlider = document.getElementById('step_slider');
const dispX0 = document.getElementById('disp_x0');
const dispEps = document.getElementById('disp_eps');

if (inpX0 && dispX0) {
inpX0.addEventListener('input', function() {
// Stop any ongoing animation
stopAnimation();
// Update the variable immediately
currentX0 = parseFloat(this.value);
// Update display
dispX0.textContent = currentX0.toFixed(3);
// Update plots with new variable value
updateAll();
});
}

if (inpEps && dispEps) {
inpEps.addEventListener('input', function() {
// Stop any ongoing animation
stopAnimation();
// Update the variable immediately
currentEps = parseFloat(this.value);
// Update display
dispEps.textContent = currentEps.toFixed(4);
// Update plots with new variable value
updateAll();
});
}

// Play button
const playBtn = document.getElementById('playBtn');
if (playBtn) {
playBtn.addEventListener('click', toggleAnimation);
}

// Initialize variables from sliders on page load
const initX0 = document.getElementById('inp_x0');
const initEps = document.getElementById('inp_eps');
if (initX0) currentX0 = parseFloat(initX0.value);
if (initEps) currentEps = parseFloat(initEps.value);

// Initialize on page load
updateAll();
}

initVisualization();
});
</script>
