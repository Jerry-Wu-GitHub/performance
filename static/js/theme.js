/**
 * 主题管理器
 * 支持 light / dark / system 三种模式
 */
const ThemeManager = {
    STORAGE_KEY: 'monitor_theme',

    /**
     * 初始化主题
     */
    init() {
        const savedMode = localStorage.getItem(this.STORAGE_KEY) || 'system';
        this.apply(savedMode);
    },

    /**
     * 应用指定主题
     * @param {string} mode - light / dark / system
     */
    apply(mode) {
        if (mode === 'system') {
            document.documentElement.removeAttribute('data-theme');
        } else {
            document.documentElement.setAttribute('data-theme', mode);
        }
        localStorage.setItem(this.STORAGE_KEY, mode);
    },

    /**
     * 获取当前强调色的 CSS 值
     * @returns {string}
     */
    getAccentColor() {
        const styles = getComputedStyle(document.documentElement);
        return styles.getPropertyValue('--accent').trim();
    },
};
