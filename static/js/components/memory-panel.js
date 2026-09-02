/**
 * 内存详情面板组件
 */
const MemoryPanelComponent = {
    mainChart: null,

    render(container) {
        const section = document.createElement('section');
        section.className = 'detail-section';
        section.id = 'section-memory';
        section.innerHTML = `
            <header class="section-header">
                <h2>Memory</h2>
                <span class="section-subtitle">内存与交换分区实时监控</span>
            </header>

            <div class="metrics-grid" id="mem-metrics-main"></div>

            <div class="chart-container">
                <div class="chart-header">
                    <span>内存使用率</span>
                    <span class="chart-unit">%</span>
                </div>
                <canvas class="main-chart" id="memory-chart"></canvas>
            </div>

            <div class="section-title">物理内存明细</div>
            <div class="metrics-grid" id="mem-metrics-detail"></div>

            <div class="section-title">交换分区 (Swap)</div>
            <div class="metrics-grid" id="mem-metrics-swap"></div>
        `;
        container.appendChild(section);

        this.mainChart = new LineChart(document.getElementById('memory-chart'), {
            maxTimeSpan: AppConfig.CHART_TIME_WINDOW,
            maxValue: 100,
        });
    },

    update(data, meta = {}) {
        const timestamp = meta.timestamp ? meta.timestamp * 1000 : null;
        this.mainChart.push(data.usagePercent, null, timestamp);
        this._renderMainMetrics(data);
        this._renderDetailMetrics(data);
        this._renderSwapMetrics(data);
    },

    _renderMainMetrics(data) {
        document.getElementById('mem-metrics-main').innerHTML = `
            <div class="metric-card">
                <div class="metric-label">已用内存</div>
                <div class="metric-value">${FormatUtils.formatBytes(data.usedBytes)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">总内存</div>
                <div class="metric-value">${FormatUtils.formatBytes(data.totalBytes)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">可用内存</div>
                <div class="metric-value">${FormatUtils.formatBytes(data.availableBytes)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">使用率</div>
                <div class="metric-value">${data.usagePercent.toFixed(1)}%</div>
            </div>
        `;
    },

    _renderDetailMetrics(data) {
        const items = [
            { label: '空闲', value: data.freeBytes },
            { label: '活动', value: data.activeBytes },
            { label: '非活动', value: data.inactiveBytes },
            { label: '缓冲区', value: data.buffersBytes },
            { label: '缓存', value: data.cachedBytes },
            { label: 'Slab', value: data.slabBytes },
        ];

        document.getElementById('mem-metrics-detail').innerHTML = items.map(item => `
            <div class="metric-card small">
                <div class="metric-label">${item.label}</div>
                <div class="metric-value">${FormatUtils.formatBytes(item.value)}</div>
            </div>
        `).join('');
    },

    _renderSwapMetrics(data) {
        const swapIn = FormatUtils.formatBytes(data.swapSinBytes);
        const swapOut = FormatUtils.formatBytes(data.swapSoutBytes);

        document.getElementById('mem-metrics-swap').innerHTML = `
            <div class="metric-card">
                <div class="metric-label">已用 Swap</div>
                <div class="metric-value">${FormatUtils.formatBytes(data.swapUsedBytes)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Swap 总量</div>
                <div class="metric-value">${FormatUtils.formatBytes(data.swapTotalBytes)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Swap 使用率</div>
                <div class="metric-value">${data.swapPercent.toFixed(1)}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">换入 / 换出</div>
                <div class="metric-value">${swapIn} / ${swapOut}</div>
            </div>
        `;
    },
};
