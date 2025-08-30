# 登录页面输入框对齐优化

## 问题描述
登录页面中用户名和密码输入框的前缀图标没有完美对齐，影响视觉效果。

## 解决方案

### 1. 固定前缀容器宽度
```scss
.ant-input-prefix {
  width: 44px; // 固定宽度确保对齐
  display: flex;
  align-items: center;
  justify-content: center;
}
```

### 2. 统一图标样式
```scss
.anticon {
  font-size: 16px;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}
```

### 3. 优化输入框布局
- 使用 flexbox 确保垂直居中
- 统一输入框高度为 48px
- 精确控制内边距避免重复

## 修复效果
✅ 所有前缀图标完美对齐  
✅ 输入框内容垂直居中  
✅ 统一的视觉风格  
✅ 良好的交互反馈