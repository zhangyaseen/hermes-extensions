# Understand 变换产出：行为观察

**迭代ID**: CR-20260705-001-feishu-skill-binding  
**日期**: 2026-07-05  
**主导角色**: PM（行为观察）  
**分类**: brownfield-poor

---

## 1. 模块识别

⚠️ [行为观察，意图待确认]

### 模块 1：补丁管理（patches/）

**源文件**：
- `patches/apply-custom-patches.py` (128 行)
- `patches/patch-feishu.py` (247 行)
- `patches/hermes-custom-patches.patch` (未观察，legacy 文件)

**依赖**：
- Python 标准库：`os`, `re`, `sys`, `pathlib.Path`
- 无外部依赖

**公开接口**：
```python
# apply-custom-patches.py
def log(msg) -> None
def patch_auxiliary_client() -> bool
def patch_config() -> bool  # NOTE: 已禁用
def patch_feishu() -> bool  # NOTE: 已禁用，由 patch-feishu.py 处理
def main() -> int

# patch-feishu.py
def log(msg) -> None
def patch_feishu() -> bool
```

**行为观察**：

1. **apply-custom-patches.py** ⚠️ [行为观察，意图待确认]
   - **行为**：通过正则表达式匹配标记字符串，修改 hermes-agent 源码文件
   - **目标文件**：
     - `~/.hermes/hermes-agent/agent/auxiliary_client.py` — 注册 qwen3.7-plus 到视觉模型
     - `~/.hermes/hermes-agent/gateway/config.py` — 添加 FEISHU_ALLOW_ALL_GROUP_MESSAGES 支持（**已禁用**）
     - `~/.hermes/hermes-agent/gateway/platforms/feishu.py` — 添加 pipeline routing（**已禁用**）
   - **幂等性**：检查目标文件是否已包含补丁内容，避免重复应用
   - **日志**：写入 `/tmp/hermes-custom-patch.log`
   - **返回值**：0 = 全部成功，1 = 部分失败

2. **patch-feishu.py** ⚠️ [行为观察，意图待确认]
   - **行为**：为飞书 adapter 添加 pipeline routing 功能
   - **目标文件**：
     - 旧路径：`~/.hermes/hermes-agent/gateway/platforms/feishu.py`
     - 新路径：`~/.hermes/hermes-agent/plugins/platforms/feishu/adapter.py`（检测到后跳过）
   - **补丁内容**：
     1. 添加 `import sys`
     2. 为 `FeishuGroupRule` 添加 `pipeline: bool = False` 字段
     3. 在 `_load_settings` 中解析 `pipeline` 配置
     4. 在 `_dispatch_inbound_event` 中添加 pipeline 路由逻辑
     5. 添加 `_should_route_to_pipeline` 和 `_route_to_pipeline` 方法
   - **幂等性**：检查关键函数是否已存在
   - **兼容逻辑**：检测到新 plugin 架构时跳过补丁（由 pipeline-routing plugin 接管）
   - **日志**：写入 `/tmp/hermes-custom-patch.log`
   - **返回值**：0 = 成功，1 = 失败

### 模块 2：安装管理（install.sh）

**源文件**：
- `install.sh` (112 行)

**依赖**：
- Shell 标准工具：`bash`, `ln`, `cp`, `chmod`, `mkdir`, `readlink`
- 无外部依赖

**公开接口**：
```bash
./install.sh              # 安装
./install.sh --uninstall  # 卸载
./install.sh --help       # 帮助
```

**行为观察**：

1. **install()** ⚠️ [行为观察，意图待确认]
   - **行为**：
     1. 创建 `~/.hermes/scripts/` 目录
     2. 为 `patches/` 下的 3 个文件创建 symlink 到 `~/.hermes/scripts/`
     3. 复制 `hooks/post-merge` 到 `~/.hermes/hermes-agent/.git/hooks/post-merge`
   - **幂等性**：检查 symlink 是否已存在且指向正确
   - **备份**：如果目标文件已存在且非 symlink，重命名为 `.bak`
   - **错误处理**：源文件不存在时退出（`exit 1`）

2. **uninstall()** ⚠️ [行为观察，意图待确认]
   - **行为**：
     1. 移除 `~/.hermes/scripts/` 下的 symlink
     2. 移除 `~/.hermes/hermes-agent/.git/hooks/post-merge`
   - **安全性**：只移除 symlink，不移除原始文件

### 模块 3：Git Hook（hooks/）

**源文件**：
- `hooks/post-merge` (46 行)

**依赖**：
- Shell 标准工具：`bash`, `date`, `python3`
- 依赖模块 1 的补丁脚本

**公开接口**：
```bash
# 由 git 自动触发（post-merge 事件）
```

**行为观察**：

1. **post-merge hook** ⚠️ [行为观察，意图待确认]
   - **行为**：
     1. 调用 `~/.hermes/scripts/apply-custom-patches.py`
     2. 调用 `~/.hermes/scripts/patch-feishu.py`
   - **触发时机**：`hermes update`（git pull）后自动触发
   - **日志**：写入 `/tmp/hermes-post-merge.log`
   - **错误处理**：失败时记录 WARNING，不中断

---

## 2. 技术栈识别

⚠️ [行为观察，意图待确认]

