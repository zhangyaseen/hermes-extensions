#!/bin/bash
# 飞书 Skill Binding Plugin 部署完成脚本
# 使用方法：从 Gateway 外部的终端执行 ./complete_deployment.sh

set -e

echo "================================================================================"
echo "                    飞书 Skill Binding Plugin 部署完成"
echo "================================================================================"
echo ""

# Step 1: 验证 Plugin 安装
echo "📦 Step 1: 验证 Plugin 安装..."
if [ -L ~/.hermes/plugins/feishu-skill-binding ]; then
    echo "   ✅ Plugin symlink 存在"
    readlink ~/.hermes/plugins/feishu-skill-binding
else
    echo "   ❌ Plugin symlink 不存在，请先运行 install.sh"
    exit 1
fi
echo ""

# Step 2: 验证配置文件
echo "⚙️  Step 2: 验证配置文件..."
if grep -q "channel_skill_bindings" ~/.hermes/config.yaml; then
    echo "   ✅ channel_skill_bindings 配置存在"
    grep -A 5 "channel_skill_bindings" ~/.hermes/config.yaml | head -6
else
    echo "   ⚠️  channel_skill_bindings 配置不存在"
    echo "   请手动添加到 ~/.hermes/config.yaml"
fi
echo ""

# Step 3: 重启 Gateway
echo "🔄 Step 3: 重启 Gateway..."
hermes gateway restart
echo "   ✅ Gateway 重启命令已发送"
echo ""

# Step 4: 等待 Gateway 启动
echo "⏳ Step 4: 等待 Gateway 启动..."
sleep 3
echo ""

# Step 5: 验证 Plugin 加载
echo "🔍 Step 5: 验证 Plugin 加载..."
echo "   查看日志（按 Ctrl+C 退出）："
echo ""
tail -f ~/.hermes/logs/gateway.log | grep --line-buffered -E "(plugin|feishu-skill-binding|Loaded)" &
TAIL_PID=$!

# 等待 10 秒查看日志
sleep 10
kill $TAIL_PID 2>/dev/null || true

echo ""
echo "================================================================================"
echo "✅ 部署完成！"
echo ""
echo "📋 验证步骤："
echo "   1. 在配置的群聊中发送消息"
echo "   2. 观察日志是否显示：[feishu-skill-binding] 注入 skills=[...]"
echo "   3. 验证 skill 是否自动加载"
echo ""
echo "📚 详细文档："
echo "   - 部署指南：hermes-extensions/iterations/CR-20260705-001-feishu-skill-binding/DEPLOYMENT_GUIDE.md"
echo "   - 实施报告：hermes-extensions/iterations/CR-20260705-001-feishu-skill-binding/IMPLEMENTATION_COMPLETE.md"
echo "================================================================================"
