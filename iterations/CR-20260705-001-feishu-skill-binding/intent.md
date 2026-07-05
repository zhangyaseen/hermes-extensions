# 用户意图确认（User Intent Confirmation）

**迭代ID**: CR-20260705-001-feishu-skill-binding  
**日期**: 2026-07-05  
**主导角色**: PM（用户意图确认）  
**分类**: brownfield-poor

---

## 用户变更意图

⚠️ [行为观察，意图待确认]

### 目标

为 Hermes Agent 的飞书平台添加 channel skill binding 功能，允许在 `config.yaml` 中配置特定群聊/会话自动加载指定的 skill。

### 核心需求

1. **功能需求**：
   - 飞书消息到达时，根据 `chat_id` / `thread_id` 自动加载绑定的 skill
   - 仅对新会话生效
   - 支持三种场景：普通群聊、话题群聊、特定 thread

2. **技术约束**：
   - ✅ 零侵入：不修改 hermes-agent 源码
   - ✅ 升级安全：Hermes 升级后功能保持有效
   - ✅ 可管理：通过 hermes-extensions repo 统一管理

3. **架构选择**：
   - ✅ 使用 Plugin Hook（`pre_gateway_dispatch`）而非文件补丁
   - ✅ 创建独立 plugin：`plugins/feishu-skill-binding/`
   - ✅ 扩展 install.sh 支持 plugin symlink

---

## 意图来源

### 对话历史

1. **初始需求**：
   - "查看一下 飞书是否支持绑定 skill"
   - "因为需要考虑一个问题 Hermes agent 每两周会做一个升级 我一般都会执行升级，而这个功能可能官方并不一定支持 如果我希望零侵入地完成这个修改 是否可行"

2. **技术验证**：
   - "参考一下 A stock message analazer 这个 skill 的实现方式 能否做参考"
   - "需要验证飞书的 thread_id 支持情况"

3. **方案选择**：
   - 用户选择 brownfield onboarding 流程
   - 用户选择继续 Phase 1（行为观察）

### 文档证据

1. **需求文档**：`docs/feishu-skill-binding-requirements.md`
   - 明确描述了功能需求
   - 明确提出了技术约束（零侵入、升级安全）
   - 明确选择了 Plugin Hook 方案

2. **实施计划**：`docs/feishu-skill-binding-plan.md`
   - 详细的 5 步实施计划
   - 完整的代码示例
   - 测试用例清单

3. **验证报告**：`docs/feishu-thread-id-verification.md`
   - 验证了飞书支持 thread_id
   - 提供了代码证据

---

## 意图分析

### 用户真实意图

⚠️ [行为观察，意图待确认]

1. **功能意图**：
   - 用户希望飞书平台能够像 Discord/Slack 一样支持 channel skill binding
   - 用户需要在特定群聊中自动加载特定 skill（如股票分析、研究等）
   - 用户需要支持飞书的 thread 功能（话题群聊）

2. **技术意图**：
   - 用户希望避免文件补丁方式（已过时、维护成本高）
   - 用户希望使用 Plugin Hook 方式（符合 Hermes 架构方向）
   - 用户希望通过 hermes-extensions 统一管理扩展

3. **业务意图**：
   - 用户定期升级 Hermes Agent（每两周）
   - 用户需要功能在升级后保持有效
   - 用户需要零侵入的扩展方式

### 意图与现有行为的关系

⚠️ [行为观察，意图待确认]

| 现有行为 | 用户意图 | 关系 |
|---------|---------|------|
| 文件补丁管理 | Plugin Hook 扩展 | 🔄 演进（从旧方式到新方式） |
| 手动应用补丁 | 自动触发补丁 | ➕ 增强（保持现有功能） |
| 无测试覆盖 | 建立测试基线 | ➕ 增强（提高质量） |
| 无 plugin 管理 | 添加 plugin 管理 | ✨ 新增功能 |

---

## 风险评估

⚠️ [行为观察，意图待确认]

### 技术风险

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| Hermes 升级改变 hook 机制 | 中 | 高 | 监控 release notes，快速适配 |
| `resolve_channel_skills` 函数签名变化 | 低 | 高 | 使用 try-except 包裹，降级处理 |
| 多个 plugin 同时修改 event | 低 | 中 | 遵循 plugin 规范，不返回 skip/rewrite |
| Plugin 加载顺序冲突 | 中 | 中 | 文档说明执行顺序 |

