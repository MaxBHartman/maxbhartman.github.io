---
layout: page
title: Bernoulli Shift Map Visualization
description: Interactive visualization of the Bernoulli shift map demonstrating chaotic dynamics and sensitive dependence on initial conditions.
importance: 1
category: work
---

## Overview

This was a small project created for the [ECE 598RE](https://courses.grainger.illinois.edu/ECE598RE/fa2025/) (Dynamical Systems & Neural Networks) webpage to visualize initial state perturbations in the Bernoulli shift map dynamical system. Specificially, the two initial states are defined: 
$$
x_0 = x_0
$$
$$
x'_0=x_0+\epsilon
$$
The maps are then defined as:

$$x_{t+1} = ax_t \pmod 1$$ 
$$x'_{t+1} = ax'_t \pmod 1$$ 

## Explaination of Parameters

$x_0$: is the initial unperturbed state at time $t$.

Perturbation ($\epsilon$): is the inital perburtbation applied at $t=0$.

$a$: is the scaling factor

Steps: Maximum number of time steps.

## Connections to Dynamical System and Stability 

The Bernoulli Shift Map is a standard toy model in dynamical systems theory for demonstrating how deterministic chaos arises in simple maps. The system's chaotic nature can be easily seen by directly computing its Lyapunov Exponent (LE) $\lambda$:

$$\lambda = \lim_{n \to \infty} \frac{1}{n} \sum_{i=0}^{n-1} \ln |f'(x_i)|\\

= \lim_{n \to \infty} \frac{1}{n} \sum_{i=0}^{n-1} \ln a = ln(a)$$

since $f'(x_i)=a$ for all $x_i\in [0,1]$.

Additionally, for this system, the Kolmogorov-Sinai (KS) Entropy $H_{KS}=ln(a)$ (the sum of all positive LEs).

If $a=1$, the system is not chaotic (Notice that $x_t=x'_t$ for all $t$), whereas if $a>1$, the system is chaotic (We assume $a\geq0$ for simplicity). In the $a=2$ case (the standard Bernoulli shift map), this map can be interpretted as a left bit shift. 

## Demo

<div class="viz-container">
<div class="controls">
<div class="control-group">
<label>x₀: <span id="disp_x0">0.1</span></label>
<input type="range" id="inp_x0" min="0" max="1" step="0.001" value="0.1">
</div>
<div class="control-group">
<label>Steps: <span id="disp_steps">50</span></label>
<input type="range" id="inp_steps" min="10" max="1000" step="10" value="50">
</div>
<div class="control-group">
<label>Perturbation: <span id="disp_eps">0.001</span></label>
<input type="range" id="inp_eps" min="0" max="0.01" step="0.0001" value="0.001">
</div>
<div class="control-group">
<label>Scale: <span id="disp_scale">2.0</span></label>
<input type="range" id="inp_scale" min="1" max="10" step="0.1" value="2">
</div>
<button id="playBtn">Play</button>
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
.control-group {
display: flex;
flex-direction: column;
gap: 5px;
flex: 1;
min-width: 150px;
}
.controls label {
font-weight: 600;
white-space: nowrap;
}
.controls input[type="range"] {
width: 100%;
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
    let currentX0 = 0.1;
    let currentEps = 0.001;
    let currentScale = 2;
    let maxSteps = 50;
    let isPlaying = false;
    let animationFrameId = null;
    let currentStep = 0;
    let simulationData = null;

    function runSimulation(x0, eps, scale, steps=50) {
      let t1 = [x0], t2 = [x0 + eps];
      let diff = [Math.abs(eps)];
      let labels = [0];
      let s1 = x0, s2 = x0 + eps;

      for (let i = 1; i <= steps; i++) {
        s1 = (s1 * scale) % 1;
        s2 = (s2 * scale) % 1;
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
      const stepsInput = document.getElementById('inp_steps');
      const scaleInput = document.getElementById('inp_scale');
      if (!x0Input || !epsInput || !stepsInput || !scaleInput) return;

      currentX0 = parseFloat(x0Input.value);
      currentEps = parseFloat(epsInput.value);
      maxSteps = parseInt(stepsInput.value);
      currentScale = parseFloat(scaleInput.value);

      // Update display values in real-time
      const dispX0El = document.getElementById('disp_x0');
      const dispEpsEl = document.getElementById('disp_eps');
      const dispStepsEl = document.getElementById('disp_steps');
      const dispScaleEl = document.getElementById('disp_scale');
      if (dispX0El) dispX0El.textContent = currentX0.toFixed(3);
      if (dispEpsEl) dispEpsEl.textContent = currentEps.toFixed(4);
      if (dispStepsEl) dispStepsEl.textContent = maxSteps;
      if (dispScaleEl) dispScaleEl.textContent = currentScale.toFixed(1);

      // Run simulation with current variable values
      simulationData = runSimulation(currentX0, currentEps, currentScale, maxSteps);
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
        // End if both sims are 0
        const t1Value = simulationData.t1[currentStep] || 0;
        const t2Value = simulationData.t2[currentStep] || 0;
        if (Math.abs(t1Value) < 1e-10 && Math.abs(t2Value) < 1e-10) {
          stopAnimation();
          return;
        }
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
        playBtn.textContent = 'Pause';
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
        playBtn.textContent = 'Play';
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
    const inpSteps = document.getElementById('inp_steps');
    const dispX0 = document.getElementById('disp_x0');
    const dispEps = document.getElementById('disp_eps');
    const dispSteps = document.getElementById('disp_steps');

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

    if (inpSteps && dispSteps) {
      inpSteps.addEventListener('input', function() {
        // Stop any ongoing animation
        stopAnimation();
        // Update the variable immediately
        maxSteps = parseInt(this.value);
        // Update display
        dispSteps.textContent = maxSteps;
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

    const inpScale = document.getElementById('inp_scale');
    const dispScale = document.getElementById('disp_scale');
    if (inpScale && dispScale) {
      inpScale.addEventListener('input', function() {
        // Stop any ongoing animation
        stopAnimation();
        // Update the variable immediately
        currentScale = parseFloat(this.value);
        // Update display
        dispScale.textContent = currentScale.toFixed(1);
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
    const initSteps = document.getElementById('inp_steps');
    const initScale = document.getElementById('inp_scale');
    if (initX0) currentX0 = parseFloat(initX0.value);
    if (initEps) currentEps = parseFloat(initEps.value);
    if (initSteps) maxSteps = parseInt(initSteps.value);
    if (initScale) currentScale = parseFloat(initScale.value);

    // Initialize on page load
    updateAll();
  }

  initVisualization();
});
</script>