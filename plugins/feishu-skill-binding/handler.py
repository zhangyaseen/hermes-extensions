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

logger = logging.getLogger(__name__)


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
        logger.debug(f"[feishu-skill-binding] 跳过非飞书平台: {event.source.platform.value}")
        return None

    chat_id = event.source.chat_id
    thread_id = event.source.thread_id
    logger.info(f"[feishu-skill-binding] 🔍 处理飞书消息 chat_id={chat_id} thread_id={thread_id}")

    # 获取飞书 adapter
    try:
        from gateway.config import Platform
        feishu_adapter = gateway.adapters.get(Platform.FEISHU)
    except Exception as e:
        logger.warning(f"[feishu-skill-binding] 获取飞书 adapter 失败: {e}")
        return None

    if not feishu_adapter:
        logger.warning("[feishu-skill-binding] 飞书 adapter 不存在")
        return None

    logger.info("[feishu-skill-binding] 🔧 开始解析 skill bindings")

    # 解析 skill bindings
    try:
        from gateway.platforms.base import resolve_channel_skills
        skills = resolve_channel_skills(
            feishu_adapter.config.extra,
            chat_id,
            thread_id
        )
        logger.info(f"[feishu-skill-binding] 📋 resolve_channel_skills 返回: {skills}")
    except Exception as e:
        logger.warning(f"[feishu-skill-binding] 解析 skill bindings 失败: {e}", exc_info=True)
        return None

    # 如果匹配，设置 auto_skill
    if skills:
        event.auto_skill = skills
        logger.info(
            f"[feishu-skill-binding] ✅ 注入 skills={skills} "
            f"chat_id={chat_id} thread_id={thread_id}"
        )
    else:
        logger.info(
            f"[feishu-skill-binding] ⚠️ 未找到匹配的 skill binding "
            f"chat_id={chat_id} thread_id={thread_id}"
        )

    return None  # 继续正常处理
