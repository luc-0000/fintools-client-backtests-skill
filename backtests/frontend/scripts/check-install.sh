#!/bin/bash

echo "=== 检查依赖安装状态 ==="
echo ""

# 检查 package.json
echo "1. 检查 package.json 中的依赖："
grep -A 10 '"dependencies"' package.json | grep -E "(antd|react-router|zustand|axios)" || echo "  ❌ 依赖尚未添加到 package.json"

echo ""
echo "2. 检查 node_modules 中的关键包："
echo "  antd: $(ls node_modules 2>/dev/null | grep -c '^antd$' || echo 0)"
echo "  @ant-design/pro-components: $(ls node_modules/@ant-design 2>/dev/null | grep -c 'pro-components' || echo 0)"
echo "  react-router-dom: $(ls node_modules 2>/dev/null | grep -c '^react-router-dom$' || echo 0)"
echo "  zustand: $(ls node_modules 2>/dev/null | grep -c '^zustand$' || echo 0)"
echo "  axios: $(ls node_modules 2>/dev/null | grep -c '^axios$' || echo 0)"

echo ""
echo "3. node_modules 总包数："
ls node_modules 2>/dev/null | wc -l

echo ""
echo "4. TypeScript 类型检查："
npx tsc --noEmit 2>&1 | head -20

echo ""
echo "=== 检查完成 ==="
