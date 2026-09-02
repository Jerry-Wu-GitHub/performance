/**
 * 全局配置常量
 */
const AppConfig = {
    get API_BASE_PATH() {
        // 获取 <base> 标签的 href
        const baseElement = document.querySelector('base');
        let basePath = '';
        if (baseElement) {
            const baseUrl = baseElement.href; // 完整 URL，如 http://example.com/myapp/
            const url = new URL(baseUrl);
            basePath = url.pathname; // 例如 '/myapp/' 或 '/'
        }
        // 去掉末尾斜杠（如果有），然后拼接 API 路径
        if (basePath.endsWith('/')) {
            basePath = basePath.slice(0, -1);
        }
        // 如果 basePath 为空（根路径），则直接返回 '/api/v1/performance'
        return basePath + '/api/v1/performance';
    },
    FAST_POLL_INTERVAL: 1000,
    SLOW_POLL_INTERVAL: 5000,
    CHART_TIME_WINDOW: 60000,       // 主图表时间窗口：60 秒
    MINI_CHART_TIME_WINDOW: 30000,  // 迷你图表时间窗口：30 秒
};
