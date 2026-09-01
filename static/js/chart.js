/**
 * Canvas 折线图组件
 * 时间轴驱动：数据点按真实时间间距分布，支持渐变填充、双线显示
 */
class LineChart {
    /**
     * @param {HTMLCanvasElement} canvas - 画布元素
     * @param {object} options - 配置项
     * @param {number} options.maxTimeSpan - 最大时间窗口（毫秒）
     * @param {number} options.maxValue - Y轴初始最大值
     * @param {number} options.strokeWidth - 线宽
     * @param {boolean} options.enableGradient - 是否启用渐变填充
     * @param {boolean} options.enableSecondLine - 是否启用第二条线
     * @param {boolean} options.enableDynamicYAxis - 是否启用动态Y轴范围
     */
    constructor(canvas, options = {}) {
        this.canvas = canvas;
        this.context = canvas.getContext('2d');
        this.dataPoints = [];       // [{ time: number, value: number }]
        this.secondDataPoints = []; // 第二条线数据

        this.maxTimeSpan = options.maxTimeSpan || 60000;
        this.maxValue = options.maxValue || 100;
        this.minValue = options.minValue || 0;
        this.strokeWidth = options.strokeWidth || 1.5;
        this.enableGradient = options.enableGradient !== false;
        this.enableSecondLine = options.enableSecondLine || false;
        this.enableDynamicYAxis = options.enableDynamicYAxis || false;

        this._resizeCanvas();
        window.addEventListener('resize', () => this._resizeCanvas());
    }

    /**
     * 添加新数据点并重绘
     * @param {number} value - 主线数据
     * @param {number|null} secondValue - 副线数据
     * @param {number} [timestamp] - 时间戳（毫秒），不传则使用当前时间
     */
    push(value, secondValue = null, timestamp = null) {
        const time = timestamp || Date.now();

        this.dataPoints.push({ time, value });
        this._purgeOldPoints(this.dataPoints);

        if (this.enableSecondLine && secondValue !== null) {
            this.secondDataPoints.push({ time, value: secondValue });
            this._purgeOldPoints(this.secondDataPoints);
        }

        // 固定范围模式下只向上调整
        if (!this.enableDynamicYAxis) {
            this._adjustMaxValue(value);
        }

        this.render();
    }

    /**
     * 主动刷新：重新计算画布尺寸并重绘
     */
    refresh() {
        this._resizeCanvas();
    }

    /**
     * 主动触发重绘
     */
    render() {
        const ctx = this.context;
        const width = this.displayWidth;
        const height = this.displayHeight;

        ctx.clearRect(0, 0, width, height);
        if (this.dataPoints.length < 2) return;

        const timeRange = this._getTimeRange();
        if (timeRange.duration <= 0) return;

        // 动态Y轴模式：根据当前窗口数据重新计算上限
        if (this.enableDynamicYAxis) {
            this._updateDynamicMaxValue();
        }

        const accent = ThemeManager.getAccentColor();

        if (this.enableGradient) {
            this._drawGradientFill(ctx, width, height, timeRange, accent);
        }

        this._drawLine(ctx, this.dataPoints, width, height, timeRange, accent, this.strokeWidth);

        if (this.enableSecondLine && this.secondDataPoints.length > 1) {
            ctx.setLineDash([3, 3]);
            this._drawLine(ctx, this.secondDataPoints, width, height, timeRange, accent, this.strokeWidth, 0.4);
            ctx.setLineDash([]);
        }
    }

    _resizeCanvas() {
        const rect = this.canvas.getBoundingClientRect();
        // 元素不可见时跳过，避免画布失效
        if (rect.width <= 0 || rect.height <= 0) return;

        const dpr = window.devicePixelRatio || 1;
        this.canvas.width = rect.width * dpr;
        this.canvas.height = rect.height * dpr;
        this.context.scale(dpr, dpr);
        this.displayWidth = rect.width;
        this.displayHeight = rect.height;
        this.render();
    }