### 业务风险

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| 配置的 skill 不存在 | 中 | 低 | 添加 skill 存在性检查 |
| 配置格式错误 | 中 | 中 | 添加配置验证 |
| 用户不理解 thread 概念 | 中 | 低 | 提供详细文档和示例 |

---

## 变更范围

⚠️ [行为观察，意图待确认]

### 新增文件

```
plugins/feishu-skill-binding/
├── __init__.py          # register(ctx) 入口
├── handler.py           # pre_gateway_dispatch hook 实现
└── plugin.yaml          # plugin 元数据
```

### 修改文件

```
install.sh               # 添加 plugin symlink 逻辑
README.md                # 添加 plugin 管理说明
```

### 不受影响的部分

```
patches/                 # 现有补丁保持不变
hooks/                   # 现有 hook 保持不变
```

---

## 成功标准

⚠️ [行为观察，意图待确认]

### 功能标准

1. ✅ 飞书群聊消息能自动加载绑定的 skill
2. ✅ 配置变更后立即生效（无需重启）
3. ✅ 支持普通群聊、话题群聊、特定 thread 三种场景
4. ✅ 仅对新会话生效

### 技术标准

1. ✅ 不修改 hermes-agent 源码
2. ✅ Hermes 升级后功能保持有效
3. ✅ 通过 hermes-extensions 统一管理
4. ✅ 日志清晰，便于故障排查

### 质量标准

1. ✅ 测试覆盖率 > 80%
2. ✅ 所有高优先级测试用例通过
3. ✅ 无严重 bug
4. ✅ 文档完整

---

## 实施优先级

⚠️ [行为观察，意图待确认]

### Phase 1: 核心功能（高优先级）

1. 创建 plugin 目录结构
2. 实现 handler.py（pre_gateway_dispatch hook）
3. 创建 plugin.yaml 和 __init__.py
4. 扩展 install.sh 支持 plugin symlink

### Phase 2: 测试验证（高优先级）

5. 实现高优先级测试用例（12 个）
6. 运行完整测试
7. 修复发现的 bug

### Phase 3: 文档更新（中优先级）

8. 更新 README.md
9. 添加配置示例
10. 添加故障排查指南

### Phase 4: 优化改进（低优先级）

11. 添加 skill 存在性检查
12. 添加配置验证
13. 性能优化（缓存解析结果）

---

## 下一步

⚠️ [行为观察，意图待确认]

### Phase 1 完成确认

棕地项目入职流程 Phase 1 已完成：

- ✅ Step 1: 行为观察（understand.md）
- ✅ Step 2: FR 推断（base/requirements.md）
- ✅ Step 3: 测试基线生成（tests/baseline-checklist.md）
- ✅ Step 4: 用户意图确认（intent.md）

### 进入 Phase 2: 架构分析

**目标**：分析现有架构，设计 plugin 架构

**产出**：
- `architecture.md`：现有架构分析
- `design.md`：plugin 架构设计

**步骤**：
1. 分析 Hermes Agent 的 plugin 机制
2. 分析 `pre_gateway_dispatch` hook 的调用点
3. 分析 `resolve_channel_skills` 函数的实现
4. 设计 plugin 架构
5. 设计数据流

### 用户确认点 5

```
Phase 1（棕地项目入职）已完成：

产出文档：
- understand.md: 行为观察
- base/requirements.md: 功能需求推断
- tests/baseline-checklist.md: 测试基线清单
- intent.md: 用户意图确认

关键发现：
- 3 个业务模块（补丁管理、安装管理、自动化触发）
- 9 个活跃功能需求
- 1 个计划中的功能需求（飞书 skill binding）
- 22 个测试用例待实现
- 0% 测试覆盖率

用户意图：
- 实现飞书 channel skill binding plugin
- 使用 Plugin Hook 方式（零侵入）
- 通过 hermes-extensions 统一管理

请确认：
1. Phase 1 产出是否完整？
2. 用户意图理解是否正确？
3. 是否继续进入 Phase 2（架构分析）？

确认后继续 Phase 2。
```
