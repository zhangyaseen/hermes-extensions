# hermes-extensions

Hermes Agent 核心补丁机制管理。

将 Hermes Agent 的自定义补丁脚本纳入版本管理，通过 git submodule 集成到 [hermes-skills](https://github.com/zhangyaseen/hermes-skills)。

## 背景

`hermes update` 会拉取上游更新，可能覆盖本地修改。此 repo 管理需要在每次 update 后自动重新应用的补丁：

| 补丁 | 目标文件 | 作用 |
|------|----------|------|
| `apply-custom-patches.py` | `agent/auxiliary_client.py` | 注册 `alibaba: qwen3.7-plus` 到 `_PROVIDER_VISION_MODELS`，启用多模态图片输入 |
| `patch-feishu.py` | `gateway/platforms/feishu.py` | 添加 pipeline routing 功能（`pipeline` 字段 + 路由方法） |
| `hermes-custom-patches.patch` | (legacy) | 旧版 patch 文件，大部分已禁用，保留兼容 |

## 安装

```bash
# 通过 hermes-skills submodule 安装（推荐）
cd hermes-skills/hermes-extensions
./install.sh

# 或独立安装
git clone git@github.com:zhangyaseen/hermes-extensions.git
cd hermes-extensions
./install.sh
```

安装脚本会：
1. 将 `patches/` 下的文件 symlink 到 `~/.hermes/scripts/`
2. 将 `hooks/post-merge` 复制到 `~/.hermes/hermes-agent/.git/hooks/post-merge`

## 验证

```bash
# 检查 symlink
ls -la ~/.hermes/scripts/apply-custom-patches.py
# 应指向 hermes-extensions/patches/apply-custom-patches.py

# 检查 hook
cat ~/.hermes/hermes-agent/.git/hooks/post-merge

# 模拟 hermes update 触发
cd ~/.hermes/hermes-agent && git merge --ff-only origin/main
cat /tmp/hermes-post-merge.log
```

## 卸载

```bash
./install.sh --uninstall
```

移除 symlink 和 git hook，原始文件保留在本 repo 中。

## 目录结构

```
hermes-extensions/
├── patches/
│   ├── apply-custom-patches.py   # auxiliary_client.py 补丁
│   ├── patch-feishu.py           # feishu.py pipeline routing 补丁
│   └── hermes-custom-patches.patch  # legacy patch 文件
├── hooks/
│   └── post-merge               # git hook，update 后自动打补丁
├── install.sh                   # 安装/卸载脚本
└── README.md
```

## 工作原理

```
hermes update
  → git pull (触发 post-merge hook)
  → post-merge hook 调用 ~/.hermes/scripts/apply-custom-patches.py
  → post-merge hook 调用 ~/.hermes/scripts/patch-feishu.py
  → 补丁通过 symlink 指向本 repo 的 patches/ 目录
  → 补丁应用完成，日志写入 /tmp/hermes-post-merge.log
```

## 注意事项

- 补丁脚本通过**标记字符串匹配**而非行号定位，适应上游代码行数变化
- 如果上游代码重构导致标记字符串不存在，补丁会跳过并记录 warning
- 定期检查 `/tmp/hermes-post-merge.log` 确认补丁正常应用
