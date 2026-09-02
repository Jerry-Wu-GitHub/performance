/**
 * 网络详情面板组件
 */
const NetworkPanelComponent = {
    mainChart: null,

    render(container) {
        const section = document.createElement('section');
        section.className = 'detail-section';
        section.id = 'section-network';
        section.innerHTML = `
            <header class="section-header">
                <h2>Network</h2>
                <span class="section-subtitle">网络接口实时流量监控</span>
            </header>

            <div class="metrics-grid" id="net-metrics-summary"></div>

            <div class="chart-container">
                <div class="chart-header">
                    <span>网络吞吐速率</span>
                    <span class="chart-unit">B/s</span>
                </div>
                <canvas class="main-chart" id="network-chart"></canvas>
            </div>

            <div class="section-title">网卡列表</div>
            <div id="network-nics-list"></div>
        `;
        container.appendChild(section);

        this.mainChart = new LineChart(document.getElementById('network-chart'), {
            maxTimeSpan: AppConfig.CHART_TIME_WINDOW,
            maxValue: 1024,        // 初始 1 KB/s，后续自动动态调整
            enableSecondLine: true,
            enableDynamicYAxis: true,
        });
    },

    update(data, meta = {}) {
        const timestamp = meta.timestamp ? meta.timestamp * 1000 : null;
        const totals = this._calculateTotalSpeed(data);
        this.mainChart.push(totals.totalReceive, totals.totalSend, timestamp);
        this._renderSummary(totals, data.activeNics.length);
        this._renderNicList(data);
    },

    _calculateTotalSpeed(data) {
        let totalSend = 0;
        let totalReceive = 0;
        Object.values(data.nicSpeeds).forEach(speed => {
            totalSend += speed.sendSpeedBytes;
            totalReceive += speed.recvSpeedBytes;
        });
        return { totalSend, totalReceive };
    },

    _renderSummary(totals, nicCount) {
        document.getElementById('net-metrics-summary').innerHTML = `
            <div class="metric-card">
                <div class="metric-label">发送速率</div>
                <div class="metric-value">${FormatUtils.formatBytesPerSecond(totals.totalSend)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">接收速率</div>
                <div class="metric-value">${FormatUtils.formatBytesPerSecond(totals.totalReceive)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">活跃网卡</div>
                <div class="metric-value">${nicCount}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">总吞吐</div>
                <div class="metric-value">${FormatUtils.formatBytesPerSecond(totals.totalSend + totals.totalReceive)}</div>
            </div>
        `;
    },

    _renderNicList(data) {
        const container = document.getElementById('network-nics-list');
        container.innerHTML = '';

        data.activeNics.forEach(nicName => {
            const config = data.nicConfigs[nicName] || {};
            const counters = data.nicCounters[nicName] || {};
            const speeds = data.nicSpeeds[nicName] || {};

            const card = document.createElement('div');
            card.className = 'nic-card';
            card.innerHTML = `
                <div class="nic-header">
                    <span class="nic-name">${nicName}</span>
                    <span class="nic-status">${config.isUp ? 'UP' : 'DOWN'}</span>
                </div>
                <div class="nic-details">
                    <div class="nic-detail-item">
                        <span class="nic-detail-label">IPv4</span>
                        <span class="nic-detail-value">${config.ipv4?.join(', ') || '—'}</span>
                    </div>
                    <div class="nic-detail-item">
                        <span class="nic-detail-label">MAC</span>
                        <span class="nic-detail-value">${config.mac || '—'}</span>
                    </div>
                    <div class="nic-detail-item">
                        <span class="nic-detail-label">速率 / MTU</span>
                        <span class="nic-detail-value">${config.speedMbps ? config.speedMbps + ' Mb/s' : '—'} / ${config.mtu || '—'}</span>
                    </div>
                    <div class="nic-detail-item">
                        <span class="nic-detail-label">发送 / 接收</span>
                        <span class="nic-detail-value">${FormatUtils.formatBytesPerSecond(speeds.sendSpeedBytes || 0)} / ${FormatUtils.formatBytesPerSecond(speeds.recvSpeedBytes || 0)}</span>
                    </div>
                    <div class="nic-detail-item">
                        <span class="nic-detail-label">累计发送</span>
                        <span class="nic-detail-value">${FormatUtils.formatBytes(counters.bytesSent || 0)}</span>
                    </div>
                    <div class="nic-detail-item">
                        <span class="nic-detail-label">累计接收</span>
                        <span class="nic-detail-value">${FormatUtils.formatBytes(counters.bytesRecv || 0)}</span>
                    </div>
                </div>
            `;
            container.appendChild(card);
        });
    },
};
