# 功能需求推断（FR Inference）

**迭代ID**: CR-20260705-001-feishu-skill-binding  
**日期**: 2026-07-05  
**主导角色**: PM（功能需求推断）  
**分类**: brownfield-poor  
**来源**: 从行为观察推断

---

## 推断说明

⚠️ [行为观察，意图待确认]

以下功能需求是从 Step 1 的行为观察中推断得出的。所有推断项均标记为 `⚠️ [行为观察，意图待确认]`，需要用户确认其意图。

---

## 1. 补丁管理功能需求

### FR-1.1: 视觉模型注册补丁

⚠️ [行为观察，意图待确认]

**行为观察**：
- `apply-custom-patches.py` 修改 `auxiliary_client.py`，将 `qwen3.7-plus` 注册到视觉模型列表

**功能需求**：
- **Given**: Hermes Agent 的 `auxiliary_client.py` 文件存在
- **When**: 执行 `apply-custom-patches.py`
- **Then**: 将 `qwen3.7-plus` 添加到视觉模型支持列表
- **And**: 如果补丁已存在（幂等性检查），跳过修改
- **And**: 记录操作日志到 `/tmp/hermes-custom-patch.log`
- **And**: 返回 0 表示成功，1 表示失败

**验收标准**：
1. ✅ 补丁成功应用后，`auxiliary_client.py` 包含 `qwen3.7-plus`
2. ✅ 重复执行补丁不会重复修改（幂等性）
3. ✅ 日志记录完整
4. ✅ 返回值正确

---

### FR-1.2: 飞书 Pipeline Routing 补丁（已过时）

⚠️ [行为观察，意图待确认]

**行为观察**：
- `patch-feishu.py` 原本为旧架构飞书添加 pipeline routing
- 检测到新 plugin 架构时跳过补丁
- 日志显示 "SKIP: Feishu is now a plugin; pipeline-routing plugin handles routing"

**功能需求**：
- **Given**: 飞书 adapter 文件存在
- **When**: 执行 `patch-feishu.py`
- **Then**: 
  - 如果是旧架构（`gateway/platforms/feishu.py`）：应用 pipeline routing 补丁
  - 如果是新架构（`plugins/platforms/feishu/adapter.py`）：跳过补丁
- **And**: 记录操作日志到 `/tmp/hermes-custom-patch.log`
- **And**: 返回 0 表示成功，1 表示失败

**验收标准**：
1. ✅ 旧架构下补丁成功应用
2. ✅ 新架构下补丁正确跳过
3. ✅ 日志记录完整
4. ✅ 返回值正确

**状态**：⚠️ 已过时 — 新架构下此补丁不再需要

---

### FR-1.3: 补丁禁用机制

⚠️ [行为观察，意图待确认]

**行为观察**：
- `apply-custom-patches.py` 中的 `patch_config()` 和 `patch_feishu()` 已禁用
- 代码中有注释：`# NOTE: 已禁用`

**功能需求**：
- **Given**: 某些补丁功能不再需要
- **When**: 执行主补丁脚本
- **Then**: 禁用的补丁不被执行
- **And**: 保留代码以便未来参考

**验收标准**：
1. ✅ 禁用的补丁不被执行
2. ✅ 代码保留完整

---

## 2. 安装管理功能需求

### FR-2.1: 补丁部署

⚠️ [行为观察，意图待确认]

**行为观察**：
- `install.sh` 为 `patches/` 下的 3 个文件创建 symlink 到 `~/.hermes/scripts/`
- 检查 symlink 是否已存在且指向正确
- 如果目标文件已存在且非 symlink，重命名为 `.bak`

**功能需求**：
- **Given**: `patches/` 目录包含补丁文件
- **When**: 执行 `install.sh`（无参数）
- **Then**: 
  - 创建 `~/.hermes/scripts/` 目录（如果不存在）
  - 为以下文件创建 symlink：
    - `apply-custom-patches.py`
    - `patch-feishu.py`
    - `hermes-custom-patches.patch`
  - 如果 symlink 已存在且指向正确，跳过
  - 如果目标文件已存在且非 symlink，重命名为 `.bak`
- **And**: 输出安装日志

**验收标准**：
1. ✅ Symlink 正确创建
2. ✅ 幂等性：重复安装不会出错
3. ✅ 现有文件被备份
4. ✅ 源文件不存在时退出（exit 1）

---

### FR-2.2: Git Hook 部署

⚠️ [行为观察，意图待确认]

**行为观察**：
- `install.sh` 复制 `hooks/post-merge` 到 `~/.hermes/hermes-agent/.git/hooks/post-merge`

**功能需求**：
- **Given**: `hooks/post-merge` 文件存在
- **When**: 执行 `install.sh`（无参数）
- **Then**: 
  - 复制 `hooks/post-merge` 到 `~/.hermes/hermes-agent/.git/hooks/post-merge`
  - 设置可执行权限（chmod +x）
- **And**: 输出安装日志

**验收标准**：
1. ✅ Git hook 正确安装
2. ✅ 可执行权限设置正确

---

### FR-2.3: 卸载管理

⚠️ [行为观察，意图待确认]

**行为观察**：
- `install.sh --uninstall` 移除 symlink 和 git hook
- 只移除 symlink，不移除原始文件

**功能需求**：
- **Given**: 已安装补丁和 hook
- **When**: 执行 `install.sh --uninstall`
- **Then**: 
  - 移除 `~/.hermes/scripts/` 下的 symlink
  - 移除 `~/.hermes/hermes-agent/.git/hooks/post-merge`
  - 不移除原始文件
