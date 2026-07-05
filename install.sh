#!/bin/bash
# hermes-extensions installer
#
# 将补丁脚本 symlink 到 ~/.hermes/scripts/，安装 git hook 到 hermes-agent。
#
# 用法: ./install.sh
# 卸载: ./install.sh --uninstall

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HERMES_HOME="${HOME}/.hermes"
HERMES_AGENT_DIR="${HERMES_HOME}/hermes-agent"

PATCH_FILES=("apply-custom-patches.py" "patch-feishu.py" "hermes-custom-patches.patch")

# 新增：Plugin 目录
PLUGIN_DIRS=("feishu-skill-binding")

uninstall() {
    echo "Uninstalling hermes-extensions..."

    # 移除 symlinks
    for f in "${PATCH_FILES[@]}"; do
        target="${HERMES_HOME}/scripts/${f}"
        if [ -L "$target" ]; then
            rm "$target"
            echo "REMOVED: ${f}"
        fi
    done

    # 移除 plugin symlinks
    for plugin in "${PLUGIN_DIRS[@]}"; do
        target="${HERMES_HOME}/plugins/${plugin}"
        if [ -L "$target" ]; then
            rm "$target"
            echo "REMOVED: plugin ${plugin}"
        fi
    done

    # 移除 git hook
    hook_target="${HERMES_AGENT_DIR}/.git/hooks/post-merge"
    if [ -f "$hook_target" ]; then
        rm "$hook_target"
        echo "REMOVED: post-merge hook"
    fi

    echo "Done. Original files are preserved in this repo."
}

install() {
    echo "Installing hermes-extensions..."

    # 1. 确保目标目录存在
    mkdir -p "${HERMES_HOME}/scripts"

    # 2. Symlink 补丁脚本
    for f in "${PATCH_FILES[@]}"; do
        target="${HERMES_HOME}/scripts/${f}"
        source="${SCRIPT_DIR}/patches/${f}"

        if [ ! -f "$source" ]; then
            echo "ERROR: source file not found: ${source}"
            exit 1
        fi

        if [ -L "$target" ]; then
            current_target=$(readlink "$target")
            if [ "$current_target" = "$source" ]; then
                echo "SKIP: ${f} already symlinked correctly"
                continue
            else
                echo "UPDATE: ${f} points to ${current_target}, updating..."
                rm "$target"
            fi
        elif [ -f "$target" ]; then
            echo "BACKUP: ${f} exists as regular file, renaming to ${f}.bak"
            mv "$target" "${target}.bak"
        fi

        ln -s "$source" "$target"
        echo "LINKED: ${f} -> ${source}"
    done

    # 3. Symlink plugins
    mkdir -p "${HERMES_HOME}/plugins"
    for plugin in "${PLUGIN_DIRS[@]}"; do
        target="${HERMES_HOME}/plugins/${plugin}"
        source="${SCRIPT_DIR}/plugins/${plugin}"

        if [ ! -d "$source" ]; then
            echo "ERROR: plugin directory not found: ${source}"
            continue
        fi

        if [ -L "$target" ]; then
            current_target=$(readlink "$target")
            if [ "$current_target" = "$source" ]; then
                echo "SKIP: plugin ${plugin} already symlinked"
                continue
            else
                echo "UPDATE: plugin ${plugin} points to ${current_target}, updating..."
                rm "$target"
            fi
        elif [ -d "$target" ]; then
            echo "BACKUP: plugin ${plugin} exists as directory, renaming to ${plugin}.bak"
            mv "$target" "${target}.bak"
        fi

        ln -s "$source" "$target"
        echo "LINKED: plugin ${plugin} -> ${source}"
    done

    # 4. 安装 git hook
    hook_target="${HERMES_AGENT_DIR}/.git/hooks/post-merge"
    hook_source="${SCRIPT_DIR}/hooks/post-merge"

    if [ ! -d "${HERMES_AGENT_DIR}/.git" ]; then
        echo "WARNING: ${HERMES_AGENT_DIR}/.git not found, skip hook installation"
        echo "         Run this again after hermes-agent is installed."
    else
        cp "$hook_source" "$hook_target"
        chmod +x "$hook_target"
        echo "INSTALLED: post-merge hook -> ${hook_target}"
    fi

    echo ""
    echo "Installation complete."
    echo "Verify with: ls -la ~/.hermes/scripts/apply-custom-patches.py"
}

# Parse arguments
case "${1:-}" in
    --uninstall|-u)
        uninstall
        ;;
    --help|-h)
        echo "Usage: $0 [--uninstall]"
        echo ""
        echo "  (no args)    Install patches and git hook"
        echo "  --uninstall  Remove symlinks and git hook"
        echo "  --help       Show this help"
        ;;
    "")
        install
        ;;
    *)
        echo "Unknown option: $1"
        echo "Run '$0 --help' for usage."
        exit 1
        ;;
esac
