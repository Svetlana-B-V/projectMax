export function drawDonutChart(canvas, data) {
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) / 2 - 10;
    const innerRadius = radius * 0.65;

    const total = Object.values(data).reduce((sum, val) => sum + parseFloat(val), 0);

    ctx.clearRect(0, 0, width, height);

    if (total === 0) {
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
        ctx.strokeStyle = '#e0e0e0';
        ctx.lineWidth = 2;
        ctx.stroke();
        ctx.fillStyle = '#999';
        ctx.font = '14px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('Нет данных', centerX, centerY);
        return;
    }

    const colors = ['#21A038', '#00B578', '#FFD93D', '#FF6B6B', '#36A2EB', '#6C5CE7', '#FF9F40'];
    let startAngle = -Math.PI / 2;
    let colorIndex = 0;

    // Зазор между сегментами (в радианах)
    const gap = 0.04;

    for (const [label, value] of Object.entries(data)) {
        const sliceAngle = (parseFloat(value) / total) * 2 * Math.PI;
        const endAngle = startAngle + sliceAngle - gap;

        // Рисуем сегмент как кольцо (без клина)
        ctx.beginPath();
        ctx.fillStyle = colors[colorIndex % colors.length];

        // Внешняя дуга (по часовой)
        ctx.arc(centerX, centerY, radius, startAngle, endAngle);

        // Закругление на конце внешней дуги
        const roundEndX = centerX + Math.cos(endAngle) * radius;
        const roundEndY = centerY + Math.sin(endAngle) * radius;
        ctx.lineTo(roundEndX, roundEndY);

        // Внутренняя дуга (против часовой)
        ctx.arc(centerX, centerY, innerRadius, endAngle, startAngle, true);

        // Закругление на начале
        const roundStartX = centerX + Math.cos(startAngle) * innerRadius;
        const roundStartY = centerY + Math.sin(startAngle) * innerRadius;
        ctx.lineTo(roundStartX, roundStartY);

        ctx.closePath();
        ctx.fill();

        startAngle += sliceAngle;
        colorIndex++;
    }

    // Белый центр
    ctx.beginPath();
    ctx.arc(centerX, centerY, innerRadius - 2, 0, 2 * Math.PI);
    ctx.fillStyle = '#fff';
    ctx.fill();

    // Текст в центре
    ctx.fillStyle = '#333';
    ctx.font = 'bold 16px Arial';
    ctx.textAlign = 'center';
    ctx.fillText(total.toLocaleString('ru-RU') + ' ₽', centerX, centerY);
    ctx.font = '12px Arial';
    ctx.fillStyle = '#666';
    ctx.fillText('всего', centerX, centerY + 20);
}