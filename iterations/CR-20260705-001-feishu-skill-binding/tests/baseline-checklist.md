# 测试基线清单（Test Baseline Checklist）

**迭代ID**: CR-20260705-001-feishu-skill-binding  
**日期**: 2026-07-05  
**主导角色**: Developer（测试基线生成）  
**分类**: brownfield-poor

---

## 测试覆盖现状

⚠️ [行为观察，意图待确认]

**当前状态**：
- ❌ 无任何测试文件
- ❌ 无测试目录
- ❌ 无测试框架配置
- ❌ 无 CI/CD 测试集成

**测试覆盖缺口**：
- 所有功能需求均无测试覆盖
- 需要建立完整的测试基线

---

## 测试清单

### 1. 补丁管理模块测试

#### 1.1 apply-custom-patches.py 测试

##### TC-1.1.1: 视觉模型注册补丁 - 正常路径

⚠️ [行为观察，意图待确认]

**测试目标**：验证补丁成功应用到 auxiliary_client.py

**测试用例**：
```python
def test_patch_auxiliary_client_success():
    """测试视觉模型注册补丁成功应用"""
    # Given: auxiliary_client.py 存在且未包含补丁
    # When: 执行 patch_auxiliary_client()
    # Then: 补丁成功应用
    # And: auxiliary_client.py 包含 qwen3.7-plus
    # And: 返回 True
```

**验收标准**：
- [ ] 补丁成功应用
- [ ] 文件包含 qwen3.7-plus
- [ ] 返回 True
- [ ] 日志记录完整

**优先级**：🔴 高

---

##### TC-1.1.2: 视觉模型注册补丁 - 幂等性

⚠️ [行为观察，意图待确认]

**测试目标**：验证补丁重复应用时的幂等性

**测试用例**：
```python
def test_patch_auxiliary_client_idempotent():
    """测试补丁重复应用时的幂等性"""
    # Given: auxiliary_client.py 已包含补丁
    # When: 再次执行 patch_auxiliary_client()
    # Then: 跳过修改
    # And: 返回 True
    # And: 文件内容未改变
```

**验收标准**：
- [ ] 补丁不重复应用
- [ ] 文件内容保持不变
- [ ] 返回 True
- [ ] 日志记录 "SKIP"

**优先级**：🔴 高

---

##### TC-1.1.3: 视觉模型注册补丁 - 目标文件不存在

⚠️ [行为观察，意图待确认]

**测试目标**：验证目标文件不存在时的错误处理

**测试用例**：
```python
def test_patch_auxiliary_client_file_not_found():
    """测试目标文件不存在时的错误处理"""
    # Given: auxiliary_client.py 不存在
    # When: 执行 patch_auxiliary_client()
    # Then: 返回 False
    # And: 记录错误日志
```

**验收标准**：
- [ ] 返回 False
- [ ] 记录错误日志
- [ ] 不抛出异常

**优先级**：🟡 中

---

##### TC-1.1.4: 视觉模型注册补丁 - 标记字符串不匹配

⚠️ [行为观察，意图待确认]

**测试目标**：验证标记字符串不匹配时的错误处理

**测试用例**：
```python
def test_patch_auxiliary_client_marker_not_found():
    """测试标记字符串不匹配时的错误处理"""
    # Given: auxiliary_client.py 存在但不包含标记字符串
    # When: 执行 patch_auxiliary_client()
    # Then: 返回 False
    # And: 记录错误日志
```

**验收标准**：
- [ ] 返回 False
- [ ] 记录错误日志 "Marker not found"

**优先级**：🟡 中

---

#### 1.2 patch-feishu.py 测试

##### TC-1.2.1: 旧架构补丁 - 正常路径

⚠️ [行为观察，意图待确认]

**测试目标**：验证旧架构下补丁成功应用

**测试用例**：
```python
def test_patch_feishu_legacy_success():
    """测试旧架构下补丁成功应用"""
    # Given: gateway/platforms/feishu.py 存在
    # When: 执行 patch_feishu()
    # Then: 5 个补丁步骤全部成功
    # And: 返回 True
```

**验收标准**：
- [ ] 5 个补丁步骤全部成功
- [ ] 返回 True
- [ ] 日志记录完整

**优先级**：🟡 中（旧架构已过时）

---

##### TC-1.2.2: 新架构跳过

⚠️ [行为观察，意图待确认]

**测试目标**：验证新架构下补丁正确跳过

