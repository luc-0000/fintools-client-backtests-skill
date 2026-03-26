# Snowy Vite - 基于 Vite + React + Ant Design Pro

这是从 snowy_umi4 项目迁移而来的现代化前端项目。

## 技术栈

- **构建工具**: Vite
- **框架**: React 19 + TypeScript
- **UI 库**: Ant Design 5.x + Ant Design Pro Components
- **路由**: React Router v6
- **状态管理**: Zustand
- **HTTP 请求**: Axios
- **日期处理**: dayjs

## 项目结构

src/
├── components/      # 公共组件
├── layouts/         # 布局组件
├── pages/           # 页面组件
│   ├── Agents/      # 代理管理
│   ├── Pools/       # 池子管理
│   ├── Rules/       # 规则管理
│   ├── Simulators/  # 模拟器管理
│   └── Shared/      # 共享常量
├── router/          # 路由配置
├── services/        # API 服务层
├── store/           # Zustand 状态管理
├── types/           # TypeScript 类型定义
└── utils/           # 工具函数

## 开发

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览生产构建
npm run preview
