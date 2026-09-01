/**
 * GPU 详情面板组件
 */
const GpuPanelComponent = {
    render(container) {
        const section = document.createElement('section');
        section.className = 'detail-section';
        section.id = 'section-gpu';
        section.innerHTML = `
            <header class="section-header">
                <h2>GPU</h2>
                <span class="section-subtitle">图形处理器实时监控</span>
            </header>
            <div id="gpu-cards-container"></div>
        `;
        container.appendChild(section);
    },

    update(data) {
        const gpus = data.gpus || [];
        const container = document.getElementById('gpu-cards-container');
        container.innerHTML = '';

        if (gpus.length === 0) {
            container.innerHTML = '<div class="gpu-empty">未检测到支持的 GPU 设备</div>';
            return;
        }

        gpus.forEach(gpu => {
            const card = document.createElement('div');
            card.className = 'gpu-card';
            card.innerHTML = `
                <div class="gpu-card-header">
                    <span class="gpu-name">${gpu.name}</span>
                </div>
                <div class="gpu-metrics-row">
                    <div class="metric-card" style="margin:0">
                        <div class="metric-label">核心利用率</div>
                        <div class="metric-value">${gpu.gpuUtil.toFixed(1)}%</div>
                    </div>
                    <div class="metric-card" style="margin:0">
                        <div class="metric-label">显存使用</div>
                        <div class="metric-value">${FormatUtils.formatBytes(gpu.memUsedBytes)} / ${FormatUtils.formatBytes(gpu.memTotalBytes)}</div>
                    </div>
                    <div class="metric-card" style="margin:0">
                        <div class="metric-label">温度</div>
                        <div class="metric-value">${gpu.tempC.toFixed(1)} °C</div>
                    </div>
                    <div class="metric-card" style="margin:0">
                        <div class="metric-label">功耗</div>
                        <div class="metric-value">${gpu.powerW.toFixed(1)} W</div>
                    </div>
                </div>
            `;
            container.appendChild(card);
        });
    },
};
