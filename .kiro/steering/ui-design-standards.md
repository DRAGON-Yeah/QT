# UI设计标准和组件规范

## 设计原则
- **简洁明了**：界面简洁，信息层次清晰
- **响应式设计**：支持多设备访问
- **一致性**：保持界面风格一致
- **易用性**：操作简单，学习成本低
- **专业性**：体现量化交易的专业特色

## 色彩规范
### 主色调
- **主色调**：#1890FF（科技蓝）- 体现专业和科技感
- **辅助色**：
  - #52C41A（成功绿）- 盈利、成功状态
  - #FAAD14（警告橙）- 警告、注意状态
  - #F5222D（错误红）- 亏损、错误状态

### 中性色
- **纯黑**：#000000 - 重要文字
- **纯白**：#FFFFFF - 背景色
- **背景灰**：#F5F5F5 - 页面背景
- **主要文字**：#262626 - 标题和重要内容
- **次要文字**：#8C8C8C - 辅助信息
- **禁用文字**：#BFBFBF - 禁用状态

### 交易专用色彩
```css
:root {
  /* 涨跌颜色 */
  --color-up: #52C41A;      /* 上涨绿色 */
  --color-down: #F5222D;    /* 下跌红色 */
  --color-neutral: #8C8C8C; /* 平盘灰色 */
  
  /* 风险等级颜色 */
  --risk-low: #52C41A;      /* 低风险 */
  --risk-medium: #FAAD14;   /* 中风险 */
  --risk-high: #F5222D;     /* 高风险 */
}
```

## 字体规范
### 字体层级
- **主标题**：24px，字重600，行高32px - 页面主标题
- **次标题**：20px，字重600，行高28px - 模块标题
- **小标题**：16px，字重500，行高24px - 卡片标题
- **正文**：14px，字重400，行高22px - 正文内容
- **辅助文字**：12px，字重400，行高20px - 说明文字

### 数字显示规范
```css
.number-display {
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-variant-numeric: tabular-nums;
}

.price-display {
  font-size: 16px;
  font-weight: 600;
}

.percentage-display {
  font-size: 14px;
  font-weight: 500;
}
```

## 间距规范
### 标准间距
- **页面边距**：24px - 页面内容与边界的距离
- **组件间距**：16px - 不同组件之间的距离
- **元素间距**：8px - 相关元素之间的距离
- **内容间距**：4px - 紧密相关内容的距离

### 响应式间距
```css
/* 桌面端 */
@media (min-width: 1200px) {
  .container { padding: 24px; }
  .component-gap { margin-bottom: 16px; }
}

/* 平板端 */
@media (min-width: 768px) and (max-width: 1199px) {
  .container { padding: 16px; }
  .component-gap { margin-bottom: 12px; }
}

/* 移动端 */
@media (max-width: 767px) {
  .container { padding: 12px; }
  .component-gap { margin-bottom: 8px; }
}
```

## 组件规范
### 按钮组件
```css
.btn {
  height: 32px; /* 默认高度 */
  padding: 0 16px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
}

.btn-large { height: 48px; font-size: 16px; }
.btn-small { height: 24px; font-size: 12px; padding: 0 8px; }

.btn-primary { background: #1890FF; color: white; }
.btn-success { background: #52C41A; color: white; }
.btn-danger { background: #F5222D; color: white; }
.btn-warning { background: #FAAD14; color: white; }
```

### 输入框组件
```css
.input {
  height: 32px;
  padding: 0 12px;
  border: 1px solid #D9D9D9;
  border-radius: 6px;
  font-size: 14px;
}

.input:focus {
  border-color: #1890FF;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.input-error {
  border-color: #F5222D;
}
```

### 卡片组件
```css
.card {
  background: white;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  padding: 16px;
}

.card-header {
  padding-bottom: 12px;
  border-bottom: 1px solid #F0F0F0;
  margin-bottom: 16px;
}
```

## 布局规范
### 栅格系统
```css
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
}

.row {
  display: flex;
  flex-wrap: wrap;
  margin: 0 -8px;
}

.col {
  padding: 0 8px;
  flex: 1;
}

.col-6 { flex: 0 0 50%; }
.col-4 { flex: 0 0 33.333%; }
.col-3 { flex: 0 0 25%; }
```

