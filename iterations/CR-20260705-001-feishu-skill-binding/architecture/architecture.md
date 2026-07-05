# 架构分析（Architecture Analysis）

**迭代ID**: CR-20260705-001-feishu-skill-binding  
**日期**: 2026-07-05  
**主导角色**: Architect（架构分析）  
**分类**: brownfield-poor

---

## 现有架构分析

⚠️ [行为观察，意图待确认]

### Hermes Agent 架构演进

#### 1.0 架构（旧）

```
Hermes Agent 1.0
├── gateway/
│   ├── platforms/
│   │   ├── base.py              # 基础平台类
│   │   ├── feishu.py            # 飞书平台实现（直接修改）
│   │   ├── discord.py           # Discord 平台实现
│   │   └── slack.py             # Slack 平台实现
│   ├── config.py                # 配置管理
│   └── run.py                   # Gateway 主循环
└── agent/
    ├── auxiliary_client.py      # 辅助客户端
    └── ...
```

**扩展方式**：
- 直接修改源码文件
- 通过正则表达式匹配标记字符串
- 维护成本高，升级易失效

#### 2.0 架构（新）

```
Hermes Agent 2.0
├── plugins/
│   ├── platforms/
│   │   ├── feishu/
│   │   │   ├── adapter.py       # 飞书平台实现（plugin 方式）
│   │   │   └── ...
│   │   ├── discord/
│   │   │   ├── adapter.py       # Discord 平台实现
│   │   │   └── ...
│   │   └── slack/
│   │       ├── adapter.py       # Slack 平台实现
│   │       └── ...
│   └── [other plugins]          # 其他 plugin
├── gateway/
│   ├── run.py                   # Gateway 主循环
│   └── config.py                # 配置管理
└── agent/
    ├── auxiliary_client.py      # 辅助客户端
    └── ...
```

**扩展方式**：
- Plugin Hook 机制
- 零侵入扩展
- 升级安全

---

## Plugin Hook 机制分析

⚠️ [行为观察，意图待确认]

### Hook 类型

Hermes Agent 2.0 支持以下 Hook：

| Hook 名称 | 触发时机 | 用途 |
|-----------|---------|------|
| `pre_gateway_dispatch` | Gateway 处理消息前 | 拦截和修改消息 |
| `on_session_start` | 会话开始时 | 初始化会话 |
| `on_session_end` | 会话结束时 | 清理资源 |
| `on_message_sent` | 消息发送后 | 后处理 |

### pre_gateway_dispatch Hook 分析

**调用点**：`gateway/run.py:8596`

```python
# gateway/run.py:8596
async def _dispatch_inbound_event(self, event: MessageEvent):
    """处理入站消息"""
    
    # 调用 pre_gateway_dispatch hook
    for plugin in self.plugins:
        if hasattr(plugin, 'pre_gateway_dispatch'):
            result = plugin.pre_gateway_dispatch(event, self)
            if result and result.get('action') == 'skip':
                logger.info(f"[{plugin.name}] Skipped message")
                return
            elif result and result.get('action') == 'rewrite':
                event = result.get('event', event)
    
    # 继续正常处理
    await self._process_event(event)
```

**关键特性**：
1. Hook 按 plugin 加载顺序执行
2. Hook 可以修改 `event` 对象（MessageEvent 是可变的 dataclass）
3. Hook 可以返回 `None`（继续处理）或 `{'action': 'skip'}`（跳过处理）
4. Hook 可以返回 `{'action': 'rewrite', 'event': new_event}`（重写消息）

**MessageEvent 结构**：

```python
# gateway/platforms/base.py:1756
@dataclass
class MessageEvent:
    """消息事件"""
    source: SessionSource
    content: str
    attachments: List[Attachment] = field(default_factory=list)
    auto_skill: Optional[List[str]] = None  # ← 我们要设置的字段
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # MessageEvent 是可变的，可以直接修改
```

---

## resolve_channel_skills 函数分析

⚠️ [行为观察，意图待确认]

### 函数定义

**位置**：`gateway/platforms/base.py:2182`

```python
def resolve_channel_skills(config_extra: Dict, channel_id: str, parent_id: Optional[str] = None) -> Optional[List[str]]:
    """解析 channel skill bindings
    
    Args:
        config_extra: 平台配置中的 extra 字段
        channel_id: chat_id 或 thread_id
        parent_id: thread 的 parent chat_id（用于继承）
    
    Returns:
        skills 列表，如果没有匹配则返回 None
    """
    if not config_extra:
        return None
    
    bindings = config_extra.get('channel_skill_bindings', [])
    if not bindings:
        return None
    
    # 优先级 1: 精确匹配 channel_id
    for binding in bindings:
        if binding.get('id') == channel_id:
            skills = binding.get('skills') or binding.get('skill')
            if isinstance(skills, str):
                skills = [skills]
            return skills
    
    # 优先级 2: 回退到 parent_id（thread 继承）
    if parent_id:
        for binding in bindings:
            if binding.get('id') == parent_id:
                skills = binding.get('skills') or binding.get('skill')
                if isinstance(skills, str):
                    skills = [skills]
                return skills
    
    return None
```

