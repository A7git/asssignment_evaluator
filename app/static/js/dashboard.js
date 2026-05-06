/* Dashboard Charts — Canvas-based (no external libs) */

document.addEventListener('DOMContentLoaded', () => {
    fetch('/dashboard/api/stats')
        .then(r => r.json())
        .then(data => {
            drawBarChart('scoreChart', data.score_distribution, 'Score Distribution', {
                '0-20': '#ff5252', '21-40': '#ff7043', '41-60': '#ffa726',
                '61-80': '#667eea', '81-100': '#00d4aa'
            });
            drawBarChart('plagChart', data.plagiarism_distribution, 'Originality Distribution', {
                '0-49': '#ff5252', '50-69': '#ffa726', '70-89': '#667eea', '90-100': '#00d4aa'
            });
        })
        .catch(err => console.log('Dashboard stats not available:', err));
});

function drawBarChart(canvasId, data, title, colorMap) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;

    // Set actual canvas size
    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = 280 * dpr;
    canvas.style.width = rect.width + 'px';
    canvas.style.height = '280px';
    ctx.scale(dpr, dpr);

    const w = rect.width;
    const h = 280;
    const labels = Object.keys(data);
    const values = Object.values(data);
    const maxVal = Math.max(...values, 1);
    const barWidth = Math.min(60, (w - 80) / labels.length - 12);
    const chartLeft = 50;
    const chartBottom = h - 40;
    const chartTop = 30;
    const chartHeight = chartBottom - chartTop;

    // Background
    ctx.fillStyle = 'transparent';
    ctx.fillRect(0, 0, w, h);

    // Grid lines
    ctx.strokeStyle = 'rgba(102,126,234,0.08)';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
        const y = chartTop + (chartHeight / 4) * i;
        ctx.beginPath();
        ctx.moveTo(chartLeft, y);
        ctx.lineTo(w - 20, y);
        ctx.stroke();

        ctx.fillStyle = '#6573a0';
        ctx.font = '11px Inter, sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText(Math.round(maxVal - (maxVal / 4) * i), chartLeft - 8, y + 4);
    }

    // Bars
    const totalWidth = labels.length * (barWidth + 12);
    const startX = chartLeft + (w - chartLeft - 20 - totalWidth) / 2;

    labels.forEach((label, i) => {
        const x = startX + i * (barWidth + 12);
        const barHeight = (values[i] / maxVal) * chartHeight;
        const y = chartBottom - barHeight;

        // Bar gradient
        const gradient = ctx.createLinearGradient(x, y, x, chartBottom);
        const color = colorMap[label] || '#667eea';
        gradient.addColorStop(0, color);
        gradient.addColorStop(1, color + '40');

        // Rounded bar
        const radius = 4;
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.moveTo(x + radius, y);
        ctx.lineTo(x + barWidth - radius, y);
        ctx.quadraticCurveTo(x + barWidth, y, x + barWidth, y + radius);
        ctx.lineTo(x + barWidth, chartBottom);
        ctx.lineTo(x, chartBottom);
        ctx.lineTo(x, y + radius);
        ctx.quadraticCurveTo(x, y, x + radius, y);
        ctx.fill();

        // Value on top
        ctx.fillStyle = '#e8eaf6';
        ctx.font = 'bold 12px Inter, sans-serif';
        ctx.textAlign = 'center';
        if (values[i] > 0) ctx.fillText(values[i], x + barWidth / 2, y - 8);

        // Label
        ctx.fillStyle = '#9fa8da';
        ctx.font = '11px Inter, sans-serif';
        ctx.fillText(label, x + barWidth / 2, chartBottom + 18);
    });
}