| 组件 | 技术 | 版本 |
|------|------|------|
| 补丁脚本 | Python | 3.x（使用 `pathlib`、`re`） |
| 安装脚本 | Bash | 标准 shell |
| Git Hook | Bash | 标准 shell |
| 目标系统 | Hermes Agent | >= 2026-07（plugin 架构） |
| 运行环境 | macOS | Homebrew Python (`/opt/homebrew/bin/python3`) |

---

## 3. 模块边界识别

⚠️ [行为观察，意图待确认]

### 业务模块

1. **补丁管理模块** ⚠️ [行为观察，意图待确认]
   - **职责**：维护 hermes-agent 源码的自定义补丁
   - **边界**：`patches/` 目录
   - **依赖**：Hermes Agent 源码结构

2. **安装管理模块** ⚠️ [行为观察，意图待确认]
   - **职责**：将补丁和 hook 部署到 hermes 环境
   - **边界**：`install.sh`
   - **依赖**：补丁管理模块、hooks 模块

3. **自动化触发模块** ⚠️ [行为观察，意图待确认]
   - **职责**：在 hermes 升级后自动应用补丁
   - **边界**：`hooks/post-merge`
   - **依赖**：补丁管理模块

### 支撑模块

- **日志模块** ⚠️ [行为观察，意图待确认]
  - **职责**：记录补丁应用过程
  - **实现**：`log()` 函数（在每个补丁脚本中重复定义）
  - **输出**：`/tmp/hermes-custom-patch.log`、`/tmp/hermes-post-merge.log`

---

## 4. 依赖图

⚠️ [行为观察，意图待确认]

```
install.sh
  ├→ patches/apply-custom-patches.py (symlink)
  ├→ patches/patch-feishu.py (symlink)
  └→ hooks/post-merge (copy)
       ├→ ~/.hermes/scripts/apply-custom-patches.py (调用)
       └→ ~/.hermes/scripts/patch-feishu.py (调用)

外部依赖：
  patches/*.py ─→ ~/.hermes/hermes-agent/ (修改目标)
  hooks/post-merge ─→ ~/.hermes/hermes-agent/.git/hooks/ (安装目标)
```

---

## 5. 已有文档（非代码行为）

⚠️ [未观察，来自 docs/ 目录]

检测到 `docs/` 目录中有大量需求文档，描述了一个**尚未实现**的功能：

- `feishu-skill-binding-requirements.md` — 飞书 skill binding 功能需求
- `feishu-skill-binding-plan.md` — 实施计划
- `feishu-thread-id-verification.md` — 技术验证报告
- `UPDATE_SUMMARY.md` — 更新总结
- `REVIEW_COMPLETE.md` — Review 完成报告

**关键信息** ⚠️ [未验证，来自文档]：

1. **计划中的功能**：飞书 channel skill binding
2. **实现方式**：Plugin Hook（`pre_gateway_dispatch`）
3. **目标文件**：
   - `plugins/feishu-skill-binding/` — 新建 plugin 目录
   - `install.sh` — 扩展支持 plugin symlink
4. **状态**：文档已完成，代码未实现

**注意**：这些文档描述的是**意图**（intent），不是**行为**（behavior）。代码中尚未实现这些功能。

---

## 6. 总结

### 已观察到的行为

| 模块 | 行为 | 状态 |
|------|------|------|
| patches/apply-custom-patches.py | 修改 auxiliary_client.py，注册 qwen3.7-plus 视觉模型 | ✅ 活跃 |
| patches/patch-feishu.py | 为飞书添加 pipeline routing（旧架构） | ⚠️ 已过时（新架构下跳过） |
| install.sh | 部署补丁和 git hook | ✅ 活跃 |
| hooks/post-merge | 自动应用补丁 | ✅ 活跃 |

### 未实现但已文档化的意图

| 功能 | 文档 | 状态 |
|------|------|------|
| 飞书 skill binding | docs/feishu-skill-binding-*.md | 📝 计划中，未实现 |
| Plugin 管理 | docs/UPDATE_SUMMARY.md | 📝 计划中，未实现 |

### 关键发现

1. **架构迁移** ⚠️ [行为观察，意图待确认]
   - 飞书从 `gateway/platforms/feishu.py` 迁移到 `plugins/platforms/feishu/adapter.py`
   - `patch-feishu.py` 在新架构下已变成 no-op
   - 未来方向是 Plugin Hook，而非文件补丁

2. **补丁模式** ⚠️ [行为观察，意图待确认]
   - 通过正则表达式匹配标记字符串
   - 依赖 Hermes Agent 源码结构不变
   - 上游重构可能导致补丁失效

3. **扩展需求** ⚠️ [未验证，来自文档]
   - 需要添加 plugin 管理能力
   - 需要实现飞书 skill binding 功能
   - 需要扩展 install.sh 支持 plugin symlink

---

## 下一步

**Step 2：FR 推断** — 从行为观察推断功能需求，生成 `base/requirements.md`

**用户确认点 2**：

```
已完成行为观察，识别到：
- 3 个业务模块（补丁管理、安装管理、自动化触发）
- 2 个支撑模块（日志）
- 8 个公开接口

请确认：
1. 模块边界识别是否正确？
2. 技术栈识别是否正确？
3. 是否有遗漏的模块或行为？

确认后继续 Step 2（FR 推断）。
```
