/**
 * 异步数据采集器
 * 支持快慢两种轮询频率，可订阅数据更新
 * 保证同一时刻只有一个请求在途，避免请求堆积
 */
class DataFetcher {
    /**
     * @param {string} endpoint - API 端点名称
     */
    constructor(endpoint) {
        this.endpoint = endpoint;
        this.apiUrl = `${AppConfig.API_BASE_PATH}/${endpoint}`;
        this.subscribers = [];
        this.timeoutId = null;
        this.pollInterval = AppConfig.SLOW_POLL_INTERVAL;
        this.latestData = null;
        this.latestMeta = null;
        this.isFetching = false;
        this.isRunning = false;
    }

    /**
     * 订阅数据更新
     * @param {function} callback - 数据回调函数
     */
    subscribe(callback) {
        this.subscribers.push(callback);
        if (this.latestData) {
            callback(this.latestData, this.latestMeta);
        }
    }

    /**
     * 设置快速轮询模式
     * @param {boolean} isFast - 是否快速模式
     */
    setFastMode(isFast) {
        this.pollInterval = isFast
            ? AppConfig.FAST_POLL_INTERVAL
            : AppConfig.SLOW_POLL_INTERVAL;
        // 无需重启定时器，下一次调度自动使用新间隔
    }

    /**
     * 启动轮询
     */
    start() {
        if (this.isRunning) return;
        this.isRunning = true;
        this._scheduleNext();
    }

    /**
     * 停止轮询
     * 清除待执行的定时器，正在进行中的请求会正常完成但不再调度下一次
     */
    stop() {
        this.isRunning = false;
        if (this.timeoutId) {
            clearTimeout(this.timeoutId);
            this.timeoutId = null;
        }
    }

    /**
     * 调度下一次请求
     */
    _scheduleNext() {
        if (!this.isRunning) return;
        this.timeoutId = setTimeout(() => {
            this._fetchOnce();
        }, this.pollInterval);
    }

    /**
     * 执行一次数据请求
     * 飞行中互斥：如果上一次请求未完成则直接跳过本次
     */
    async _fetchOnce() {
        if (this.isFetching) return;

        this.isFetching = true;
        try {
            const response = await fetch(this.apiUrl);
            const result = await response.json();
            if (result.data) {
                this.latestData = result.data;
                this.latestMeta = result.meta || {};
                this.subscribers.forEach(callback => callback(result.data, result.meta || {}));
            }
        } catch (error) {
            console.error(`Fetch ${this.endpoint} failed:`, error);
        } finally {
            this.isFetching = false;
            this._scheduleNext();
        }
    }
}
