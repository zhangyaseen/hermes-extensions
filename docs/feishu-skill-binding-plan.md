# 飞书 Skill Binding 实施计划

## 目标

在 hermes-extensions repo 中实现飞书 channel skill binding 功能，通过 Plugin Hook 方式（非文件补丁）实现零侵入扩展。

## 为什么选择 Plugin Hook 而非文件补丁？

### 文件补丁的问题

1. **已过时**：`patch-feishu.py` 在飞书迁移到 plugin 架构后已变成 no-op
2. **维护成本高**：依赖标记字符串匹配，上游重构会导致补丁失效
3. **不符合方向**：Hermes 正在从文件修改转向 plugin 架构

### Plugin Hook 的优势

1. **零侵入**：不修改 hermes-agent 源码
2. **升级安全**：plugin 机制是官方推荐的扩展方式
3. **可复用**：同样的模式可以用于其他平台的 skill binding
4. **易管理**：通过 hermes-extensions 统一管理

## 实施步骤

### Step 1: 创建 Plugin 目录结构

```bash
cd /Users/zhangyixiang/workspace/github/hermes-skills/hermes-extensions
mkdir -p plugins/feishu-skill-binding
```

### Step 2: 实现 Plugin 核心逻辑

**plugins/feishu-skill-binding/plugin.yaml**

```yaml
name: feishu-skill-binding
version: "1.0.0"
description: "飞书 channel skill binding — 根据群聊 ID 自动加载 skill"
provides_hooks:
  - pre_gateway_dispatch
```

**plugins/feishu-skill-binding/__init__.py**

```python
"""飞书 skill binding plugin"""

def register(ctx):
    """注册 pre_gateway_dispatch hook"""
    from .handler import on_pre_gateway_dispatch
    ctx.register_hook("pre_gateway_dispatch", on_pre_gateway_dispatch)
```

**plugins/feishu-skill-binding/handler.py**

```python
"""
pre_gateway_dispatch hook: 为飞书消息注入 auto_skill

工作原理：
1. 拦截所有飞书消息
2. 从 config.extra 读取 channel_skill_bindings
3. 调用 resolve_channel_skills() 解析绑定的 skill
4. 设置 event.auto_skill，Gateway 会自动在新会话中加载

零侵入设计：
- 不修改任何 hermes-agent 源码
- 直接修改 event 对象（MessageEvent 是可变的 dataclass）
- 返回 None，让 Gateway 继续正常处理
"""

import logging

logger = logging.getLogger("feishu-skill-binding")


def on_pre_gateway_dispatch(event, gateway, **kwargs):
    """拦截飞书消息，注入 auto_skill
    
    Args:
        event: MessageEvent 对象
        gateway: Gateway 实例
        **kwargs: 接受未来 Hermes 版本新增的参数
    
    Returns:
        None: 继续正常处理
    """
    # 仅处理飞书平台
    if event.source.platform.value != "feishu":
        return None
    
    chat_id = event.source.chat_id
    thread_id = event.source.thread_id
    
    # 获取飞书 adapter
    try:
        from gateway.config import Platform
        feishu_adapter = gateway.adapters.get(Platform.FEISHU)
    except Exception as e:
        logger.warning(f"[feishu-skill-binding] 获取飞书 adapter 失败: {e}")
        return None
    
    if not feishu_adapter:
        return None
    
    # 解析 skill bindings
    try:
        from gateway.platforms.base import resolve_channel_skills
        skills = resolve_channel_skills(
            feishu_adapter.config.extra,
            chat_id,
            thread_id
        )
    except Exception as e:
        logger.warning(f"[feishu-skill-binding] 解析 skill bindings 失败: {e}")
        return None
    
    # 如果匹配，设置 auto_skill
    if skills:
        event.auto_skill = skills
        logger.info(
            f"[feishu-skill-binding] 注入 skills={skills} "
            f"chat_id={chat_id} thread_id={thread_id}"
        )
    
    return None  # 继续正常处理
```

### Step 3: 扩展 install.sh

修改 `install.sh`，添加 plugin symlink 逻辑：

