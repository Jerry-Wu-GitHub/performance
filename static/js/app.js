/**
 * 监控应用主入口
 * 协调所有组件与数据采集器
 */
class MonitorApplication {
    constructor() {
        this.fetchers = {};
        this.panels = {
            cpu: CpuPanelComponent,
            memory: MemoryPanelComponent,
            disk: DiskPanelComponent,
            network: NetworkPanelComponent,
            gpu: GpuPanelComponent,
        };
        this.currentTab = 'cpu';
    }

    /**
     * 启动应用
     */
    start() {
        ThemeManager.init();
        this._createFetchers();
        this._renderLayout();
        this._bindDataSubscriptions();
        this._startAllFetchers();
        this._switchTab('cpu');
    }

    _createFetchers() {
        Object.keys(this.panels).forEach(key => {
            this.fetchers[key] = new DataFetcher(key);
        });
    }

    _renderLayout() {
        const root = document.getElementById('app');

        // 渲染侧边栏
        SidebarComponent.render(root);
        SidebarComponent.onSwitch = tab => this._switchTab(tab);

        // 渲染详情面板容器
        const detailPanel = document.createElement('main');
        detailPanel.className = 'detail-panel';
        root.appendChild(detailPanel);

        // 渲染各个面板
        Object.values(this.panels).forEach(panel => {
            panel.render(detailPanel);
        });
    }

    _bindDataSubscriptions() {
        this.fetchers.cpu.subscribe((data, meta) => {
            const timestamp = meta?.timestamp ? meta.timestamp * 1000 : null;
            SidebarComponent.updateMini('cpu', data.overallUsage, [
                data.overallUsage.toFixed(1) + '%',
                data.currentFreqMhz ? data.currentFreqMhz.toFixed(0) + ' MHz' : '—'
            ], timestamp);
            this.panels.cpu.update(data, meta);
        });

        this.fetchers.memory.subscribe((data, meta) => {
            const timestamp = meta?.timestamp ? meta.timestamp * 1000 : null;
            SidebarComponent.updateMini('memory', data.usagePercent, [
                `${FormatUtils.formatBytes(data.usedBytes)} / ${FormatUtils.formatBytes(data.totalBytes)}`,
                data.usagePercent.toFixed(1) + '%'
            ], timestamp);
            this.panels.memory.update(data, meta);
        });

        this.fetchers.disk.subscribe((data, meta) => {
            const timestamp = meta?.timestamp ? meta.timestamp * 1000 : null;
            SidebarComponent.updateMini('disk', data.utilization, [
                data.utilization.toFixed(1) + '%',
                data.awaitMs.toFixed(1) + ' ms'
            ], timestamp);
            this.panels.disk.update(data, meta);
        });

        this.fetchers.network.subscribe((data, meta) => {
            const timestamp = meta?.timestamp ? meta.timestamp * 1000 : null;
            let totalSend = 0;
            let totalReceive = 0;
            Object.values(data.nicSpeeds).forEach(s => {
                totalSend += s.sendSpeedBytes;
                totalReceive += s.recvSpeedBytes;
            });
            SidebarComponent.updateMini('network', totalReceive, [
                '↑ ' + FormatUtils.formatBytesPerSecond(totalSend),
                '↓ ' + FormatUtils.formatBytesPerSecond(totalReceive)
            ], timestamp);
            this.panels.network.update(data, meta);
        });

        this.fetchers.gpu.subscribe((data, meta) => {
            const timestamp = meta?.timestamp ? meta.timestamp * 1000 : null;
            const gpus = data.gpus || [];
            if (gpus.length > 0) {
                const first = gpus[0];
                SidebarComponent.updateMini('gpu', first.gpuUtil, [
                    first.name.split(' ').slice(-2).join(' '),
                    first.gpuUtil.toFixed(1) + '%'
                ], timestamp);
            } else {
                SidebarComponent.updateMini('gpu', 0, ['无 GPU', '—'], timestamp);
            }
            this.panels.gpu.update(data, meta);
        });
    }

    _startAllFetchers() {
        Object.values(this.fetchers).forEach(fetcher => fetcher.start());
    }

    _switchTab(tabKey) {
        // 切换面板显示
        document.querySelectorAll('.detail-section').forEach(el => {
            el.classList.toggle('active', el.id === `section-${tabKey}`);
        });

        // 调整各模块轮询频率
        Object.keys(this.fetchers).forEach(key => {
            this.fetchers[key].setFastMode(key === tabKey);
        });

        // 面板显示后刷新图表，重新计算画布尺寸
        const panel = this.panels[tabKey];
        if (panel && panel.mainChart) {
            panel.mainChart.refresh();
        }

        this.currentTab = tabKey;
    }
}

// 页面加载完成后启动
document.addEventListener('DOMContentLoaded', () => {
    const app = new MonitorApplication();
    app.start();
});
