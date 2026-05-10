# Web 前端开发核心技术能力

本指南详细说明了前端工程师在面试中所需具备的核心能力维度，这些维度与我们的面试题库直接对应。

## JavaScript与TypeScript
- **执行机制**：原型与原型链、闭包应用与内存表现、执行上下文（Scope/this/Variable Hoisting）。
- **同步/异步**：Promise A+ 规范、Generator、async/await 底层逻辑、浏览器与 Node.js 事件循环机制对比。
- **现代特性**：ES6-ES14 系列新特性、解构赋值原理、Proxy 与 Reflect、Decorator (装饰器) 提案。
- **TypeScript 高级**：类型系统核心（Interface vs Type）、泛型高级应用、类型编程（Infer/Mapped Types/Conditional Types）、tsconfig 常用配置。

## CSS与页面布局
- **布局体系**：盒子模型细节、BFC/IFC 概念、Flexbox 属性全集、Grid 网格布局高级应用、响应式设计常见方案（Media Query/Container Query）。
- **底层原理**：CSS 选择器优先级、继承与层叠机制、浏览器渲染流水线（CRP）、重绘（Repaint）与重排（Reflow）性能优化方案。
- **现代化工具**：CSS Variables、CSS Modules、Sass/Less 深度特性、Tailwind CSS 类原子化理念、CSS-in-JS。

## 框架原理 (Vue/React)
- **React 体系**：JSX 编译机制、Hooks 设计思想与闭包陷阱、Fiber 架构原理（时间分片/双缓存）、Concurrent Mode、高阶组件 (HOC) 与 Render Props。
- **Vue 体系**：Vue 2 响应式 (Object.defineProperty) 与 Vue 3 响应式 (Proxy) 差异、模板编译原理（Patch Flags/Block Tree）、Composition API 演进、插件机制。
- **通用能力**：虚拟 DOM 与 Diff 算法演进、组件通信模式、状态管理逻辑（Redux/Pinia/Zustand）、离屏渲染（Portal/Teleport）。

## 前端工程化与工具链
- **构建工具**：Webpack 核心逻辑（Loader/Plugin/Tree Shaking/HMR）、Vite 基于 ESM 的快速开发原理、Rollup 与 esbuild 优劣分析。
- **包管理与规范**：npm/yarn/pnpm 依赖处理差异、Monorepo 架构设计（Lerna/Turborepo/pnpm workspace）、Git Flow 与 Commit 规范。
- **质量保障**：单元测试 (Jest/Vitest)、E2E 测试 (Cypress/Playwright)、静态扫描工具、CI/CD 自动化流水线。

## 性能优化与前端安全
- **指标评估**：Web Vitals 核心指标 (LCP, FID, CLS, INP)、Chrome DevTools Performance 性能面板分析。
- **性能方案**：代码分割 (Code Splitting)、懒加载、预加载机制 (prefetch/preload)、Service Worker 缓存策略。
- **安全攻防**：XSS 防御、CSRF 原理与 SameSite 属性、点击劫持、内容安全策略 (CSP)、HTTPS 原理及 TLS 握手。
- **跨端架构**：H5 适配方案、Hybrid 混合开发原理、SSG/SSR/ISR 渲染模式差异、微前端架构 (qiankun)。
