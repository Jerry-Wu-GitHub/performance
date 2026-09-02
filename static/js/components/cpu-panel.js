/**
 * CPU 详情面板组件
 */
const CpuPanelComponent = {
    mainChart: null,
    sectionElement: null,

    /**
     * 渲染面板 DOM
     * @param {HTMLElement} container
     */
    render(container) {
        const section = document.createElement('section');
        section.className = 'detail-section';
        section.id = 'section-cpu';
        section.innerHTML = `
            <header class="section-header">
                <h2>CPU</h2>
                <span class="section-subtitle">处理器性能实时监控</span>
            </header>
            
            <div class="metrics-grid" id="cpu-metrics-top"></div>
            
            <div class="chart-container">
                <div class="chart-header">
                    <span>CPU 使用率</span>
                    <span class="chart-unit">%</span>
                </div>
                <canvas class="main-chart" id="cpu-chart"></canvas>
            </div>

            <div class="section-title">各核心使用率</div>
            <div class="per-core-grid" id="cpu-per-core"></div>

            <div class="metrics-grid" id="cpu-metrics-bottom"></div>
        `;
        container.appendChild(section);
        this.sectionElement = section;

        this.mainChart = new LineChart(document.getElementById('cpu-chart'), {
            maxTimeSpan: AppConfig.CHART_TIME_WINDOW,
            maxValue: 100,
        });
    },

    /**
     * 更新面板数据
     * @param {object} data - CPUStats 数据
     */
    update(data, meta = {}) {
        const timestamp = meta.timestamp ? meta.timestamp * 1000 : null;
        this.mainChart.push(data.overallUsage, null, timestamp);
        this._renderTopMetrics(data);
        this._renderPerCore(data.perCpuUsage);
        this._renderBottomMetrics(data);
    },

    _renderTopMetrics(data) {
        const grid = document.getElementById('cpu-metrics-top');
        grid.innerHTML = this._buildMetricCards([
            { label: '整体使用率', value: data.overallUsage.toFixed(1) + '%' },
            { label: '物理核心', value: data.physicalCores },
            { label: '逻辑核心', value: data.logicalCores },
            {
                label: '当前频率',
                value: data.currentFreqMhz
                    ? data.currentFreqMhz.toFixed(0) + ' MHz'
                    : '—'
            },
        ]);
    },

    _renderPerCore(usages) {
        const container = document.getElementById('cpu-per-core');
        const currentCount = container.children.length;

        if (currentCount !== usages.length) {
            container.innerHTML = '';
            usages.forEach((_, index) => {
                const bar = document.createElement('div');
                bar.className = 'core-bar';
                bar.innerHTML = `
                    <div class="core-label">Core ${index}</div>
                    <div class="core-track">
                        <div class="core-fill" style="width: 0%"></div>
                    </div>
                `;
                container.appendChild(bar);
            });
        }

        container.querySelectorAll('.core-fill').forEach((fill, index) => {
            fill.style.width = usages[index].toFixed(1) + '%';
        });
    },

    _renderBottomMetrics(data) {
        const grid = document.getElementById('cpu-metrics-bottom');
        grid.innerHTML = this._buildMetricCards([
            {
                label: '1 分钟负载',
                value: data.loadAvg1Min !== null
                    ? data.loadAvg1Min.toFixed(2)
                    : '—'
            },
            {
                label: '5 分钟负载',
                value: data.loadAvg5Min !== null
                    ? data.loadAvg5Min.toFixed(2)
                    : '—'
            },
            {
                label: '15 分钟负载',
                value: data.loadAvg15Min !== null
                    ? data.loadAvg15Min.toFixed(2)
                    : '—'
            },
            { label: '进程数', value: data.processCount },
            { label: '运行时间', value: FormatUtils.formatUptime(data.uptimeSeconds) },
            { label: '上下文切换', value: FormatUtils.formatLargeNumber(data.ctxSwitches) },
        ]);
    },

    _buildMetricCards(items) {
        return items.map(item => `
            <div class="metric-card">
                <div class="metric-label">${item.label}</div>
                <div class="metric-value">${item.value}</div>
            </div>
        `).join('');
    },
};