- **And**: 输出卸载日志

**验收标准**：
1. ✅ Symlink 正确移除
2. ✅ Git hook 正确移除
3. ✅ 原始文件保留

---

### FR-2.4: 帮助信息

⚠️ [行为观察，意图待确认]

**行为观察**：
- `install.sh --help` 显示帮助信息

**功能需求**：
- **Given**: 用户需要帮助
- **When**: 执行 `install.sh --help`
- **Then**: 显示使用说明、参数列表、示例

**验收标准**：
1. ✅ 帮助信息完整
2. ✅ 格式清晰

---

## 3. 自动化触发功能需求

### FR-3.1: Post-Merge Hook 自动触发

⚠️ [行为观察，意图待确认]

**行为观察**：
- `hooks/post-merge` 在 git pull 后自动触发
- 调用 `apply-custom-patches.py` 和 `patch-feishu.py`
- 失败时记录 WARNING，不中断

**功能需求**：
- **Given**: `hermes-agent` 执行 git pull
- **When**: post-merge hook 触发
- **Then**: 
  - 调用 `~/.hermes/scripts/apply-custom-patches.py`
  - 调用 `~/.hermes/scripts/patch-feishu.py`
- **And**: 记录操作日志到 `/tmp/hermes-post-merge.log`
- **And**: 失败时记录 WARNING，不中断 git 操作

**验收标准**：
1. ✅ Hook 在 git pull 后自动触发
2. ✅ 补丁脚本被正确调用
3. ✅ 日志记录完整
4. ✅ 失败不中断 git 操作

---

## 4. 支撑功能需求

### FR-4.1: 日志记录

⚠️ [行为观察，意图待确认]

**行为观察**：
- 每个补丁脚本都有独立的 `log()` 函数
- 日志写入 `/tmp/hermes-custom-patch.log` 和 `/tmp/hermes-post-merge.log`

**功能需求**：
- **Given**: 补丁脚本执行
- **When**: 执行关键操作
- **Then**: 
  - 记录操作时间戳
  - 记录操作内容
  - 记录成功/失败状态
- **And**: 日志格式一致

**验收标准**：
1. ✅ 日志格式统一
2. ✅ 时间戳准确
3. ✅ 操作内容清晰

---

## 5. 计划中的功能需求（来自文档）

⚠️ [未验证，来自文档]

以下功能需求来自 `docs/` 目录的文档，描述的是**意图**（intent），不是**行为**（behavior）。代码中尚未实现这些功能。

### FR-5.1: 飞书 Channel Skill Binding Plugin

⚠️ [未验证，来自文档]

**文档来源**：`docs/feishu-skill-binding-requirements.md`

**功能需求**：
- **Given**: 飞书消息到达
- **When**: 消息来自配置的群聊/会话
- **Then**: 自动加载绑定的 skill
- **And**: 仅对新会话生效

**配置示例**：
```yaml
platforms:
  feishu:
    extra:
      channel_skill_bindings:
        - id: "oc_regular_group"
          skills: ["research"]
        - id: "oc_forum_chat"
          skills: ["a-stock-message-analyzer"]
        - id: "omt_specific_thread"
          skill: "creative"
```

**技术需求**：
1. 零侵入：不修改 hermes-agent 源码
2. 升级安全：Hermes 升级后功能保持有效
3. 可管理：通过 hermes-extensions repo 统一管理

**实现方式**：
- 使用 Plugin Hook（`pre_gateway_dispatch`）
- 创建 `plugins/feishu-skill-binding/` plugin
- 扩展 `install.sh` 支持 plugin symlink

**状态**：📝 计划中，未实现

---

## 6. 总结

### 已观察到的功能需求

| ID | 功能 | 状态 | 优先级 |
|----|------|------|--------|
| FR-1.1 | 视觉模型注册补丁 | ✅ 活跃 | 高 |
| FR-1.2 | 飞书 Pipeline Routing 补丁 | ⚠️ 已过时 | 低 |
| FR-1.3 | 补丁禁用机制 | ✅ 活跃 | 中 |
| FR-2.1 | 补丁部署 | ✅ 活跃 | 高 |
| FR-2.2 | Git Hook 部署 | ✅ 活跃 | 高 |
| FR-2.3 | 卸载管理 | ✅ 活跃 | 中 |
| FR-2.4 | 帮助信息 | ✅ 活跃 | 低 |
| FR-3.1 | Post-Merge Hook 自动触发 | ✅ 活跃 | 高 |
| FR-4.1 | 日志记录 | ✅ 活跃 | 中 |

### 计划中的功能需求（未实现）

| ID | 功能 | 文档 | 状态 | 优先级 |
|----|------|------|------|--------|
| FR-5.1 | 飞书 Channel Skill Binding Plugin | docs/feishu-skill-binding-*.md | 📝 计划中 | 高 |

---

## 下一步

**Step 3：测试基线生成** — 生成测试清单，识别测试覆盖缺口

**用户确认点 3**：

```
已完成 FR 推断，识别到：

已观察到的功能需求：
- 9 个活跃功能需求（FR-1.1 ~ FR-4.1）
- 1 个已过时功能需求（FR-1.2）

计划中的功能需求：
- 1 个未实现功能需求（FR-5.1）

请确认：
1. 功能需求推断是否正确？
2. 优先级划分是否合理？
3. 是否有遗漏的功能需求？

确认后继续 Step 3（测试基线生成）。
```
