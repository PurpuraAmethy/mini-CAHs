# 配置

miniCAH 的配置按下面这个优先级合并：

```
CLI 显式参数 > 环境变量 > 项目 .miniCAH.toml > 全局 ~/.config/miniCAH/config.toml > 代码默认
```

## Provider profile

provider 是 TOML 里的一段配置 profile，名字（如 `deepseek` `openai` `anthropic`）只用于人类辨识；真正决定走哪个协议的是 `protocol` 字段，目前支持 `openai` 和 `anthropic` 两种。

### .miniCAH.toml 示例

放在仓库根目录，**不要提交真实 key**（默认已被 `.gitignore` 忽略）：

```toml
provider = "deepseek"

[providers.deepseek]
protocol = "anthropic"
api_key = "sk-..."
base_url = "https://api.deepseek.com/anthropic"
model = "deepseek-v4-pro"

[providers.openai]
protocol = "openai"
api_key = "sk-..."
base_url = "https://api.openai.com/v1"
model = "gpt-5.4"

[providers.anthropic]
protocol = "anthropic"
api_key = "sk-ant-..."
base_url = "https://api.anthropic.com"
model = "claude-sonnet-4-6"
```

切 provider：

```bash
miniCAH                       # 用 toml 里的默认 provider
miniCAH --provider openai     # 临时切换
miniCAH --provider anthropic --model claude-opus-4-6
```

## 环境变量

不写 toml 也能跑——只设环境变量即可：

| 变量 | 用途 |
|------|------|
| `MINI-CAH_PROVIDER` | 默认 provider |
| `MINI-CAH_API_KEY` / `MINI-CAH_BASE_URL` / `MINI-CAH_MODEL` | 通用 override |
| `ANTHROPIC_API_KEY` / `ANTHROPIC_BASE_URL` / `ANTHROPIC_MODEL` | Anthropic |
| `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `OPENAI_MODEL` | OpenAI |
| `DEEPSEEK_API_KEY` / `DEEPSEEK_BASE_URL` / `DEEPSEEK_MODEL` | DeepSeek |

兼容历史 `.env`：`MINI-CAH_OPENAI_*` / `MINI-CAH_ANTHROPIC_*` / `MINI-CAH_DEEPSEEK_*` 仍然能用。

## 全局配置

`~/.config/miniCAH/config.toml` 适合放跨项目都用的 provider profile。项目 `.miniCAH.toml` 覆盖它，CLI 参数再覆盖项目。

## CLI 参数

```bash
miniCAH --provider deepseek --model deepseek-v4-pro
miniCAH --api-key sk-... --base-url https://...
miniCAH --max-steps 50 --max-new-tokens 4096
miniCAH --temperature 0.0
miniCAH --approval ask          # ask | auto | never
miniCAH --sandbox best_effort   # off | best_effort | required
miniCAH --no-auto-dream         # 关闭后台 memory 整合
miniCAH --cwd /path/to/repo     # 切换工作目录
miniCAH --resume latest         # 续接上一个 session
miniCAH --config /path/to/custom.toml
```

跑 `miniCAH --help` 看完整参数。

## 默认值速查

| 项 | 默认 |
|----|------|
| `max-steps` | 50 |
| `max-new-tokens` | Anthropic 32000 / OpenAI 8192 / DeepSeek 8192 / fallback 4096 |
| `temperature` | 0.2 |
| `approval` | `ask` |
| `sandbox` | `off` |
| `dream-interval` | 24 小时 |
| `dream-min-sessions` | 5 |

## 调试

- `/session` 查看 session 文件路径和当前 runtime 标识
- `/context` 查看上下文用量切片
- `/usage` 查看 token / call 数
- 所有事件流写到 `.miniCAH/sessions/<id>.events.jsonl`，可以用 `tail -f` 观察
- 每次运行的 trace 在 `.miniCAH/runs/<run_id>/trace.jsonl`
