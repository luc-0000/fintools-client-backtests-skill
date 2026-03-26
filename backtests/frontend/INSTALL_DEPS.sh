#!/bin/bash

# 安装迁移所需的所有依赖

echo "开始安装迁移所需的依赖..."

# 核心依赖
echo "安装核心依赖..."
npm install react-router-dom zustand axios

# UI 组件库
echo "安装 Ant Design 和 ProComponents..."
npm install antd @ant-design/pro-components

# 图标库（可选）
echo "安装图标库..."
npm install @ant-design/icons

# TypeScript 类型
echo "安装 TypeScript 类型定义..."
npm install -D @types/react @types/react-dom

echo "依赖安装完成！"
echo ""
echo "请运行以下命令启动开发服务器:"
echo "  npm run dev"
