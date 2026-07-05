# hermes-extensions 更新总结

## 本次更新内容

### 1. 需求文档 ✅

**文件**: `docs/feishu-skill-binding-requirements.md`

包含：
- 功能需求和技术需求
- 方案对比（文件补丁 vs Plugin Hook）
- 推荐方案及理由
- 架构设计和核心代码
- 实施计划和风险缓解
- 成功标准和参考资料

### 2. 实施计划 ✅

**文件**: `docs/feishu-skill-binding-plan.md`

包含：
- 详细的实施步骤（Step 1-5）
- 完整的代码实现（plugin.yaml, __init__.py, handler.py）
- install.sh 扩展方案
- 配置示例和测试验证流程
- 时间估算（2.5 小时）

### 3. README 更新 ✅

**文件**: `README.md`

更新内容：
- 新增"扩展插件（plugins/）"章节
- 更新目录结构，包含 plugins/ 和 docs/
- 新增"插件开发指南"章节
- 新增"飞书 Skill Binding 插件"使用说明
- 区分文件补丁和扩展插件两种扩展方式

## 架构演进

```
hermes-extensions 1.0 (当前)
  └── patches/          # 文件补丁
  └── hooks/            # git hooks
  └── install.sh        # 补丁安装

hermes-extensions 2.0 (本次更新)
  ├── patches/          # 文件补丁（保留，用于无法用 plugin 实现的场景）
  ├── plugins/          # 扩展插件（新增，优先使用）
  ├── docs/             # 文档（新增）
  ├── hooks/            # git hooks
  └── install.sh        # 补丁 + 插件安装
```

## 下一步行动

### Phase 1: 实现 Plugin（优先级：高）

- [ ] 创建 `plugins/feishu-skill-binding/` 目录
- [ ] 实现 `plugin.yaml`
- [ ] 实现 `__init__.py`
- [ ] 实现 `handler.py`

### Phase 2: 扩展 install.sh（优先级：高）

- [ ] 添加 `PLUGIN_DIRS` 数组
- [ ] 添加 plugin symlink 逻辑到 `install()`
- [ ] 添加 plugin 清理逻辑到 `uninstall()`

### Phase 3: 测试验证（优先级：高）

- [ ] 运行 `./install.sh` 验证安装
- [ ] 检查 `~/.hermes/plugins/feishu-skill-binding/` symlink
- [ ] 重启 Hermes Gateway，检查 plugin 加载日志
- [ ] 配置 `channel_skill_bindings`，测试 skill 自动加载

### Phase 4: 文档完善（优先级：中）

- [ ] 添加故障排查指南
- [ ] 添加性能优化建议
- [ ] 更新 hermes-skills 主 repo 的文档

## 关键决策

### 为什么选择 Plugin Hook 而非文件补丁？

1. **Hermes 架构方向**：Hermes 正在从文件修改转向 plugin 架构
   - 飞书已从 `gateway/platforms/feishu.py` 迁移到 `plugins/platforms/feishu/adapter.py`
   - `patch-feishu.py` 在新架构下已变成 no-op

2. **维护成本**：文件补丁依赖标记字符串匹配，上游重构会导致补丁失效
   - Plugin Hook 使用官方 API，升级安全
   - 不需要维护复杂的正则表达式

3. **可扩展性**：Plugin 模式可以复用到其他平台
   - WeCom、QQ 等平台也可以用同样的模式添加 skill binding
   - 可以扩展更多功能（如 channel_prompt、auto_tool 等）

### 为什么在 hermes-extensions 中管理 Plugin？

1. **统一管理**：所有 Hermes 扩展集中在一个 repo
2. **版本控制**：通过 git submodule 管理，与 skills 一起版本化
3. **安装便利**：一次 `./install.sh` 同时安装补丁和插件
4. **渐进迁移**：保留 patches/ 用于无法用 plugin 实现的场景（如 auxiliary_client.py）

## 技术细节

### Plugin Hook 工作原理

```python
# 1. Gateway 启动时加载 plugin
~/.hermes/plugins/feishu-skill-binding/__init__.py
  → register(ctx)
  → ctx.register_hook("pre_gateway_dispatch", on_pre_gateway_dispatch)

# 2. 飞书消息到达时触发 hook
gateway/run.py:8596
  → invoke_hook("pre_gateway_dispatch", event=event, gateway=self, ...)
  → on_pre_gateway_dispatch(event, gateway, ...)

# 3. Plugin 修改 event 对象
handler.py:
  → skills = resolve_channel_skills(config.extra, chat_id, thread_id)
  → event.auto_skill = skills  # 直接修改（MessageEvent 是可变 dataclass）

# 4. Gateway 消费 auto_skill
gateway/run.py:10514
  → _auto = getattr(event, "auto_skill", None)
  → 加载 skill 并注入到 session
```

### 关键代码路径

| 文件 | 行号 | 作用 |
|------|------|------|
| `gateway/platforms/base.py` | 1756 | `MessageEvent.auto_skill` 定义 |
| `gateway/platforms/base.py` | 2182 | `resolve_channel_skills()` 函数 |
| `gateway/run.py` | 8596 | `pre_gateway_dispatch` hook 调用点 |
| `gateway/run.py` | 10514 | `auto_skill` 消费点 |

## 预期效果

### 用户体验

1. 在 `config.yaml` 中配置飞书群聊的 skill binding
2. 在该群聊中发送消息，skill 自动加载
3. 无需手动调用 `/skill` 命令
4. 新会话自动生效，已有会话不受影响

### 开发体验

1. 修改 plugin 源码后立即生效（通过 symlink）
2. 通过 git 管理版本，可回滚
3. 统一的安装/卸载流程
4. 清晰的日志输出，便于调试

## 风险与缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| Hermes 改变 hook 机制 | 低 | 高 | 监控 release notes，快速适配 |
| `resolve_channel_skills` 签名变化 | 中 | 中 | try-except 包裹，降级为无 skill binding |
| Plugin 加载失败 | 低 | 中 | 日志告警，不影响正常消息处理 |
| 多个 plugin 冲突 | 低 | 中 | 遵循 Hermes plugin 规范，不返回 skip/rewrite |

## 参考资料

- [需求文档](./docs/feishu-skill-binding-requirements.md)
- [实施计划](./docs/feishu-skill-binding-plan.md)
- [Discord channel_skill_bindings 实现](https://github.com/NousResearch/hermes-agent/blob/main/plugins/platforms/discord/adapter.py#L4550)
- [a-stock-message-analyzer plugin 示例](../skills/a-stock-message-analyzer/plugin/pipeline-routing/)
- [Hermes Plugin 文档](https://hermes-agent.nousresearch.com/docs/plugins)
