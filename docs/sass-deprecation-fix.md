# Sass 弃用警告修复文档

## 问题描述

前端项目在启动时出现多个 Sass 弃用警告：

1. `@import` 规则已弃用，将在 Dart Sass 3.0.0 中移除
2. `darken()` 函数已弃用，建议使用 `color.adjust()` 或 `color.scale()`
3. 全局内置函数已弃用
4. 传统 JS API 已弃用

## 修复方案

### 1. 更新 @import 语法为 @use

**修复前：**
```scss
@import '@/styles/variables.scss';
```

**修复后：**
```scss
@use '@/styles/variables.scss' as *;
```

### 2. 更新颜色函数

**修复前：**
```scss
color: darken($primary-color, 10%);
```

**修复后：**
```scss
@use 'sass:color';
color: color.adjust($primary-color, $lightness: -10%);
```

### 3. 更新 Vite 配置

**修复前：**
```typescript
css: {
  preprocessorOptions: {
    scss: {
      additionalData: `@import "@/styles/variables.scss";`,
    },
  },
}
```

**修复后：**
```typescript
css: {
  preprocessorOptions: {
    scss: {
      additionalData: `@use "@/styles/variables.scss" as *;`,
      api: 'modern-compiler',
    },
  },
}
```

## 修复的文件列表

### 核心样式文件
- `frontend/src/styles/variables.scss` - 添加 `@use 'sass:color'`，更新 `darken()` 函数
- `frontend/src/styles/global.scss` - 更新 `@import` 为 `@use`，修复 `darken()` 函数

### 组件样式文件
- `frontend/src/components/layout/style.scss`
- `frontend/src/components/ui/Button/style.scss` - 修复多个 `darken()` 函数调用
- `frontend/src/components/ui/Card/style.scss`
- `frontend/src/components/ui/Table/style.scss`
- `frontend/src/components/ui/Input/style.scss` - 修复 `darken()` 函数

### 页面样式文件
- `frontend/src/pages/Login/style.scss`
- `frontend/src/pages/Dashboard/style.scss`
- `frontend/src/pages/MenuManagement/style.scss`
- `frontend/src/pages/MenuManagement/components/IconSelector.scss`
- `frontend/src/pages/MenuManagement/components/MenuPreview.scss`

### 配置文件
- `frontend/vite.config.ts` - 更新 CSS 预处理器配置

## 验证结果

修复完成后，前端服务器启动时不再出现 Sass 弃用警告，所有样式正常工作。

## 最佳实践

1. **使用现代 Sass 语法**：优先使用 `@use` 而不是 `@import`
2. **使用新的颜色函数**：使用 `color.adjust()` 替代 `darken()`、`lighten()` 等
3. **模块化导入**：使用 `@use` 可以更好地控制命名空间
4. **配置现代编译器**：在构建工具中启用 `modern-compiler` API

## 相关链接

- [Sass @use 规则文档](https://sass-lang.com/documentation/at-rules/use)
- [Sass 颜色函数迁移指南](https://sass-lang.com/d/color-functions)
- [Sass @import 弃用说明](https://sass-lang.com/d/import)