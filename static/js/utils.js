/**
 * 通用工具函数集合
 */
const FormatUtils = {
    /**
     * 格式化字节数为人类可读字符串
     * @param {number|null|undefined} bytes - 字节数
     * @returns {string}
     */
    formatBytes(bytes) {
        if (bytes === null || bytes === undefined) return '—';
        if (bytes >= 1073741824) return (bytes / 1073741824).toFixed(2) + ' GB';
        if (bytes >= 1048576) return (bytes / 1048576).toFixed(1) + ' MB';
        if (bytes >= 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return bytes + ' B';
    },

    /**
     * 格式化字节每秒速率
     * @param {number|null|undefined} bytesPerSecond
     * @returns {string}
     */
    formatBytesPerSecond(bytesPerSecond) {
        if (bytesPerSecond === null || bytesPerSecond === undefined) return '—';
        return this.formatBytes(bytesPerSecond) + '/s';
    },

    /**
     * 格式化系统运行时间
     * @param {number} seconds - 运行秒数
     * @returns {string}
     */
    formatUptime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        if (hours > 24) {
            const days = Math.floor(hours / 24);
            return `${days}d ${hours % 24}h`;
        }
        return `${hours}h ${minutes}m`;
    },

    /**
     * 格式化大数字为带单位字符串
     * @param {number|null|undefined} number
     * @returns {string}
     */
    formatLargeNumber(number) {
        if (number === null || number === undefined) return '—';
        if (number >= 1000000) return (number / 1000000).toFixed(2) + ' M';
        if (number >= 1000) return (number / 1000).toFixed(1) + ' K';
        return number.toString();
    },
};
