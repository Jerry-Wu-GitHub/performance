---
domain: # 领域
tags: # 自定义标签
-
datasets: # 关联数据集
  evaluation:
  test:
  train:
models: # 关联模型

# 启动文件
deployspec:
  entry_file: main.py
license: Apache License 2.0
---

# 性能监控

## 简介

这是一个 FastAPI 项目。

本项目能很方便地为您的网络应用添加一个性能监控界面。

该界面会展示以下项目的信息：

- CPU
- 内存
- 磁盘
- 网络
- GPU

## 快速开始

1. 克隆仓库

    ```bash
    git clone https://github.com/Jerry-Wu-GitHub/performance.git
    ```

2. 安装依赖

    ```bash
    cd performance
    python -m pip install -r requirements.txt
    ```

3. 启动应用

    ```bash
    python main.py
    ```

应用默认运行在 `0.0.0.0:7860` ，可以通过环境变量配置。

## 添加为子页面

可以将本性能监控添加为您的已有的网络应用的子页面。

1. 在入口文件的包搜索路径里，将本仓库作为项目子模块：

    ```bash
    git submodule add https://github.com/Jerry-Wu-GitHub/performance.git performance
    git submodule update --remote
    ```

2. 安装依赖

    ```bash
    python -m pip install -r "performance/requirements.txt"
    ```

3. 在您的 FastAPI 应用创建处：

    ```python
    from performance import get_router as get_performance_router
    
    # 创建 FastAPI 应用
    app = FastAPI(title="Your APP")
    
    # 添加路由
    app.include_router(get_performance_router(prefix="/performance"))
    ```

如果指定了前缀（如 `get_router(prefix="/performance")`），那么该子页面的所有请求（包括对静态资源的）都会带上该前缀。

## 环境变量

应用启动时会调用 `load_dotenv()`，因此也可以通过项目根目录下的 `.env` 文件配置。环境变量未设置或为空字符串时使用默认值；`PORT` 等需要类型转换的变量若转换失败，也会回退到默认值。

| 环境变量                           | 说明                                       | 默认值                            |
| ---------------------------------- | ------------------------------------------ | --------------------------------- |
| `BASE_DIR`                         | Performace 根目录                          | 本仓库根目录                      |
| `STATIC_DIR`                       | Performace 静态资源目录                    | `"${BASE_DIR}/static"`            |
| `INDEX_PATH`                       | Performace 首页 HTML 文件路径              | `"${STATIC_DIR}/html/index.html"` |
| `HOST`                             | 服务监听主机                               | `"0.0.0.0"`                       |
| `PORT`                             | 服务监听端口                               | `7860`                            |
| `PERFORMANCE_MEASUREMENT_INTERVAL` | 对需要耗时采集的数据的采样时长（单位：秒） | `1.0`                             |

- `HOST` 和 `PORT` 仅在启动本仓库根目录里的 `main.py` 时才有效。

如果由于环境变量冲突而无法配置环境变量的话，也可以使用 `Config` 对象来配置：

```python
from performance import get_config as get_performance_config

performance_config = get_performance_config()
performance_config.performance_measurement_interval = 2.0
```
