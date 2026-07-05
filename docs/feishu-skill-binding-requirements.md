# 飞书 Skill Binding 功能需求文档

## 概述

为飞书平台添加 channel skill binding 功能，允许在 `config.yaml` 中配置特定群聊/会话自动加载指定的 skill。

## 背景

### 当前状态

- **Discord / Slack / Telegram** 等平台已支持 `channel_skill_bindings` 配置
- **飞书** 尚未实现此功能
- Hermes Agent 核心提供了 `resolve_channel_skills()` 函数（`gateway/platforms/base.py:2182`）
- 飞书 adapter 未调用此函数，导致无法自动加载 skill

### 架构现状

```
Hermes Agent 架构演进：
  旧架构: gateway/platforms/feishu.py (文件补丁方式)
  新架构: plugins/platforms/feishu/adapter.py (plugin 方式)

扩展机制演进：
  旧方式: 文件补丁 (hermes-extensions/patches/)
  新方式: Plugin Hook (pre_gateway_dispatch, on_session_start, etc.)
```

## 需求

### 功能需求

1. **配置支持**：在 `config.yaml` 的飞书平台配置中支持 `channel_skill_bindings`
2. **自动加载**：飞书消息到达时，根据 `chat_id` / `thread_id` 自动加载绑定的 skill
3. **仅新会话生效**：skill 仅在新会话开始时加载，不影响已有会话

### 配置示例

```yaml
platforms:
  feishu:
    extra:
      channel_skill_bindings:
        # 场景 1：普通群聊（基于 chat_id）
        - id: "oc_regular_group"
          skills: ["research"]
        
        # 场景 2：话题群聊（所有 thread 共享，基于 chat_id）
        - id: "oc_forum_chat"
          skills: ["a-stock-message-analyzer"]
        
        # 场景 3：特定 thread（基于 thread_id，优先级高于 parent chat）
        - id: "omt_specific_thread"
          skill: "creative"
```

### 飞书 Thread 支持

飞书支持两种群聊类型：

| 类型 | Chat Type | Thread 支持 | 说明 |
|------|-----------|------------|------|
| 普通群聊 | `group` | ❌ 无 | 所有消息在同一个聊天流中 |
| 话题群聊 | `topic`/`thread`/`forum` | ✅ 有 | 类似 Discord Forum，支持独立 thread |

**Skill Binding 行为**：

1. **普通群聊消息**：
   - `event.source.chat_id` = 群聊 ID
   - `event.source.thread_id` = `None`
   - 匹配 `channel_skill_bindings` 中的 `chat_id`

2. **话题群聊消息（非 thread）**：
   - `event.source.chat_id` = 话题群聊 ID
   - `event.source.thread_id` = `None`
   - 匹配 `channel_skill_bindings` 中的 `chat_id`

3. **话题群聊消息（在 thread 中）**：
   - `event.source.chat_id` = 话题群聊 ID
   - `event.source.thread_id` = thread ID
   - 优先匹配 `thread_id`，如果没有则继承 `chat_id` 的 binding

**代码证据**：
- Thread ID 提取：`plugins/platforms/feishu/adapter.py:3200`
- Chat 类型映射：`plugins/platforms/feishu/adapter.py:3959-3967`
- 测试用例：`tests/gateway/test_feishu.py:1997`（`test_send_uses_metadata_reply_target_for_threaded_feishu_topic`）

详见：[飞书 Thread ID 验证报告](./feishu-thread-id-verification.md)

### 技术需求

1. **零侵入**：不修改 hermes-agent 源码
2. **升级安全**：Hermes 升级后功能保持有效
3. **可管理**：通过 hermes-extensions repo 统一管理

## 方案设计

### 方案对比

| 方案 | 实现方式 | 优点 | 缺点 | 推荐 |
|------|----------|------|------|------|
| A. 文件补丁 | 修改 feishu/adapter.py | 与现有 hermes-extensions 模式一致 | 文件补丁正在过时，维护成本高 | ❌ |
| B. Plugin Hook | 创建独立 plugin 使用 pre_gateway_dispatch | 符合 Hermes 架构方向，零侵入 | 需要扩展 hermes-extensions 管理 plugin | ✅ |

### 推荐方案：Plugin Hook

**架构设计**：

