# 飞书 Skill Binding Plugin 部署指南

## 快速开始

### 1. 安装 Plugin

```bash
cd /Users/zhangyixiang/workspace/github/hermes-skills/hermes-extensions
./install.sh
```

**预期输出**：
```
Installing hermes-extensions...
LINKED: apply-custom-patches.py -> /path/to/patches/apply-custom-patches.py
LINKED: patch-feishu.py -> /path/to/patches/patch-feishu.py
LINKED: hermes-custom-patches.patch -> /path/to/patches/hermes-custom-patches.patch
LINKED: plugin feishu-skill-binding -> /path/to/plugins/feishu-skill-binding
INSTALLED: post-merge hook -> ~/.hermes/hermes-agent/.git/hooks/post-merge

Installation complete.
```

### 2. 验证安装

```bash
# 检查 plugin symlink
ls -la ~/.hermes/plugins/feishu-skill-binding/
```

**预期输出**：
```
lrwxr-xr-x  1 user  staff    68B  __init__.py -> /path/to/hermes-extensions/plugins/feishu-skill-binding/__init__.py
lrwxr-xr-x  1 user  staff    65B  handler.py -> /path/to/hermes-extensions/plugins/feishu-skill-binding/handler.py
lrwxr-xr-x  1 user  staff    67B  plugin.yaml -> /path/to/hermes-extensions/plugins/feishu-skill-binding/plugin.yaml
```

### 3. 配置 Skill Bindings

编辑 `~/.hermes/config.yaml`，在飞书平台配置中添加 `channel_skill_bindings`：

```yaml
platforms:
  feishu:
    # ... 其他配置 ...
    extra:
      channel_skill_bindings:
        # 场景 1：普通群聊（基于 chat_id）
        - id: "oc_regular_group"
          skills: ["research"]
        
        # 场景 2：话题群聊（所有 thread 共享）
        - id: "oc_forum_chat"
          skills: ["a-stock-message-analyzer"]
        
        # 场景 3：特定 thread（优先级高于 parent chat）
        - id: "omt_specific_thread"
          skill: "creative"
```

**配置说明**：
- `id`: 群聊 ID（chat_id）或 Thread ID（thread_id）
- `skills`: skill 列表（数组）
- `skill`: 单个 skill（字符串，与 skills 二选一）

**如何获取 Chat ID / Thread ID**：
- 在飞书群聊中发送消息，查看 Gateway 日志中的 `chat_id`
- 在 Thread 中发送消息，查看日志中的 `thread_id`

### 4. 重启 Gateway

```bash
hermes gateway restart
```

### 5. 验证功能

```bash
# 查看日志，确认 plugin 加载
tail -f ~/.hermes/logs/gateway.log | grep "feishu-skill-binding"
```

**预期日志**：
```
[feishu-skill-binding] 注入 skills=['research'] chat_id=oc_regular_group thread_id=None
[feishu-skill-binding] 注入 skills=['a-stock-message-analyzer'] chat_id=oc_forum_chat thread_id=omt_thread_123
```

**测试步骤**：
1. 在配置的群聊中发送消息
2. 观察是否自动加载绑定的 skill
3. 检查日志确认 skill 注入成功

---

## 配置示例

### 示例 1：普通群聊

```yaml
platforms:
  feishu:
    extra:
      channel_skill_bindings:
        - id: "oc_abc123"
          skills: ["research", "web-search"]
```

**行为**：在 `oc_abc123` 群聊中发送消息时，自动加载 `research` 和 `web-search` skill。

### 示例 2：话题群聊（所有 Thread 共享）

```yaml
platforms:
  feishu:
    extra:
      channel_skill_bindings:
        - id: "oc_forum_xyz"
          skills: ["a-stock-message-analyzer"]
```

**行为**：
- 在话题群聊 `oc_forum_xyz` 的任意 Thread 中发送消息
- 自动加载 `a-stock-message-analyzer` skill
- Thread 继承 parent chat 的配置

### 示例 3：特定 Thread（独立配置）

```yaml
platforms:
  feishu:
    extra:
      channel_skill_bindings:
        # Parent chat 配置
        - id: "oc_forum_xyz"
          skills: ["research"]
        
        # 特定 Thread 配置（优先级更高）
        - id: "omt_thread_456"
          skills: ["creative-writing"]
```

**行为**：
- 在 `omt_thread_456` Thread 中发送消息 → 加载 `creative-writing`
- 在 `oc_forum_xyz` 的其他 Thread 中发送消息 → 加载 `research`