    _purgeOldPoints(points) {
        const cutoff = Date.now() - this.maxTimeSpan;
        while (points.length > 0 && points[0].time < cutoff) {
            points.shift();
        }
    }

    _getTimeRange() {
        const endTime = this.dataPoints.length > 0
            ? this.dataPoints[this.dataPoints.length - 1].time
            : Date.now();
        const startTime = endTime - this.maxTimeSpan;
        return { startTime, endTime, duration: endTime - startTime };
    }

    /**
     * 固定范围模式：只向上调整Y轴上限
     */
    _adjustMaxValue(value) {
        if (value > this.maxValue * 0.85) {
            this.maxValue = Math.ceil(value * 1.2 / 10) * 10;
        }
    }

    /**
     * 动态范围模式：根据当前所有可见数据计算Y轴上限，可升可降
     */
    _updateDynamicMaxValue() {
        let maxValue = 0;

        // 遍历主线数据
        for (const point of this.dataPoints) {
            if (point.value > maxValue) {
                maxValue = point.value;
            }
        }

        // 遍历副线数据
        if (this.enableSecondLine) {
            for (const point of this.secondDataPoints) {
                if (point.value > maxValue) {
                    maxValue = point.value;
                }
            }
        }

        // 最小下限保护，避免除以0
        if (maxValue <= 0) {
            this.maxValue = 1;
            return;
        }

        // 顶部保留20%余量
        this.maxValue = Math.ceil(maxValue * 1.2);
    }

    _drawLine(ctx, points, width, height, timeRange, color, lineWidth, alpha = 1) {
        ctx.beginPath();
        let hasStarted = false;

        for (let i = 0; i < points.length; i++) {
            const point = points[i];
            if (point.time < timeRange.startTime) continue;

            const x = ((point.time - timeRange.startTime) / timeRange.duration) * width;
            const y = height - (point.value / this.maxValue) * height;

            if (!hasStarted) {
                ctx.moveTo(x, y);
                hasStarted = true;
            } else {
                ctx.lineTo(x, y);
            }
        }

        if (!hasStarted) return;

        ctx.strokeStyle = alpha < 1 ? this._hexToRgba(color, alpha) : color;
        ctx.lineWidth = lineWidth;
        ctx.lineJoin = 'round';
        ctx.stroke();
    }

    _drawGradientFill(ctx, width, height, timeRange, accent) {
        const gradient = ctx.createLinearGradient(0, 0, 0, height);
        gradient.addColorStop(0, this._hexToRgba(accent, 0.3));
        gradient.addColorStop(1, this._hexToRgba(accent, 0.02));

        ctx.beginPath();
        let hasStarted = false;

        for (let i = 0; i < this.dataPoints.length; i++) {
            const point = this.dataPoints[i];
            if (point.time < timeRange.startTime) continue;

            const x = ((point.time - timeRange.startTime) / timeRange.duration) * width;
            const y = height - (point.value / this.maxValue) * height;

            if (!hasStarted) {
                ctx.moveTo(x, height);
                ctx.lineTo(x, y);
                hasStarted = true;
            } else {
                ctx.lineTo(x, y);
            }
        }

        if (!hasStarted) return;

        const lastX = ((this.dataPoints[this.dataPoints.length - 1].time - timeRange.startTime) / timeRange.duration) * width;
        ctx.lineTo(lastX, height);
        ctx.closePath();
        ctx.fillStyle = gradient;
        ctx.fill();
    }

    _hexToRgba(hex, alpha) {
        let r, g, b;
        if (hex.startsWith('#')) {
            const hexNum = hex.slice(1);
            r = parseInt(hexNum.substr(0, 2), 16);
            g = parseInt(hexNum.substr(2, 2), 16);
            b = parseInt(hexNum.substr(4, 2), 16);
        } else {
            const match = hex.match(/\d+/g);
            r = match ? +match[0] : 0;
            g = match ? +match[1] : 255;
            b = match ? +match[2] : 136;
        }
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }
}