**测试用例**：
```python
def test_patch_feishu_plugin_skip():
    """测试新架构下补丁正确跳过"""
    # Given: plugins/platforms/feishu/adapter.py 存在
    # When: 执行 patch_feishu()
    # Then: 跳过补丁
    # And: 返回 True
    # And: 日志记录 "SKIP: Feishu is now a plugin"
```

**验收标准**：
- [ ] 补丁被跳过
- [ ] 返回 True
- [ ] 日志记录 "SKIP"

**优先级**：🔴 高

---

#### 1.3 apply-custom-patches.py 主函数测试

##### TC-1.3.1: 主函数 - 全部成功

⚠️ [行为观察，意图待确认]

**测试目标**：验证所有补丁成功应用

**测试用例**：
```python
def test_main_all_success():
    """测试所有补丁成功应用"""
    # Given: 所有补丁条件满足
    # When: 执行 main()
    # Then: 返回 0
    # And: 所有补丁成功应用
```

**验收标准**：
- [ ] 返回 0
- [ ] 所有补丁成功应用

**优先级**：🔴 高

---

##### TC-1.3.2: 主函数 - 部分失败

⚠️ [行为观察，意图待确认]

**测试目标**：验证部分补丁失败时的返回值

**测试用例**：
```python
def test_main_partial_failure():
    """测试部分补丁失败时的返回值"""
    # Given: 某个补丁失败
    # When: 执行 main()
    # Then: 返回 1
    # And: 其他补丁继续执行
```

**验收标准**：
- [ ] 返回 1
- [ ] 其他补丁继续执行
- [ ] 失败补丁记录错误日志

**优先级**：🟡 中

---

### 2. 安装管理模块测试

#### 2.1 install.sh 测试

##### TC-2.1.1: 安装 - 正常路径

⚠️ [行为观察，意图待确认]

**测试目标**：验证安装成功

**测试用例**：
```bash
test_install_success() {
    # Given: 所有源文件存在
    # When: 执行 ./install.sh
    # Then: 创建 ~/.hermes/scripts/ 目录
    # And: 创建 3 个 symlink
    # And: 复制 git hook
    # And: 输出安装日志
}
```

**验收标准**：
- [ ] 目录创建成功
- [ ] Symlink 正确创建
- [ ] Git hook 正确安装
- [ ] 退出码为 0

**优先级**：🔴 高

---

##### TC-2.1.2: 安装 - 幂等性

⚠️ [行为观察，意图待确认]

**测试目标**：验证重复安装时的幂等性

**测试用例**：
```bash
test_install_idempotent() {
    # Given: 已安装完成
    # When: 再次执行 ./install.sh
    # Then: 跳过已存在的 symlink
    # And: 输出 "SKIP" 日志
    # And: 退出码为 0
}
```

**验收标准**：
- [ ] Symlink 不重复创建
- [ ] 输出 "SKIP" 日志
- [ ] 退出码为 0

**优先级**：🔴 高

---

##### TC-2.1.3: 安装 - 目标文件已存在

⚠️ [行为观察，意图待确认]

**测试目标**：验证目标文件已存在时的备份逻辑

**测试用例**：
```bash
test_install_backup_existing() {
    # Given: 目标文件已存在且非 symlink
    # When: 执行 ./install.sh
    # Then: 将目标文件重命名为 .bak
    # And: 创建新的 symlink
    # And: 输出 "BACKUP" 日志
}
```

**验收标准**：
- [ ] 原文件重命名为 .bak
- [ ] 创建新的 symlink
- [ ] 输出 "BACKUP" 日志

**优先级**：🟡 中

---

##### TC-2.1.4: 安装 - 源文件不存在

⚠️ [行为观察，意图待确认]

**测试目标**：验证源文件不存在时的错误处理

**测试用例**：
```bash
test_install_source_not_found() {
    # Given: 某个源文件不存在
    # When: 执行 ./install.sh
    # Then: 输出错误日志
    # And: 退出码为 1
}
```

**验收标准**：
- [ ] 输出错误日志
- [ ] 退出码为 1

**优先级**：🟡 中

---

##### TC-2.1.5: 卸载 - 正常路径

⚠️ [行为观察，意图待确认]

**测试目标**：验证卸载成功

**测试用例**：
```bash
test_uninstall_success() {
    # Given: 已安装完成
    # When: 执行 ./install.sh --uninstall
    # Then: 移除所有 symlink
    # And: 移除 git hook
    # And: 原始文件保留
    # And: 退出码为 0
}
```

