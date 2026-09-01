/**
 * 左侧导航栏组件
 * 动态渲染五个监控项的导航入口与迷你图表
 */
const SidebarComponent = {
    miniCharts: {},
    activeKey: 'cpu',

    /**
     * 渲染侧边栏 DOM
     * @param {HTMLElement} container - 父容器
     */
    render(container) {
        const sidebar = document.createElement('aside');
        sidebar.className = 'sidebar';
        sidebar.innerHTML = `
            <div class="sidebar-header">
                <h1>Performance</h1>
                <span class="sidebar-subtitle">System Monitor</span>
            </div>
            <nav class="nav-list" id="nav-list"></nav>
        `;
        container.appendChild(sidebar);

        this._renderNavItems();
        this._bindNavigationEvents();
    },

    _renderNavItems() {
        const navList = document.getElementById('nav-list');
        const items = ['cpu', 'memory', 'disk', 'network', 'gpu'];
        const labels = {
            cpu: 'CPU',
            memory: 'Memory',
            disk: 'Disk',
            network: 'Network',
            gpu: 'GPU',
        };

        items.forEach(key => {
            const item = document.createElement('div');
            item.className = 'nav-item';
            item.dataset.target = key;
            item.innerHTML = `
                <canvas class="mini-chart" id="${key}-mini"></canvas>
                <div class="nav-info">
                    <div class="nav-title">${labels[key]}</div>
                    <div class="nav-sub" id="${key}-mini-sub">
                        <span>—</span>
                        <span>—</span>
                    </div>
                </div>
            `;
            navList.appendChild(item);

            this.miniCharts[key] = new LineChart(
                document.getElementById(`${key}-mini`),
                {
                    maxTimeSpan: AppConfig.MINI_CHART_TIME_WINDOW,
                    maxValue: 100,
                    strokeWidth: 1.2,
                }
            );
        });

        // 默认选中第一项
        navList.querySelector('[data-target="cpu"]').classList.add('active');
    },

    _bindNavigationEvents() {
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', () => {
                const target = item.dataset.target;
                this._setActive(target);
                this.onSwitch?.(target);
            });
        });
    },

    _setActive(key) {
        document.querySelectorAll('.nav-item').forEach(el => {
            el.classList.toggle('active', el.dataset.target === key);
        });
        this.activeKey = key;
    },

    /**
     * 更新迷你图表与文字
     * @param {string} key - 模块键名
     * @param {number} value - 图表值
     * @param {string[]} texts - 两行说明文字
     */
    updateMini(key, value, texts) {
        this.miniCharts[key].push(value);

        const sub = document.getElementById(`${key}-mini-sub`);
        if (sub && texts.length >= 2) {
            sub.innerHTML = `<span>${texts[0]}</span><span>${texts[1]}</span>`;
        }
    },
};
