# hermes-extensions

Hermes Agent 核心补丁与插件机制管理。

将 Hermes Agent 的自定义补丁脚本和扩展插件纳入版本管理，通过 git submodule 集成到 [hermes-skills](https://github.com/zhangyaseen/hermes-skills)。

## 背景

`hermes update` 会拉取上游更新，可能覆盖本地修改。此 repo 管理两类扩展：

### 1. 文件补丁（patches/）

需要在每次 update 后自动重新应用的代码补丁：

| 补丁 | 目标文件 | 作用 | 状态 |
|------|----------|------|------|
| `apply-custom-patches.py` | `agent/auxiliary_client.py` | 注册 `alibaba: qwen3.7-plus` 到 `_PROVIDER_VISION_MODELS`，启用多模态图片输入 | ✅ 活跃 |
| `patch-feishu.py` | `gateway/platforms/feishu.py` | 添加 pipeline routing 功能（`pipeline` 字段 + 路由方法） | ⚠️ 已过时（飞书已迁移到 plugin 架构） |
| `hermes-custom-patches.patch` | (legacy) | 旧版 patch 文件，大部分已禁用，保留兼容 | ⚠️ Legacy |

### 2. 扩展插件（plugins/）

通过 Hermes Plugin API 实现的零侵入扩展，符合 Hermes 架构演进方向：

| 插件 | Hook | 作用 | 状态 |
|------|------|------|------|
| `feishu-skill-binding` | `pre_gateway_dispatch` | 飞书 channel skill binding，根据群聊 ID 自动加载 skill | 📝 计划中 |

**为什么优先使用 Plugin 而非文件补丁？**

- ✅ **零侵入**：不修改 hermes-agent 源码
- ✅ **升级安全**：plugin 机制是官方推荐的扩展方式
- ✅ **维护成本低**：不依赖标记字符串匹配，不受上游重构影响
- ✅ **可复用**：同样的模式可以用于其他平台

## 安装

```bash
# 通过 hermes-skills submodule 安装（推荐）
cd hermes-skills/hermes-extensions
./install.sh

# 或独立安装
git clone git@github.com:zhangyaseen/hermes-extensions.git
cd hermes-extensions
./install.sh
```

安装脚本会：
1. 将 `patches/` 下的文件 symlink 到 `~/.hermes/scripts/`
2. 将 `hooks/post-merge` 复制到 `~/.hermes/hermes-agent/.git/hooks/post-merge`
3. 将 `plugins/` 下的插件目录 symlink 到 `~/.hermes/plugins/`

## 验证

```bash
# 检查 symlink
ls -la ~/.hermes/scripts/apply-custom-patches.py
# 应指向 hermes-extensions/patches/apply-custom-patches.py

# 检查 hook
cat ~/.hermes/hermes-agent/.git/hooks/post-merge

# 模拟 hermes update 触发
cd ~/.hermes/hermes-agent && git merge --ff-only origin/main
cat /tmp/hermes-post-merge.log
```

## 卸载

```bash
./install.sh --uninstall
```

移除 symlink 和 git hook，原始文件保留在本 repo 中。

## 目录结构

```
hermes-extensions/
├── patches/                          # 文件补丁（旧方式）
│   ├── apply-custom-patches.py      # auxiliary_client.py 补丁
│   ├── patch-feishu.py              # feishu.py pipeline routing 补丁
│   └── hermes-custom-patches.patch  # legacy patch 文件
├── plugins/                          # 扩展插件（新方式）
│   └── feishu-skill-binding/        # 飞书 skill binding plugin
│       ├── __init__.py
│       ├── handler.py
│       └── plugin.yaml
├── docs/                             # 文档
│   ├── feishu-skill-binding-requirements.md
│   └── feishu-skill-binding-plan.md
├── hooks/
│   └── post-merge                   # git hook，update 后自动打补丁
├── install.sh                       # 安装/卸载脚本
└── README.md
```

## 工作原理

### 文件补丁（patches/）

```
hermes update
  → git pull (触发 post-merge hook)
  → post-merge hook 调用 ~/.hermes/scripts/apply-custom-patches.py
  → post-merge hook 调用 ~/.hermes/scripts/patch-feishu.py
  → 补丁通过 symlink 指向本 repo 的 patches/ 目录
  → 补丁应用完成，日志写入 /tmp/hermes-post-merge.log
```

### 扩展插件（plugins/）

```
Hermes Gateway 启动
  → 扫描 ~/.hermes/plugins/ 目录
  → 加载每个 plugin 的 __init__.py
  → 调用 register(ctx) 注册 hooks
  → Plugin 开始监听事件
  
以 feishu-skill-binding 为例：
  飞书消息到达
    → Gateway 调用 pre_gateway_dispatch hook
    → feishu-skill-binding plugin 拦截
    → 解析 channel_skill_bindings 配置
    → 注入 event.auto_skill
    → Gateway 在新会话中自动加载 skill
```

## 插件开发指南

### 创建新插件

1. 在 `plugins/` 下创建目录：

```bash
mkdir -p plugins/my-plugin
```

2. 创建 `plugin.yaml`：

```yaml
name: my-plugin
version: "1.0.0"
description: "My custom plugin"
provides_hooks:
  - pre_gateway_dispatch  # 或其他 hook
```

3. 创建 `__init__.py`：

```python
def register(ctx):
    from .handler import my_handler
    ctx.register_hook("pre_gateway_dispatch", my_handler)
```

4. 创建 `handler.py`：

```python
def my_handler(event, gateway, **kwargs):
    # 处理逻辑
    return None  # 或 {"action": "skip"} 等
```

5. 更新 `install.sh` 的 `PLUGIN_DIRS` 数组

6. 运行 `./install.sh` 安装插件

### 可用的 Hooks

| Hook | 触发时机 | 用途 |
|------|----------|------|
| `pre_gateway_dispatch` | 消息进入 Gateway 前 | 拦截/修改消息 |
| `on_session_start` | 会话开始 | 初始化会话状态 |
| `pre_llm_call` | 调用 LLM 前 | 修改 prompt |
| `post_llm_call` | LLM 返回后 | 处理响应 |
| `pre_tool_call` | 调用工具前 | 拦截/修改工具调用 |
| `post_tool_call` | 工具返回后 | 处理工具结果 |
| `on_session_end` | 会话结束 | 清理资源 |

更多 hook 参考：[Hermes Plugin 文档](https://hermes-agent.nousresearch.com/docs/plugins)

## 注意事项

### 文件补丁

- 补丁脚本通过**标记字符串匹配**而非行号定位，适应上游代码行数变化
- 如果上游代码重构导致标记字符串不存在，补丁会跳过并记录 warning
- 定期检查 `/tmp/hermes-post-merge.log` 确认补丁正常应用

### 扩展插件

- 插件通过 symlink 安装，修改源码后立即生效（无需重新安装）
- 插件使用 Hermes 官方 Plugin API，升级安全
- 插件日志写入 Hermes Gateway 日志（`~/.hermes/logs/gateway.log`）
- 如果 Hermes 改变 hook 机制，需要更新插件代码

## 飞书 Skill Binding 插件

### 功能

为飞书平台添加 channel skill binding 功能，允许在 `config.yaml` 中配置特定群聊自动加载指定的 skill。

### 配置示例

在 `~/.hermes/config.yaml` 中添加：

```yaml
platforms:
  feishu:
    extra:
      channel_skill_bindings:
        - id: "oc_xxxxx"  # 飞书群聊 ID
          skills: ["a-stock-message-analyzer", "research"]
        - id: "oc_yyyyy"
          skill: "creative"  # 单个 skill 也可以用字符串
```

### 工作原理

1. 飞书消息到达时，plugin 拦截事件
2. 根据 `chat_id` / `thread_id` 查询 `channel_skill_bindings` 配置
3. 如果匹配，设置 `event.auto_skill = skills`
4. Gateway 在新会话中自动加载绑定的 skill

### 状态

📝 **计划中** — 详见 [需求文档](./docs/feishu-skill-binding-requirements.md) 和 [实施计划](./docs/feishu-skill-binding-plan.md)
