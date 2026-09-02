/**
 * 磁盘详情面板组件
 */
const DiskPanelComponent = {
    mainChart: null,

    render(container) {
        const section = document.createElement('section');
        section.className = 'detail-section';
        section.id = 'section-disk';
        section.innerHTML = `
            <header class="section-header">
                <h2>Disk</h2>
                <span class="section-subtitle">磁盘 I/O 性能实时监控</span>
            </header>

            <div class="metrics-grid" id="disk-metrics-overview"></div>

            <div class="chart-container">
                <div class="chart-header">
                    <span>磁盘利用率</span>
                    <span class="chart-unit">%</span>
                </div>
                <canvas class="main-chart" id="disk-chart"></canvas>
            </div>

            <div class="section-title">实时速率</div>
            <div class="metrics-grid" id="disk-metrics-rate"></div>

            <div class="section-title">累计计数</div>
            <div class="metrics-grid" id="disk-metrics-total"></div>
        `;
        container.appendChild(section);

        this.mainChart = new LineChart(document.getElementById('disk-chart'), {
            maxTimeSpan: AppConfig.CHART_TIME_WINDOW,
            maxValue: 100,
        });
    },

    update(data, meta = {}) {
        const timestamp = meta.timestamp ? meta.timestamp * 1000 : null;
        this.mainChart.push(data.utilization, null, timestamp);
        this._renderOverview(data);
        this._renderRates(data);
        this._renderTotals(data);
    },

    _renderOverview(data) {
        document.getElementById('disk-metrics-overview').innerHTML = `
            <div class="metric-card">
                <div class="metric-label">总容量</div>
                <div class="metric-value">${FormatUtils.formatBytes(data.totalBytes)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">磁盘类型</div>
                <div class="metric-value">${data.diskType || '—'}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">利用率</div>
                <div class="metric-value">${data.utilization.toFixed(1)}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">平均响应时间</div>
                <div class="metric-value">${data.awaitMs.toFixed(1)} ms</div>
            </div>
        `;
    },

    _renderRates(data) {
        document.getElementById('disk-metrics-rate').innerHTML = `
            <div class="metric-card">
                <div class="metric-label">读取速率</div>
                <div class="metric-value">${FormatUtils.formatBytesPerSecond(data.readSpeedBytes)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">写入速率</div>
                <div class="metric-value">${FormatUtils.formatBytesPerSecond(data.writeSpeedBytes)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">读取 IOPS</div>
                <div class="metric-value">${data.iopsRead.toFixed(1)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">写入 IOPS</div>
                <div class="metric-value">${data.iopsWrite.toFixed(1)}</div>
            </div>
        `;
    },

    _renderTotals(data) {
        const items = [
            { label: '累计读取', value: data.readBytes },
            { label: '累计写入', value: data.writeBytes },
            { label: '读取次数', value: data.readCount },
            { label: '写入次数', value: data.writeCount },
        ];

        document.getElementById('disk-metrics-total').innerHTML = items.map(item => `
            <div class="metric-card small">
                <div class="metric-label">${item.label}</div>
                <div class="metric-value">${item.value !== null
                    ? FormatUtils.formatBytes(item.value)
                    : '—'}</div>
            </div>
        `).join('');
    },
};