### 工作原理

1. **输入**：
   - `config_extra`: 平台配置中的 `extra` 字段
   - `channel_id`: 当前消息的 chat_id 或 thread_id
   - `parent_id`: 如果是 thread 消息，parent chat_id

2. **匹配逻辑**：
   - 优先级 1: 精确匹配 `channel_id`
   - 优先级 2: 回退到 `parent_id`（thread 继承）

3. **输出**：
   - 返回 skills 列表（如 `["research", "a-stock-message-analyzer"]`）
   - 如果没有匹配，返回 `None`

### 飞书场景

对于飞书消息：
- **普通群聊**：`channel_id=chat_id`, `parent_id=None`
- **话题群聊（非 thread）**：`channel_id=chat_id`, `parent_id=None`
- **话题群聊（在 thread 中）**：`channel_id=thread_id`, `parent_id=chat_id`

---

## auto_skill 消费点分析

⚠️ [行为观察，意图待确认]

### 消费点

**位置**：`gateway/run.py:10514`

```python
# gateway/run.py:10514
async def _create_new_session(self, event: MessageEvent):
    """创建新会话"""
    
    # 检查 auto_skill
    if event.auto_skill:
        logger.info(f"Loading auto_skill: {event.auto_skill}")
        
        # 加载 skill
        from agent.skill_commands import _load_skill_payload
        
        skills = []
        for skill_name in event.auto_skill:
            skill_payload = _load_skill_payload(skill_name)
            if skill_payload:
                skills.append(skill_payload)
            else:
                logger.warning(f"Skill '{skill_name}' not found")
        
        # 将 skill 注入会话
        if skills:
            session.initial_skills = skills
```

### 工作原理

1. **检查**：`event.auto_skill` 是否设置
2. **加载**：调用 `_load_skill_payload()` 加载 skill
3. **注入**：将 skill 注入到新会话的 `initial_skills`

### 关键特性

1. **仅对新会话生效**：`auto_skill` 只在创建新会话时检查
2. **自动加载**：Gateway 会自动加载 skill，无需用户干预
3. **错误处理**：如果 skill 不存在，记录 warning 但不会崩溃

---

## 参考实现分析

⚠️ [行为观察，意图待确认]

### a-stock-message-analyzer Plugin

**位置**：`skills/a-stock-message-analyzer/plugin/pipeline-routing/`

**结构**：
```
pipeline-routing/
├── plugin.yaml
├── __init__.py
└── handler.py
```

**plugin.yaml**：
```yaml
name: pipeline-routing
version: "1.0.0"
description: "Pipeline routing for a-stock-message-analyzer"
provides_hooks:
  - pre_gateway_dispatch
```

**__init__.py**：
```python
"""Pipeline routing plugin"""

def register(ctx):
    """注册 pre_gateway_dispatch hook"""
    from .handler import on_pre_gateway_dispatch
    ctx.register_hook("pre_gateway_dispatch", on_pre_gateway_dispatch)
```

**handler.py**：
```python
"""Pipeline routing handler"""

import logging

logger = logging.getLogger("pipeline-routing")


def on_pre_gateway_dispatch(event, gateway, **kwargs):
    """拦截消息，判断是否需要路由到 pipeline"""
    
    # 仅处理飞书平台
    if event.source.platform.value != "feishu":
        return None
    
    # 检查是否是 pipeline 群组
    chat_id = event.source.chat_id
    
    # 获取配置
    try:
        from gateway.config import Platform
        feishu_adapter = gateway.adapters.get(Platform.FEISHU)
    except Exception as e:
        logger.warning(f"获取飞书 adapter 失败: {e}")
        return None
    
    if not feishu_adapter:
        return None
    
    # 检查是否是 pipeline 群组
    pipeline_groups = feishu_adapter.config.extra.get('pipeline_groups', [])
    if chat_id in pipeline_groups:
        logger.info(f"[pipeline-routing] Routing to pipeline: {chat_id}")
        # 不返回 skip，让 Gateway 继续处理
        # Pipeline 会在后续步骤中接管
    
    return None  # 继续正常处理
```

### 关键学习点

1. **Plugin 结构**：
   - `plugin.yaml`: 声明 plugin 元数据和提供的 hooks
   - `__init__.py`: `register(ctx)` 函数注册 hooks
   - `handler.py`: Hook 实现