**验收标准**：
- [ ] Symlink 正确移除
- [ ] Git hook 正确移除
- [ ] 原始文件保留
- [ ] 退出码为 0

**优先级**：🔴 高

---

##### TC-2.1.6: 卸载 - 部分文件不存在

⚠️ [行为观察，意图待确认]

**测试目标**：验证部分文件不存在时的错误处理

**测试用例**：
```bash
test_uninstall_partial_missing() {
    # Given: 某些 symlink 不存在
    # When: 执行 ./install.sh --uninstall
    # Then: 移除存在的 symlink
    # And: 跳过不存在的文件
    # And: 退出码为 0
}
```

**验收标准**：
- [ ] 存在的 symlink 被移除
- [ ] 不存在的文件被跳过
- [ ] 退出码为 0

**优先级**：🟡 中

---

##### TC-2.1.7: 帮助信息

⚠️ [行为观察，意图待确认]

**测试目标**：验证帮助信息显示

**测试用例**：
```bash
test_help() {
    # When: 执行 ./install.sh --help
    # Then: 显示使用说明
    # And: 显示参数列表
    # And: 退出码为 0
}
```

**验收标准**：
- [ ] 帮助信息完整
- [ ] 退出码为 0

**优先级**：🟢 低

---

### 3. 自动化触发模块测试

#### 3.1 post-merge hook 测试

##### TC-3.1.1: Hook 触发 - 正常路径

⚠️ [行为观察，意图待确认]

**测试目标**：验证 hook 成功触发补丁脚本

**测试用例**：
```bash
test_post_merge_success() {
    # Given: 补丁脚本已安装
    # When: 触发 post-merge hook
    # Then: 调用 apply-custom-patches.py
    # And: 调用 patch-feishu.py
    # And: 日志记录完整
}
```

**验收标准**：
- [ ] 两个补丁脚本被调用
- [ ] 日志记录完整
- [ ] 退出码为 0

**优先级**：🔴 高

---

##### TC-3.1.2: Hook 触发 - 补丁失败

⚠️ [行为观察，意图待确认]

**测试目标**：验证补丁失败时不中断 git 操作

**测试用例**：
```bash
test_post_merge_patch_failure() {
    # Given: 某个补丁脚本失败
    # When: 触发 post-merge hook
    # Then: 记录 WARNING 日志
    # And: 不中断 git 操作
    # And: 继续执行其他补丁
}
```

**验收标准**：
- [ ] 记录 WARNING 日志
- [ ] 不中断 git 操作
- [ ] 其他补丁继续执行

**优先级**：🔴 高

---

### 4. 集成测试

#### 4.1 端到端测试

##### TC-4.1.1: 完整安装流程

⚠️ [行为观察，意图待确认]

**测试目标**：验证从安装到自动触发的完整流程

**测试用例**：
```bash
test_end_to_end_install_and_trigger() {
    # Given: 干净的 hermes 环境
    # When: 执行 ./install.sh
    # And: 模拟 git pull 触发 post-merge hook
    # Then: 补丁成功应用
    # And: 日志记录完整
}
```

**验收标准**：
- [ ] 安装成功
- [ ] Hook 触发成功
- [ ] 补丁应用成功
- [ ] 日志记录完整

**优先级**：🔴 高

---

##### TC-4.1.2: 升级后补丁保持

⚠️ [行为观察，意图待确认]

**测试目标**：验证 Hermes 升级后补丁自动重新应用

**测试用例**：
```bash
test_patches_after_upgrade() {
    # Given: 已安装并应用补丁
    # When: 执行 hermes update (git pull)
    # Then: post-merge hook 自动触发
    # And: 补丁重新应用
    # And: 功能保持有效
}
```

**验收标准**：
- [ ] Hook 自动触发
- [ ] 补丁重新应用
- [ ] 功能保持有效

**优先级**：🔴 高

---

### 5. 计划中的功能测试（未实现）

#### 5.1 飞书 Skill Binding Plugin 测试

⚠️ [未验证，来自文档]

##### TC-5.1.1: Plugin 加载

**测试目标**：验证 plugin 成功加载

**测试用例**：
```python
def test_plugin_load():
    """测试 plugin 成功加载"""
    # Given: plugin 已安装
    # When: 启动 Gateway
    # Then: plugin 成功加载
    # And: 日志记录 "Loaded plugin: feishu-skill-binding"
```

**验收标准**：
- [ ] Plugin 加载成功
- [ ] 日志记录完整

**优先级**：🔴 高（待实现）

---

##### TC-5.1.2: Skill 注入 - 普通群聊