---

## 故障排查

### 问题 1：Plugin 未加载

**症状**：日志中没有 `[feishu-skill-binding]` 相关记录

**排查步骤**：
```bash
# 1. 检查 plugin 是否安装
ls -la ~/.hermes/plugins/feishu-skill-binding/

# 2. 检查 Gateway 日志
grep -i "plugin" ~/.hermes/logs/gateway.log

# 3. 重启 Gateway
hermes gateway restart
```

### 问题 2：Skill 未注入

**症状**：消息发送后 skill 未自动加载

**排查步骤**：
```bash
# 1. 检查配置是否正确
grep -A 10 "channel_skill_bindings" ~/.hermes/config.yaml

# 2. 检查 chat_id / thread_id 是否匹配
tail -f ~/.hermes/logs/gateway.log | grep "chat_id"

# 3. 检查 skill 是否存在
ls ~/.hermes/skills/
```

### 问题 3：Thread 继承失败

**症状**：Thread 消息未继承 parent chat 的 skill

**排查步骤**：
```bash
# 1. 检查 thread_id 是否正确提取
tail -f ~/.hermes/logs/gateway.log | grep "thread_id"

# 2. 检查配置中是否有 parent chat 的 binding
grep -B 2 -A 2 "oc_forum" ~/.hermes/config.yaml

# 3. 确认飞书群聊类型是"话题群聊"（topic/thread/forum）
```

---

## 卸载

```bash
cd /Users/zhangyixiang/workspace/github/hermes-skills/hermes-extensions
./install.sh --uninstall
```

**预期输出**：
```
Uninstalling hermes-extensions...
REMOVED: apply-custom-patches.py
REMOVED: patch-feishu.py
REMOVED: hermes-custom-patches.patch
REMOVED: plugin feishu-skill-binding
REMOVED: post-merge hook
Done. Original files are preserved in this repo.
```

---

## 升级

当 hermes-extensions 有更新时：

```bash
# 1. 拉取最新代码
cd /Users/zhangyixiang/workspace/github/hermes-skills/hermes-extensions
git pull

# 2. 重新运行安装脚本
./install.sh

# 3. 重启 Gateway
hermes gateway restart
```

**注意**：
- install.sh 会自动更新 symlink
- 配置保持不变
- 如果 post-merge hook 已安装，`git pull` 会自动触发安装

---

## 技术架构

```
飞书消息
  ↓
Gateway 接收
  ↓
pre_gateway_dispatch hook 触发
  ↓
feishu-skill-binding plugin 拦截
  ↓
解析 channel_skill_bindings 配置
  ↓
调用 resolve_channel_skills()
  ↓
设置 event.auto_skill
  ↓
Gateway 创建新会话时加载 skill
  ↓
正常处理消息
```

---

## 参考资料

- **Plugin 源码**：`plugins/feishu-skill-binding/`
- **实施报告**：`iterations/CR-20260705-001-feishu-skill-binding/IMPLEMENTATION_COMPLETE.md`
- **架构分析**：`iterations/CR-20260705-001-feishu-skill-binding/architecture/architecture.md`
- **需求文档**：`docs/feishu-skill-binding-requirements.md`
- **Thread 验证**：`docs/feishu-thread-id-verification.md`

---

## 常见问题

### Q: 配置变更后需要重启 Gateway 吗？

**A**: 不需要。Gateway 会动态读取配置，变更后立即生效。

### Q: 可以同时绑定多个 skill 吗？

**A**: 可以。使用 `skills` 数组配置多个 skill：
```yaml
- id: "oc_chat"
  skills: ["research", "web-search", "code-review"]
```

### Q: Thread 配置和 parent chat 配置冲突时，哪个优先？

**A**: Thread 配置优先。匹配顺序：
1. 精确匹配 thread_id
2. 回退到 parent chat_id

### Q: 如何查看当前加载了哪些 skill？

**A**: 查看 Gateway 日志：
```bash
tail -f ~/.hermes/logs/gateway.log | grep "auto_skill"
```

### Q: Plugin 会影响其他平台吗？

**A**: 不会。Plugin 仅处理飞书平台消息（`event.source.platform.value == "feishu"`）。

---

## 联系与支持

如有问题，请查看：
1. Gateway 日志：`~/.hermes/logs/gateway.log`
2. Plugin 源码：`plugins/feishu-skill-binding/handler.py`
3. 实施报告：`iterations/CR-20260705-001-feishu-skill-binding/IMPLEMENTATION_COMPLETE.md`
