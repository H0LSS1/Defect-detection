<!-- 应用根组件: 整体布局骨架.
     登录页(meta.public)全屏显示; 其他页面套"侧边菜单 + 顶栏 + 内容区"的后台布局. -->
<script setup lang="ts">
import { computed, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useUserStore } from "./stores/user";

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();

// 登录页不需要后台布局(通过路由 meta.public 判断)
const isPublic = computed(() => route.meta.public === true);

// 自动补拉用户信息: 有 token 但还没拉取用户资料时(刚登录/刚刷新页面),
// 自动调 /auth/me, 顶栏才能正确显示用户名而不是"用户".
watch(
  () => userStore.isLoggedIn,
  (loggedIn) => {
    if (loggedIn && !userStore.userInfo) userStore.fetchUserInfo();
  },
  { immediate: true }, // 组件挂载时立即检查一次
);

// 顶栏标题: 取路由 meta.title(见 router/index.ts), 没配置就用默认值
const pageTitle = computed(() => (route.meta.title as string) ?? "检测工作台");

// 侧边菜单项: el-menu 开启 router 模式后, index 就是跳转路径.
// 用户管理仅对 admin 显示 —— menus 变成 computed, 角色变化时菜单自动更新.
const menus = computed(() => {
  const base = [
    { path: "/", label: "检测工作台", icon: "Upload" },
    { path: "/tasks", label: "任务管理", icon: "List" },
    { path: "/stats", label: "统计看板", icon: "DataAnalysis" },
    { path: "/reports", label: "报告中心", icon: "Document" },
  ];
  if (userStore.isAdmin) {
    base.push({ path: "/users", label: "用户管理", icon: "User" });
  }
  return base;
});

function handleLogout() {
  userStore.logout();
  router.push("/login");
}
</script>

<template>
  <!-- 登录页: 不套后台布局, 直接全屏渲染 -->
  <router-view v-if="isPublic" />

  <el-container v-else class="layout">
    <!-- 侧边栏: 深色渐变背景, logo 带图标, 菜单项圆角高亮 -->
    <el-aside width="220px" class="aside">
      <div class="logo">
        <el-icon size="26" color="#1677ff"><Camera /></el-icon>
        <span>焊缝缺陷检测平台</span>
      </div>
      <el-menu :default-active="route.path" router class="menu">
        <el-menu-item v-for="m in menus" :key="m.path" :index="m.path">
          <el-icon><component :is="m.icon" /></el-icon>
          <span>{{ m.label }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <!-- 顶栏: 左侧页面标题(随路由变化), 右侧头像下拉 -->
      <el-header class="header">
        <div class="header-title">{{ pageTitle }}</div>
        <el-dropdown v-if="userStore.isLoggedIn" @command="handleLogout">
          <span class="user">
            <!-- el-avatar 头像: 取用户名首字符 -->
            <el-avatar :size="32" class="avatar">
              {{ (userStore.userInfo?.username ?? "U").charAt(0).toUpperCase() }}
            </el-avatar>
            {{ userStore.userInfo?.username ?? "用户" }}
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout">
                <el-icon><SwitchButton /></el-icon>退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>

      <!-- 内容区: router-view 带 fade 动画(见 style.css), 页面切换不生硬 -->
      <el-main class="main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.layout {
  height: 100vh; /* 占满整个视口高度 */
}
.aside {
  background: linear-gradient(180deg, #001529 0%, #002140 100%); /* 深色纵向渐变 */
  display: flex;
  flex-direction: column;
}
.logo {
  color: #fff;
  font-size: 15px;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 60px;
  border-bottom: 1px solid #ffffff1a; /* logo 与菜单之间的分隔线(半透明白) */
}
.menu {
  border-right: none;   /* 去掉菜单默认右边框, 融入深色侧栏 */
  background: transparent;
  padding: 8px;         /* 留出边距, 菜单项圆角才好看 */
}
.menu :deep(.el-menu-item) {
  color: #ffffffa6;             /* 半透明白文字 */
  border-radius: 8px;           /* 圆角菜单项 */
  margin-bottom: 4px;
  height: 44px;
}
.menu :deep(.el-menu-item:hover) {
  color: #fff;
  background-color: #ffffff1a;  /* 悬浮半透明白底 */
}
.menu :deep(.el-menu-item.is-active) {
  color: #fff;
  background: linear-gradient(90deg, #1677ff, #4096ff); /* 选中项蓝色渐变高亮 */
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #eee;
  background: #fff;
}
.header-title {
  font-size: 16px;
  font-weight: 600;
}
.user {
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.avatar {
  background: #1677ff;
  font-weight: bold;
}
.main {
  background: #f5f7fa;
  overflow: auto; /* 内容超出时出滚动条, 而不是撑破布局 */
}
</style>
