# RealMoon Exchange Rate Monitor

RealMoon 是一个可扩展的命令行应用，用于实时获取人民币（CNY）对美元（USD）、澳元（AUD）、日元（JPY）等货币的最新汇率，并在超过设定阈值时触发预警。

## 功能特性

- 默认从 [exchangerate.host](https://exchangerate.host/) 获取实时外汇数据。
- 支持通过 YAML 配置文件自定义监控的币种、阈值以及轮询周期。
- 提供一次性查询和长期守护两种运行模式。
- 当汇率突破上下阈值时输出告警信息，方便与告警系统进行集成。

## 快速开始

### 1. 创建虚拟环境并安装依赖

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # 可选，安装后可启用完整的 YAML 语法支持
```

### 2. 编写配置文件

可以直接复制 `config/sample_config.yml` 并按需修改：

```bash
cp config/sample_config.yml my_config.yml
```

示例：

```yaml
base_currency: CNY
currencies:
  - USD
  - AUD
  - JPY
interval_seconds: 600
thresholds:
  USD:
    lower: 0.130
    upper: 0.150
  AUD:
    lower: 0.190
    upper: 0.210
  JPY:
    lower: 20.0
    upper: 22.0
```

### 3. 一次性查询

```bash
python -m realmoon.app --config my_config.yml --once --log-level DEBUG
```

### 4. 长期监控

```bash
python -m realmoon.app --config my_config.yml
```

应用会按照配置中的 `interval_seconds` 周期运行，支持使用 `Ctrl+C` 安全退出。

## 阈值预警

当汇率突破配置的上下阈值时，程序会输出预警信息，例如：

```
[2024-01-01T12:00:00] USD rate 0.151000 crossed upper threshold 0.150000
```

可以将程序输出重定向至日志系统或以管道方式接入自定义的通知模块。

> **提示**：项目内置了一个轻量级 YAML 解析器，足以支持示例配置文件中的语法。
> 若需兼容更复杂的 YAML 特性，请安装 `PyYAML`（已在 `requirements.txt` 中列出）。

## 运行测试

```bash
pytest
```

## 注意事项

- exchangerate.host 接口免费且无需 API Key，但其速率限制和 SLA 需要使用者自行评估。
- 在无网络环境下，可以通过在测试或运行时注入自定义的 `ExchangeRateFetcher` 来实现离线运行。
