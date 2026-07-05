"""飞书 skill binding plugin"""

import logging

logger = logging.getLogger(__name__)


def register(ctx):
    """注册 pre_gateway_dispatch hook"""
    from .handler import on_pre_gateway_dispatch
    ctx.register_hook("pre_gateway_dispatch", on_pre_gateway_dispatch)
    logger.info("[feishu-skill-binding] ✅ Plugin 已加载并注册 pre_gateway_dispatch hook")