```
hermes-extensions/
├── patches/                    # 现有：文件补丁
│   ├── apply-custom-patches.py
│   ├── patch-feishu.py
│   └── hermes-custom-patches.patch
├── plugins/                    # 新增：plugin 管理
│   └── feishu-skill-binding/
│       ├── __init__.py         # register(ctx) 入口
│       ├── handler.py          # pre_gateway_dispatch hook 实现
│       └── plugin.yaml         # plugin 元数据
├── hooks/
│   └── post-merge
└── install.sh                  # 扩展：同时 symlink plugins
```

**工作流程**：

```
1. 飞书消息到达
   ↓
2. Gateway 调用 pre_gateway_dispatch hook
   ↓
3. feishu-skill-binding plugin 拦截
   ↓
4. 从 config.extra 读取 channel_skill_bindings
   ↓
5. 调用 resolve_channel_skills(config.extra, chat_id, thread_id)
   ↓
6. 如果匹配，设置 event.auto_skill = skills
   ↓
7. 返回 None，继续正常处理
   ↓
8. Gateway 在新会话中自动加载 skill
```

**核心代码**：

```python
# plugins/feishu-skill-binding/handler.py

def on_pre_gateway_dispatch(event, gateway, **kwargs):
    """拦截飞书消息，注入 auto_skill"""
    # 仅处理飞书平台
    if event.source.platform.value != "feishu":
        return None
    
    chat_id = event.source.chat_id
    thread_id = event.source.thread_id
    
    # 获取飞书 adapter
    from gateway.config import Platform
    feishu_adapter = gateway.adapters.get(Platform.FEISHU)
    if not feishu_adapter:
        return None
    
    # 解析 skill bindings
    from gateway.platforms.base import resolve_channel_skills
    skills = resolve_channel_skills(
        feishu_adapter.config.extra,
        chat_id,
        thread_id
    )
    
    if skills:
        # 直接修改 event 对象（零侵入）
        event.auto_skill = skills
        logger.info(f"[feishu-skill-binding] 注入 skills={skills} chat_id={chat_id}")
    
    return None  # 继续正常处理
```

## 实施计划

### Phase 1: 创建 Plugin（1-2 小时）

- [ ] 创建 `plugins/feishu-skill-binding/` 目录
- [ ] 实现 `handler.py`（pre_gateway_dispatch hook）
- [ ] 创建 `plugin.yaml`（plugin 元数据）
- [ ] 创建 `__init__.py`（register 入口）

### Phase 2: 扩展 install.sh（30 分钟）

- [ ] 添加 plugin symlink 逻辑
- [ ] 更新安装/卸载流程
- [ ] 添加验证逻辑

### Phase 3: 测试验证（1 小时）

- [ ] 测试 plugin 加载
- [ ] 测试 skill 注入
- [ ] 测试多 skill 绑定
- [ ] 测试 thread_id 继承

### Phase 4: 文档更新（30 分钟）

- [ ] 更新 README.md
- [ ] 添加配置示例
- [ ] 添加故障排查指南

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| Hermes 升级改变 hook 机制 | plugin 失效 | 监控 Hermes release notes，hermes-extensions 快速适配 |
| `resolve_channel_skills` 函数签名变化 | plugin 报错 | 使用 try-except 包裹，降级为无 skill binding |
| 多个 plugin 同时修改 event | 冲突 | 遵循 Hermes plugin 规范，不返回 skip/rewrite |

## 成功标准

1. ✅ 飞书群聊消息能自动加载绑定的 skill
2. ✅ 配置变更后立即生效（无需重启）
3. ✅ Hermes 升级后功能保持有效
4. ✅ 日志清晰，便于故障排查

## 参考资料

- Discord channel_skill_bindings 实现：`plugins/platforms/discord/adapter.py:4550`
- resolve_channel_skills 函数：`gateway/platforms/base.py:2182`
- pre_gateway_dispatch hook 调用点：`gateway/run.py:8596`
- a-stock-message-analyzer plugin 示例：`skills/a-stock-message-analyzer/plugin/pipeline-routing/`

## 附录：相关文件路径

```
源码位置：
  hermes-agent/gateway/platforms/base.py:1756         # MessageEvent.auto_skill 定义
  hermes-agent/gateway/platforms/base.py:2182         # resolve_channel_skills 函数
  hermes-agent/gateway/run.py:8596                    # pre_gateway_dispatch hook 调用
  hermes-agent/gateway/run.py:10514                   # auto_skill 消费点

Plugin 位置：
  ~/.hermes/plugins/feishu-skill-binding/             # 运行时 plugin 目录
  hermes-extensions/plugins/feishu-skill-binding/     # 源码管理目录

配置位置：
  ~/.hermes/config.yaml                               # channel_skill_bindings 配置
```
