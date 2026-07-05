"""飞书 skill binding plugin"""

def register(ctx):
    """注册 pre_gateway_dispatch hook"""
    from .handler import on_pre_gateway_dispatch
    ctx.register_hook("pre_gateway_dispatch", on_pre_gateway_dispatch)
