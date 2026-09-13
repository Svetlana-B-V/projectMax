export function drawLineChart(canvas, data) {
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    const padding = 40;

    const values = Object.values(data);
    if (values.length === 0) {
        ctx.fillStyle = '#999';
        ctx.font = '14px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('Нет данных', width / 2, height / 2);
        return;
    }

    const maxValue = Math.max(...values);
    const minValue = 0;
    const range = maxValue - minValue || 1;

    const chartWidth = width - padding * 2;
    const chartHeight = height - padding * 2;
    const stepX = chartWidth / (values.length - 1 || 1);

    // Draw grid
    ctx.strokeStyle = '#e0e0e0';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 5; i++) {
        const y = padding + (chartHeight / 5) * i;
        ctx.beginPath();
        ctx.moveTo(padding, y);
        ctx.lineTo(width - padding, y);
        ctx.stroke();
    }

    // Draw line
    ctx.strokeStyle = '#36A2EB';
    ctx.lineWidth = 2;
    ctx.beginPath();
    values.forEach((value, index) => {
        const x = padding + stepX * index;
        const y = padding + chartHeight - ((value - minValue) / range) * chartHeight;
        if (index === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    });
    ctx.stroke();

    // Draw dots
    values.forEach((value, index) => {
        const x = padding + stepX * index;
        const y = padding + chartHeight - ((value - minValue) / range) * chartHeight;
        ctx.beginPath();
        ctx.fillStyle = '#36A2EB';
        ctx.arc(x, y, 4, 0, 2 * Math.PI);
        ctx.fill();
    });
}