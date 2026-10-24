/**
 * 应用入口: 把 Vue、Pinia(全局状态)、Router(页面路由)、Element Plus(UI 组件库) 组装到一起.
 * 执行顺序: 创建 app → 装插件 → 挂载到 #app(index.html 里的 div).
 */
import { createApp } from "vue";
import { createPinia } from "pinia";

// Element Plus: 饿了么开源的 Vue3 组件库(表单/表格/弹窗...全都有)
import ElementPlus from "element-plus";
import "element-plus/dist/index.css";
// Element Plus 的图标组件包, 全局注册后模板里直接 <el-icon><User /></el-icon> 这样用
import * as ElementPlusIconsVue from "@element-plus/icons-vue";

import App from "./App.vue";
import router from "./router";
import "./style.css"; // 全局视觉规范(卡片圆角阴影/页面过渡动画等)

const app = createApp(App);

app.use(createPinia()); // 全局状态管理, 必须在 router 之前装(路由守卫里用到了仓库)
app.use(router);
app.use(ElementPlus);   // 注册所有 el-xxx 组件

// 把所有图标组件注册成全局组件(组件名 = 图标名, 如 <User />, <Upload />)
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component);
}

app.mount("#app");