### 页面布局
```css
.layout {
  display: flex;
  min-height: 100vh;
}

.layout-header {
  height: 64px;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.layout-sider {
  width: 240px;
  background: #001529;
  transition: width 0.3s;
}

.layout-sider.collapsed {
  width: 64px;
}

.layout-content {
  flex: 1;
  padding: 24px;
  background: #F5F5F5;
}
```

## 交互状态
### 悬停状态
```css
.interactive:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;
}

.btn:hover {
  opacity: 0.8;
}
```

### 加载状态
```css
.loading {
  position: relative;
  pointer-events: none;
}

.loading::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #1890FF;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}
```

## 响应式设计
### 断点设置
```css
/* 大屏幕 - 桌面端 */
@media (min-width: 1200px) {
  .desktop-only { display: block; }
  .mobile-only { display: none; }
}

/* 中等屏幕 - 平板端 */
@media (min-width: 768px) and (max-width: 1199px) {
  .layout-sider { width: 200px; }
  .card { padding: 12px; }
}

/* 小屏幕 - 移动端 */
@media (max-width: 767px) {
  .desktop-only { display: none; }
  .mobile-only { display: block; }
  .layout-sider { 
    position: fixed;
    z-index: 1000;
    transform: translateX(-100%);
  }
  .layout-sider.open {
    transform: translateX(0);
  }
}
```

## 数据可视化规范
### 图表颜色
```css
:root {
  --chart-colors: #1890FF, #52C41A, #FAAD14, #F5222D, #722ED1, #13C2C2;
  --candlestick-up: #52C41A;
  --candlestick-down: #F5222D;
  --volume-color: rgba(24, 144, 255, 0.6);
}
```

### K线图样式
```css
.kline-chart {
  background: #1a1a1a;
  color: #ffffff;
}

.kline-up {
  fill: #52C41A;
  stroke: #52C41A;
}

.kline-down {
  fill: #F5222D;
  stroke: #F5222D;
}
```

## 表格组件
### 基础表格样式
```css
.table {
  width: 100%;
  border-collapse: collapse;
  background: white;
}

.table th {
  background: #FAFAFA;
  padding: 12px 16px;
  text-align: left;
  font-weight: 600;
  border-bottom: 1px solid #F0F0F0;
}

.table td {
  padding: 12px 16px;
  border-bottom: 1px solid #F0F0F0;
}

.table tr:hover {
  background: #F5F5F5;
}
```

### 数据表格特殊样式
```css
.price-cell {
  font-family: monospace;
  text-align: right;
}

.change-positive {
  color: #52C41A;
}

.change-negative {
  color: #F5222D;
}

.status-active {
  color: #52C41A;
}

.status-inactive {
  color: #8C8C8C;
}
```

## 表单组件
### 表单布局
```css
.form-group {
  margin-bottom: 16px;
}

.form-label {
  display: block;
  margin-bottom: 4px;
  font-weight: 500;
  color: #262626;
}

.form-control {
  width: 100%;
  height: 32px;
  padding: 0 12px;
  border: 1px solid #D9D9D9;
  border-radius: 6px;
}

.form-error {
  color: #F5222D;
  font-size: 12px;
  margin-top: 4px;
}
```

## 动画效果
### 基础动画
```css
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideIn {
  from { transform: translateX(-100%); }
  to { transform: translateX(0); }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.fade-in {
  animation: fadeIn 0.3s ease-in-out;
}

.slide-in {
  animation: slideIn 0.3s ease-in-out;
}
```

## 可访问性规范
### 键盘导航
```css
.focusable:focus {
  outline: 2px solid #1890FF;
  outline-offset: 2px;
}

.skip-link {
  position: absolute;
  top: -40px;
  left: 6px;
  background: #1890FF;
  color: white;
  padding: 8px;
  text-decoration: none;
  z-index: 1000;
}

.skip-link:focus {
  top: 6px;
}
```

### 屏幕阅读器支持
```html
<!-- 使用语义化标签 -->
<main role="main">
  <section aria-labelledby="trading-section">
    <h2 id="trading-section">交易管理</h2>
  </section>
</main>

<!-- 提供替代文本 -->
<img src="chart.png" alt="BTC/USDT价格走势图" />

<!-- 表单标签关联 -->
<label for="price-input">价格</label>
<input id="price-input" type="number" />
```