```bash
# 新增：Plugin 目录
PLUGIN_DIRS=("feishu-skill-binding")

install() {
    # ... 现有逻辑 ...
    
    # 4. Symlink plugins
    mkdir -p "${HERMES_HOME}/plugins"
    for plugin in "${PLUGIN_DIRS[@]}"; do
        target="${HERMES_HOME}/plugins/${plugin}"
        source="${SCRIPT_DIR}/plugins/${plugin}"
        
        if [ ! -d "$source" ]; then
            echo "ERROR: plugin directory not found: ${source}"
            continue
        fi
        
        if [ -L "$target" ]; then
            current_target=$(readlink "$target")
            if [ "$current_target" = "$source" ]; then
                echo "SKIP: plugin ${plugin} already symlinked"
                continue
            else
                echo "UPDATE: plugin ${plugin} points to ${current_target}, updating..."
                rm "$target"
            fi
        elif [ -d "$target" ]; then
            echo "BACKUP: plugin ${plugin} exists as directory, renaming to ${plugin}.bak"
            mv "$target" "${target}.bak"
        fi
        
        ln -s "$source" "$target"
        echo "LINKED: plugin ${plugin} -> ${source}"
    done
}

uninstall() {
    # ... 现有逻辑 ...
    
    # 移除 plugin symlinks
    for plugin in "${PLUGIN_DIRS[@]}"; do
        target="${HERMES_HOME}/plugins/${plugin}"
        if [ -L "$target" ]; then
            rm "$target"
            echo "REMOVED: plugin ${plugin}"
        fi
    done
}
```

### Step 4: 配置示例

在 `~/.hermes/config.yaml` 中添加：

```yaml
platforms:
  feishu:
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

**飞书 Thread 支持说明**：

飞书支持两种群聊类型：
- **普通群聊（group）**：无 thread 概念，只能基于 `chat_id` 绑定
- **话题群聊（topic/thread/forum）**：支持独立 thread，可以基于 `chat_id` 或 `thread_id` 绑定
  - 在 thread 中发送的消息会继承 parent chat 的 skill binding
  - 也可以为特定 thread 单独配置 skill binding

详见：[飞书 Thread ID 验证报告](./feishu-thread-id-verification.md)

### Step 5: 测试验证

```bash
# 1. 安装 plugin
cd /Users/zhangyixiang/workspace/github/hermes-skills/hermes-extensions
./install.sh

# 2. 验证 symlink
ls -la ~/.hermes/plugins/feishu-skill-binding/

# 3. 重启 Hermes Gateway
hermes gateway restart

# 4. 查看日志，确认 plugin 加载
tail -f ~/.hermes/logs/gateway.log | grep "feishu-skill-binding"

# 5. 在配置的群聊中发送消息，验证 skill 自动加载
```

## 文件清单

```
新增文件：
  hermes-extensions/plugins/feishu-skill-binding/__init__.py
  hermes-extensions/plugins/feishu-skill-binding/handler.py
  hermes-extensions/plugins/feishu-skill-binding/plugin.yaml
  hermes-extensions/docs/feishu-skill-binding-requirements.md
  hermes-extensions/docs/feishu-skill-binding-plan.md (本文档)

修改文件：
  hermes-extensions/install.sh (添加 plugin symlink 逻辑)
  hermes-extensions/README.md (添加 plugin 管理说明)
```

## 时间估算

| 步骤 | 预计时间 |
|------|----------|
| 创建 plugin 目录和文件 | 30 分钟 |
| 扩展 install.sh | 30 分钟 |
| 测试验证 | 1 小时 |
| 文档更新 | 30 分钟 |
| **总计** | **2.5 小时** |

## 后续优化

1. **支持更多平台**：将同样的模式应用到 WeCom、QQ 等平台
2. **动态配置**：支持运行时修改 channel_skill_bindings，无需重启
3. **监控告警**：添加 skill 加载失败的告警机制
4. **性能优化**：缓存 skill binding 解析结果，减少重复查询

## 测试用例

### 正常路径

- [ ] 普通群聊发送消息，skill 自动加载
- [ ] 话题群聊发送消息（非 thread），skill 自动加载
- [ ] 话题群聊 thread 中发送消息，继承 parent chat 的 skill
- [ ] 话题群聊 thread 有独立配置，使用 thread 的 skill
- [ ] 未配置的群聊发送消息，无 skill 加载
- [ ] 配置多个 skill，全部加载

### 边界情况

- [ ] `channel_skill_bindings` 为空数组
- [ ] 配置的 skill 不存在（应跳过并记录 warning）
- [ ] chat_id / thread_id 格式错误
- [ ] 飞书 adapter 未启用
- [ ] 多个 plugin 同时拦截消息

### 集成测试

- [ ] 与 `pipeline-routing` plugin 共存
- [ ] Hermes 升级后功能保持
- [ ] 配置热更新（无需重启）

## 参考

- [需求文档](./feishu-skill-binding-requirements.md)
- [a-stock-message-analyzer plugin 实现](../../skills/a-stock-message-analyzer/plugin/pipeline-routing/)
- [Hermes Plugin 开发指南](https://hermes-agent.nousresearch.com/docs/plugins)
