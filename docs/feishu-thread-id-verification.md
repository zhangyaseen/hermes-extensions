# 飞书 Thread ID 支持验证报告

## 验证结果：✅ 飞书支持 Thread ID

### 代码证据

#### 1. Thread ID 提取（adapter.py:3200）

```python
thread_id = getattr(message, "thread_id", None) or getattr(message, "root_id", None) or None
```

飞书 adapter 从消息对象中提取 `thread_id` 或 `root_id`，并传递给 `build_source()`。

#### 2. Session Source 构建（adapter.py:3230-3236）

```python
source = self.build_source(
    chat_id=chat_id,
    chat_name=chat_info.get("name") or chat_id or "Feishu Chat",
    chat_type=self._resolve_source_chat_type(chat_info=chat_info, event_chat_type=chat_type),
    user_id=sender_profile["user_id"],
    user_name=sender_profile["user_name"],
    thread_id=thread_id,  # ← thread_id 被传递
    user_id_alt=sender_profile["user_id_alt"],
    is_bot=is_bot,
)
```

#### 3. Channel Prompt 解析（adapter.py:3250）

```python
channel_prompt=self._resolve_channel_prompt(chat_id, thread_id or None),
```

飞书 adapter 使用 `thread_id` 解析 channel prompt，与 Discord/Slack 一致。

#### 4. Thread 消息发送（adapter.py:4556-4580）

```python
if not effective_reply_to and metadata and metadata.get("thread_id"):
    # For topic/thread messages that fell back from reply→create, use
    # thread_id as receive_id so the message lands in the topic instead of
    # the top-level chat.
    _thread_id = (metadata or {}).get("thread_id")
    if _thread_id:
        request = self._build_create_message_request(
            receive_id=_thread_id,
            ...
        )
        request = self._build_create_message_request("thread_id", body)
```

飞书 adapter 支持在 thread/topic 中发送消息。

### 测试证据

#### 测试用例：test_feishu.py:1997

```python
def test_send_uses_metadata_reply_target_for_threaded_feishu_topic(self):
    """测试在飞书 topic 中发送消息"""
    result = asyncio.run(
        adapter.send(
            chat_id="oc_chat",
            content="status update",
            metadata={
                "thread_id": "omt-thread",
                "reply_to_message_id": "om_trigger",
            },
        )
    )
    self.assertTrue(captured["request"].request_body.reply_in_thread)
```

测试名称明确表示：**"threaded feishu topic"**（飞书话题主题）。

### 飞书 Chat 类型映射（adapter.py:3959-3967）

```python
@staticmethod
def _map_chat_type(raw_chat_type: str) -> str:
    normalized = (raw_chat_type or "").strip().lower()
    if normalized == "p2p":
        return "dm"
    if "topic" in normalized or "thread" in normalized or "forum" in normalized:
        return "forum"  # ← 飞书的 topic/thread 映射为 "forum"
    if normalized == "group":
        return "group"
    return "dm"
```

飞书有三种主要 chat 类型：
- **p2p**: 私聊（DM）
- **group**: 普通群聊
- **topic/thread/forum**: 话题群聊（类似 Discord Forum）

### 结论

**飞书确实支持 thread_id**，但仅适用于**话题群聊（topic/thread/forum）**类型，不适用于普通群聊。

| Chat 类型 | thread_id 支持 | 说明 |
|-----------|---------------|------|
| 私聊 (p2p) | ❌ 无 | 一对一聊天 |
| 普通群聊 (group) | ❌ 无 | 普通群组，无 thread 概念 |
| 话题群聊 (topic/thread/forum) | ✅ 有 | 类似 Discord Forum，支持 thread |

## 对 Skill Binding 的影响

### 配置示例更新

```yaml
platforms:
  feishu:
    extra:
      channel_skill_bindings:
        # 普通群聊：基于 chat_id 绑定
        - id: "oc_regular_group"
          skills: ["research"]
        
        # 话题群聊：可以基于 chat_id 或 thread_id 绑定
        - id: "oc_forum_chat"
          skills: ["a-stock-message-analyzer"]
        
        # 特定 thread：基于 thread_id 绑定（可选）
        - id: "omt-specific-thread"
          skill: "creative"
```

### 工作原理

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
   - 优先匹配 `thread_id`，如果没有则匹配 `chat_id`

### resolve_channel_skills 行为

```python
# gateway/platforms/base.py:2182
def resolve_channel_skills(config_extra, channel_id, parent_id=None):
    """
    解析 channel skill bindings
    
    Args:
        channel_id: chat_id 或 thread_id
        parent_id: thread 的 parent chat_id（用于继承）
    
    优先级：
    1. 精确匹配 channel_id（thread_id 或 chat_id）
    2. 回退到 parent_id（thread 继承 parent chat 的 bindings）
    """
```

对于飞书：
- 如果消息在 thread 中：`channel_id=thread_id`, `parent_id=chat_id`
- 如果消息不在 thread 中：`channel_id=chat_id`, `parent_id=None`

### 文档更新建议

#### 需求文档更新

```markdown
## 飞书 Thread 支持

飞书支持两种群聊类型：

1. **普通群聊（group）**：无 thread 概念，所有消息在同一个聊天流中
2. **话题群聊（topic/thread/forum）**：类似 Discord Forum，支持创建独立的 thread

对于 skill binding：
- 普通群聊：只能基于 `chat_id` 绑定
- 话题群聊：可以基于 `chat_id` 或 `thread_id` 绑定
  - 在 thread 中发送的消息会继承 parent chat 的 skill binding
  - 也可以为特定 thread 单独配置 skill binding
```

#### 配置示例更新

```yaml
platforms:
  feishu:
    extra:
      channel_skill_bindings:
        # 场景 1：普通群聊
        - id: "oc_regular_group"
          skills: ["research"]
        
        # 场景 2：话题群聊（所有 thread 共享）
        - id: "oc_forum_chat"
          skills: ["a-stock-message-analyzer"]
        
        # 场景 3：特定 thread（优先级高于 parent chat）
        - id: "omt_specific_thread"
          skill: "creative"
```

## 修订后的 Review 结论

### 原始问题

> **问题**：文档假设飞书支持 `thread_id`，但未验证飞书是否有 thread 概念。

### 验证结果

✅ **飞书确实支持 thread_id**，但仅适用于话题群聊（topic/thread/forum）类型。

### 需要更新的文档

1. ✅ **需求文档**：添加飞书 thread 支持说明
2. ✅ **实施计划**：更新配置示例，包含 thread_id 场景
3. ✅ **测试用例**：添加 thread_id 相关的测试场景

### 新增测试用例

```markdown
### Thread 相关测试

- [ ] 普通群聊消息，thread_id=None，匹配 chat_id
- [ ] 话题群聊消息（非 thread），thread_id=None，匹配 chat_id
- [ ] 话题群聊 thread 消息，匹配 thread_id
- [ ] 话题群聊 thread 消息，无 thread_id 配置，继承 parent chat_id
- [ ] thread_id 和 chat_id 都有配置，优先使用 thread_id
```

## 参考资料

- 飞书 adapter 代码：`plugins/platforms/feishu/adapter.py:3200`
- Thread ID 提取：`adapter.py:3200`
- Chat 类型映射：`adapter.py:3959-3967`
- Thread 消息发送：`adapter.py:4556-4580`
- 测试用例：`tests/gateway/test_feishu.py:1997`
