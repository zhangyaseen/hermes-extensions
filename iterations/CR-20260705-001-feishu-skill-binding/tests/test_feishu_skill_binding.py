"""
飞书 skill binding plugin 简化测试

测试覆盖：
- TC-5.1.1: Plugin 加载
- TC-5.1.2: Skill 注入 - 普通群聊
- TC-5.1.3: Skill 注入 - Thread 继承
- TC-5.1.4: Skill 注入 - Thread 独立配置
- TC-5.1.5: 未配置的群聊
"""

import pytest
from unittest.mock import Mock, MagicMock
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from pathlib import Path
import sys
import builtins


# Mock MessageEvent
@dataclass
class MockSessionSource:
    platform: Mock
    chat_id: str
    thread_id: Optional[str] = None


@dataclass
class MockMessageEvent:
    source: MockSessionSource
    content: str
    auto_skill: Optional[List[str]] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class TestFeishuSkillBinding:
    """飞书 skill binding plugin 测试"""

    @classmethod
    def setup_class(cls):
        """类级别设置"""
        # 添加 plugin 目录到 Python 路径
        plugin_dir = Path(__file__).parent.parent.parent.parent / "plugins" / "feishu-skill-binding"
        sys.path.insert(0, str(plugin_dir))
        cls.plugin_dir = plugin_dir

    @classmethod
    def teardown_class(cls):
        """类级别清理"""
        # 移除 plugin 目录
        if str(cls.plugin_dir) in sys.path:
            sys.path.remove(str(cls.plugin_dir))
        # 移除 handler 模块
        if 'handler' in sys.modules:
            del sys.modules['handler']

    def create_mock_gateway(self, config_extra=None):
        """创建 mock gateway"""
        gateway = Mock()

        # Mock飞书 adapter
        feishu_adapter = Mock()
        feishu_adapter.config = Mock()
        feishu_adapter.config.extra = config_extra or {}

        # Mock adapters dict
        gateway.adapters = Mock()
        gateway.adapters.get = Mock(return_value=feishu_adapter)

        return gateway

    def create_mock_event(self, platform="feishu", chat_id="oc_test", thread_id=None):
        """创建 mock event"""
        source = MockSessionSource(
            platform=Mock(value=platform),
            chat_id=chat_id,
            thread_id=thread_id
        )
        return MockMessageEvent(source=source, content="test message")

    # TC-5.1.1: Plugin 加载
    def test_plugin_load(self):
        """测试 plugin 成功加载"""
        # Given: plugin 目录存在
        assert self.plugin_dir.exists()
        assert (self.plugin_dir / "plugin.yaml").exists()
        assert (self.plugin_dir / "__init__.py").exists()
        assert (self.plugin_dir / "handler.py").exists()

        # When: 导入 plugin
        import __init__ as plugin

        # Then: register 函数存在
        assert hasattr(plugin, 'register')
        assert callable(plugin.register)

    # TC-5.1.2: Skill 注入 - 普通群聊
    def test_skill_injection_regular_group(self):
        """测试普通群聊消息的 skill 注入"""
        # Given: 配置了 chat_id binding
        config_extra = {
            'channel_skill_bindings': [
                {'id': 'oc_regular_group', 'skills': ['research', 'analysis']}
            ]
        }
        gateway = self.create_mock_gateway(config_extra)
        event = self.create_mock_event(chat_id='oc_regular_group')

        # Mock resolve_channel_skills
        mock_resolve = Mock(return_value=['research', 'analysis'])

        # Patch the import in handler
        import handler
        original_import = builtins.__import__

        def custom_import(name, *args, **kwargs):
            if name == 'gateway.platforms.base':
                mock_module = Mock()
                mock_module.resolve_channel_skills = mock_resolve
                return mock_module
            elif name == 'gateway.config':
                mock_module = Mock()
                mock_module.Platform = Mock()
                mock_module.Platform.FEISHU = 'feishu'
                return mock_module
            return original_import(name, *args, **kwargs)

        builtins.__import__ = custom_import
        try:
            # When: 消息到达
            result = handler.on_pre_gateway_dispatch(event, gateway)

            # Then: event.auto_skill 被设置
            assert result is None  # 继续正常处理
            assert event.auto_skill == ['research', 'analysis']
        finally:
            builtins.__import__ = original_import

    # TC-5.1.3: Skill 注入 - Thread 继承
    def test_skill_injection_thread_inherit(self):
        """测试 thread 消息继承 parent chat 的 skill"""
        # Given: 配置了 chat_id binding
        config_extra = {
            'channel_skill_bindings': [
                {'id': 'oc_forum_chat', 'skills': ['a-stock-message-analyzer']}
            ]
        }
        gateway = self.create_mock_gateway(config_extra)
        event = self.create_mock_event(
            chat_id='oc_forum_chat',
            thread_id='omt_thread_123'
        )

        # Mock resolve_channel_skills（模拟继承）
        mock_resolve = Mock(return_value=['a-stock-message-analyzer'])

        import handler
        original_import = builtins.__import__

        def custom_import(name, *args, **kwargs):
            if name == 'gateway.platforms.base':
                mock_module = Mock()
                mock_module.resolve_channel_skills = mock_resolve
                return mock_module
            elif name == 'gateway.config':
                mock_module = Mock()
                mock_module.Platform = Mock()
                mock_module.Platform.FEISHU = 'feishu'
                return mock_module
            return original_import(name, *args, **kwargs)

        builtins.__import__ = custom_import
        try:
            # When: thread 消息到达（无独立配置）
            result = handler.on_pre_gateway_dispatch(event, gateway)

            # Then: event.auto_skill 继承 parent chat 的配置
            assert result is None
            assert event.auto_skill == ['a-stock-message-analyzer']
        finally:
            builtins.__import__ = original_import

    # TC-5.1.4: Skill 注入 - Thread 独立配置
    def test_skill_injection_thread_specific(self):
        """测试 thread 独立配置优先"""
        # Given: 同时配置了 chat_id 和 thread_id binding
        config_extra = {
            'channel_skill_bindings': [
                {'id': 'oc_forum_chat', 'skills': ['research']},
                {'id': 'omt_specific_thread', 'skills': ['creative']}
            ]
        }
        gateway = self.create_mock_gateway(config_extra)
        event = self.create_mock_event(
            chat_id='oc_forum_chat',
            thread_id='omt_specific_thread'
        )

        # Mock resolve_channel_skills（模拟 thread 配置优先）
        mock_resolve = Mock(return_value=['creative'])

        import handler
        original_import = builtins.__import__

        def custom_import(name, *args, **kwargs):
            if name == 'gateway.platforms.base':
                mock_module = Mock()
                mock_module.resolve_channel_skills = mock_resolve
                return mock_module
            elif name == 'gateway.config':
                mock_module = Mock()
                mock_module.Platform = Mock()
                mock_module.Platform.FEISHU = 'feishu'
                return mock_module
            return original_import(name, *args, **kwargs)

        builtins.__import__ = custom_import
        try:
            # When: thread 消息到达
            result = handler.on_pre_gateway_dispatch(event, gateway)

            # Then: event.auto_skill 使用 thread_id 的配置
            assert result is None
            assert event.auto_skill == ['creative']
        finally:
            builtins.__import__ = original_import

    # TC-5.1.5: 未配置的群聊
    def test_no_skill_injection_unconfigured(self):
        """测试未配置的群聊不注入 skill"""
        # Given: 群聊未配置 binding
        config_extra = {
            'channel_skill_bindings': [
                {'id': 'oc_other_group', 'skills': ['research']}
            ]
        }
        gateway = self.create_mock_gateway(config_extra)
        event = self.create_mock_event(chat_id='oc_unconfigured_group')

        # Mock resolve_channel_skills（无匹配）
        mock_resolve = Mock(return_value=None)

        import handler
        original_import = builtins.__import__

        def custom_import(name, *args, **kwargs):
            if name == 'gateway.platforms.base':
                mock_module = Mock()
                mock_module.resolve_channel_skills = mock_resolve
                return mock_module
            elif name == 'gateway.config':
                mock_module = Mock()
                mock_module.Platform = Mock()
                mock_module.Platform.FEISHU = 'feishu'
                return mock_module
            return original_import(name, *args, **kwargs)

        builtins.__import__ = custom_import
        try:
            # When: 消息到达
            result = handler.on_pre_gateway_dispatch(event, gateway)

            # Then: event.auto_skill 不被设置
            assert result is None
            assert event.auto_skill is None
        finally:
            builtins.__import__ = original_import

    # 边界情况测试
    def test_non_feishu_platform(self):
        """测试非飞书平台不处理"""
        # Given: 非飞书平台消息
        gateway = self.create_mock_gateway()
        event = self.create_mock_event(platform='discord')

        import handler
        # When: 消息到达
        result = handler.on_pre_gateway_dispatch(event, gateway)

        # Then: 直接返回 None
        assert result is None
        assert event.auto_skill is None

    def test_feishu_adapter_not_found(self):
        """测试飞书 adapter 不存在"""
        # Given: 飞书 adapter 不存在
        gateway = Mock()
        gateway.adapters = Mock()
        gateway.adapters.get = Mock(return_value=None)

        event = self.create_mock_event()

        import handler
        # When: 消息到达
        result = handler.on_pre_gateway_dispatch(event, gateway)

        # Then: 返回 None，不设置 auto_skill
        assert result is None
        assert event.auto_skill is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
