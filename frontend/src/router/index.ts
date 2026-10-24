/**
 * 路由表 + 全局路由守卫.
 *
 * 页面即路由: 每个页面一个 path, component 用 () => import(...) 懒加载
 * (第一次访问该页面才下载对应的 js, 首屏更快).
 * meta.title: 显示在顶栏的页面标题(App.vue 读取).
 */
import { createRouter, createWebHistory } from "vue-router";
import { useUserStore } from "../stores/user";

const router = createRouter({
  // history 模式: URL 里没有 # 号, 更美观(需要 dev 服务器/部署环境支持回退到 index.html)
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/login",
      name: "login",
      component: () => import("../views/LoginView.vue"),
      meta: { public: true, title: "登录" }, // meta.public = true: 登录页不需要登录态
    },
    { path: "/", name: "workbench", component: () => import("../views/WorkbenchView.vue"), meta: { title: "检测工作台" } },
    { path: "/tasks", name: "tasks", component: () => import("../views/TasksView.vue"), meta: { title: "任务管理" } },
    // 动态参数: /tasks/TSK2026... 里的 taskNo 会注入到组件的 route.params.taskNo
    { path: "/tasks/:taskNo", name: "task-detail", component: () => import("../views/TaskDetailView.vue"), meta: { title: "任务详情" } },
    { path: "/stats", name: "stats", component: () => import("../views/StatsView.vue"), meta: { title: "统计看板" } },
    { path: "/reports", name: "reports", component: () => import("../views/ReportsView.vue"), meta: { title: "报告中心" } },
    { path: "/users", name: "users", component: () => import("../views/UsersView.vue"), meta: { title: "用户管理" } },
  ],
});

// 全局路由守卫: 每次页面跳转前都会执行(相当于后端路由的"依赖注入"前端版).
router.beforeEach((to) => {
  // 在守卫回调内部才调用 useUserStore():
  // Pinia 必须先被 app.use() 激活, 而守卫回调在首次导航时才执行, 时机刚好.
  const { isLoggedIn } = useUserStore();

  // 规则 1: 目标页面需要登录, 但用户没登录 → 踢去登录页
  if (!to.meta.public && !isLoggedIn) {
    return { path: "/login" };
  }
  // 规则 2: 已登录还去登录页 → 直接送回工作台
  if (to.path === "/login" && isLoggedIn) {
    return { path: "/" };
  }
  // 返回 undefined/true = 放行
});

export default router;