**测试目标**：验证普通群聊消息的 skill 注入

**测试用例**：
```python
def test_skill_injection_regular_group():
    """测试普通群聊消息的 skill 注入"""
    # Given: 配置了 chat_id binding
    # When: 普通群聊消息到达
    # Then: event.auto_skill 被设置
    # And: skill 在新会话中加载
```

**验收标准**：
- [ ] auto_skill 正确设置
- [ ] Skill 在新会话中加载

**优先级**：🔴 高（待实现）

---

##### TC-5.1.3: Skill 注入 - Thread 继承

**测试目标**：验证 thread 消息继承 parent chat 的 skill

**测试用例**：
```python
def test_skill_injection_thread_inherit():
    """测试 thread 消息继承 parent chat 的 skill"""
    # Given: 配置了 chat_id binding
    # When: thread 消息到达（无独立配置）
    # Then: event.auto_skill 继承 parent chat 的配置
```

**验收标准**：
- [ ] auto_skill 正确继承
- [ ] 日志记录继承关系

**优先级**：🔴 高（待实现）

---

##### TC-5.1.4: Skill 注入 - Thread 独立配置

**测试目标**：验证 thread 独立配置优先

**测试用例**：
```python
def test_skill_injection_thread_specific():
    """测试 thread 独立配置优先"""
    # Given: 同时配置了 chat_id 和 thread_id binding
    # When: thread 消息到达
    # Then: event.auto_skill 使用 thread_id 的配置
    # And: 不使用 chat_id 的配置
```

**验收标准**：
- [ ] auto_skill 使用 thread_id 配置
- [ ] 不使用 chat_id 配置

**优先级**：🔴 高（待实现）

---

##### TC-5.1.5: 未配置的群聊

**测试目标**：验证未配置的群聊不注入 skill

**测试用例**：
```python
def test_no_skill_injection_unconfigured():
    """测试未配置的群聊不注入 skill"""
    # Given: 群聊未配置 binding
    # When: 消息到达
    # Then: event.auto_skill 不被设置
    # And: 返回 None
```

**验收标准**：
- [ ] auto_skill 不被设置
- [ ] 返回 None

**优先级**：🟡 中（待实现）

---

## 测试覆盖统计

### 当前状态

| 模块 | 测试文件数 | 测试用例数 | 覆盖率 |
|------|-----------|-----------|--------|
| patches/apply-custom-patches.py | 0 | 0 | 0% |
| patches/patch-feishu.py | 0 | 0 | 0% |
| install.sh | 0 | 0 | 0% |
| hooks/post-merge | 0 | 0 | 0% |
| plugins/feishu-skill-binding (计划中) | 0 | 0 | 0% |
| **总计** | **0** | **0** | **0%** |

### 测试用例统计

| 优先级 | 测试用例数 | 状态 |
|--------|-----------|------|
| 🔴 高 | 12 | 待实现 |
| 🟡 中 | 9 | 待实现 |
| 🟢 低 | 1 | 待实现 |
| **总计** | **22** | **待实现** |

---

## 测试框架建议

⚠️ [行为观察，意图待确认]

**Python 测试框架**：
- **pytest**: 推荐的 Python 测试框架
- **pytest-mock**: Mock 支持
- **pytest-cov**: 覆盖率报告

**Shell 测试框架**：
- **bats**: Bash Automated Testing System
- **shunit2**: Shell 单元测试框架

**测试目录结构**：
```
hermes-extensions/
├── tests/
│   ├── test_apply_custom_patches.py
│   ├── test_patch_feishu.py
│   ├── test_install.sh (bats)
│   ├── test_post_merge.sh (bats)
│   └── fixtures/
│       ├── auxiliary_client.py (测试用)
│       ├── feishu_legacy.py (测试用)
│       └── feishu_plugin.py (测试用)
├── pytest.ini
└── .bats.conf
```

---

## 下一步

**Step 4：用户意图确认** — 确认用户变更意图，生成 `intent.md`

**用户确认点 4**：

```
已完成测试基线生成，识别到：

测试覆盖现状：
- 当前无任何测试
- 0% 测试覆盖率

测试用例统计：
- 22 个测试用例待实现
- 12 个高优先级
- 9 个中优先级
- 1 个低优先级

计划中的功能测试：
- 5 个 plugin 测试用例（待实现）

请确认：
1. 测试清单是否完整？
2. 优先级划分是否合理？
3. 测试框架选择是否合适？

确认后继续 Step 4（用户意图确认）。
```
