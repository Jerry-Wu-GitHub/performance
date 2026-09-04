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

### Clone with HTTP

把本项目克隆到您的项目根目录下。

```bash
git submodule add https://github.com/Jerry-Wu-GitHub/performance.git performance
git submodule update --remote
```

### 设置依赖

这一步是可选的。

您可以为与性能监控相关的页面和 API 添加依赖，用以身份验证等。

```python
from performance import dependence_mounter

dependence_mounter.register(dependence) # `dependence` 是您要添加的依赖函数
```

您还可以额外传入 `route_pattern` 参数，来过滤要执行该依赖的路由。

注意，以上方法添加的依赖函数不能有参数。如果您要添加有 FastAPI 注入参数的依赖函数，请参见[注册路由](#注册路由)。

### 注册路由

```python
from performance import get_router

app.include_router(get_router(
    prefix="子应用前缀",
    dependencies=[dependence] # 可选。`dependence` 是您要添加的依赖函数
))
```

## 示例

见 [`main.py`](main.py) 。