2. **Hook 签名**：
   ```python
   def on_pre_gateway_dispatch(event, gateway, **kwargs):
       # event: MessageEvent 对象
       # gateway: Gateway 实例
       # **kwargs: 接受未来 Hermes 版本新增的参数
   ```

3. **返回值**：
   - `None`: 继续正常处理
   - `{'action': 'skip'}`: 跳过处理
   - `{'action': 'rewrite', 'event': new_event}`: 重写消息

4. **访问配置**：
   ```python
   from gateway.config import Platform
   adapter = gateway.adapters.get(Platform.FEISHU)
   config_extra = adapter.config.extra
   ```

5. **修改 event**：
   ```python
   event.auto_skill = skills  # 直接修改（MessageEvent 是可变的）
   ```

---

## Plugin 架构设计

⚠️ [行为观察，意图待确认]

### 目标架构

```
hermes-extensions/
├── plugins/
│   └── feishu-skill-binding/
│       ├── plugin.yaml          # Plugin 元数据
│       ├── __init__.py          # register(ctx) 入口
│       └── handler.py           # pre_gateway_dispatch hook 实现
├── install.sh                   # 扩展：同时 symlink plugins
└── ...
```

### 数据流

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

### 核心代码

#### plugin.yaml

```yaml
name: feishu-skill-binding
version: "1.0.0"
description: "飞书 channel skill binding — 根据群聊 ID 自动加载 skill"
provides_hooks:
  - pre_gateway_dispatch
```

#### __init__.py

```python
"""飞书 skill binding plugin"""

def register(ctx):
    """注册 pre_gateway_dispatch hook"""
    from .handler import on_pre_gateway_dispatch
    ctx.register_hook("pre_gateway_dispatch", on_pre_gateway_dispatch)
```

#### handler.py

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

---

## install.sh 扩展设计

⚠️ [行为观察，意图待确认]

### 目标

扩展 `install.sh` 支持 plugin symlink。

### 设计

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

---

## 架构决策

⚠️ [行为观察，意图待确认]

### 决策 1: Plugin Hook vs 文件补丁

**选择**：Plugin Hook

**理由**：
1. ✅ 零侵入：不修改 hermes-agent 源码
2. ✅ 升级安全：plugin 机制是官方推荐的扩展方式
3. ✅ 可复用：同样的模式可以用于其他平台的 skill binding
4. ✅ 易管理：通过 hermes-extensions 统一管理

**风险**：
- ⚠️ Hermes 升级可能改变 hook 机制
- ⚠️ `resolve_channel_skills` 函数签名可能变化

**缓解措施**：
- 监控 Hermes release notes
- 使用 try-except 包裹，降级处理

### 决策 2: Plugin 位置

**选择**：`hermes-extensions/plugins/feishu-skill-binding/`

**理由**：
1. ✅ 统一管理：与现有补丁在同一 repo
2. ✅ 版本控制：通过 git 管理
3. ✅ 易于部署：通过 install.sh 自动 symlink

### 决策 3: Hook 返回值

**选择**：返回 `None`

**理由**：
1. ✅ 不拦截消息：让 Gateway 继续正常处理
2. ✅ 仅修改 event：设置 `auto_skill` 字段
3. ✅ 符合规范：遵循 Hermes plugin 最佳实践

---

## 下一步

**Phase 2 完成确认**：

- ✅ 分析 Hermes Agent plugin 机制
- ✅ 分析 pre_gateway_dispatch hook 调用点
- ✅ 分析 resolve_channel_skills 函数实现
- ✅ 设计 plugin 架构
- ✅ 设计数据流
- ✅ 设计 install.sh 扩展

**进入 Phase 3: 实施**：

1. 创建 plugin 目录结构
2. 实现 plugin 代码
3. 扩展 install.sh
4. 实现测试用例
5. 运行测试验证

**用户确认点 6**：

```
Phase 2（架构分析）已完成：

架构分析：
- Hermes Agent 2.0 使用 plugin 机制
- pre_gateway_dispatch hook 可以修改 event 对象
- resolve_channel_skills 函数支持 chat_id 和 thread_id
- auto_skill 在新会话创建时自动加载

架构设计：
- Plugin 结构：plugin.yaml + __init__.py + handler.py
- 数据流：拦截 → 解析 → 设置 auto_skill → 继续处理
- install.sh 扩展：支持 plugin symlink

架构决策：
- 选择 Plugin Hook（零侵入）
- Plugin 位置：hermes-extensions/plugins/
- Hook 返回值：None（不拦截消息）

请确认：
1. 架构分析是否完整？
2. 架构设计是否合理？
3. 是否继续进入 Phase 3（实施）？

确认后继续 Phase 3。
```
