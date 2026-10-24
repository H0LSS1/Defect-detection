<!-- 用户管理(仅 admin 可见): 用户列表 + 启停开关 + 角色调整.
     自己的行禁止操作(后端同样校验, 前端只是提前给出提示). -->
<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { listUsers, updateUser } from "../api/auth";
import type { UserOut, UserRole } from "../api/types";
import { useUserStore } from "../stores/user";

const userStore = useUserStore();
const users = ref<UserOut[]>([]);
const loading = ref(false);

async function load() {
  loading.value = true;
  try {
    users.value = await listUsers();
  } finally {
    loading.value = false;
  }
}

/** 启停开关: 先弹确认框(禁用是敏感操作), 确认后调接口, 失败则回滚开关状态 */
async function toggleStatus(user: UserOut) {
  const action = user.status ? "禁用" : "启用";
  try {
    await ElMessageBox.confirm(`确定要${action}用户 "${user.username}" 吗?`, "确认操作", {
      type: "warning",
    });
  } catch {
    load(); // 用户点了取消 → 重新拉数据, 让开关回到原状态
    return;
  }
  try {
    await updateUser(user.id, { status: !user.status });
    ElMessage.success(`已${action}`);
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail ?? "操作失败");
  }
  load(); // 无论成败都刷新列表(开关显示以数据库为准)
}

/** 角色调整: 下拉选择后直接提交 */
async function changeRole(user: UserOut, role: UserRole) {
  try {
    await updateUser(user.id, { role });
    ElMessage.success(`已将 ${user.username} 的角色改为 ${role}`);
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail ?? "操作失败");
  }
  load();
}

onMounted(load);
</script>

<template>
  <el-card>
    <template #header>
      <div class="header">
        <span>用户管理</span>
        <el-button :loading="loading" @click="load">刷新</el-button>
      </div>
    </template>

    <el-table :data="users" v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="username" label="用户名" min-width="120" />
      <el-table-column prop="real_name" label="姓名" width="120">
        <template #default="{ row }">{{ row.real_name ?? "-" }}</template>
      </el-table-column>

      <!-- 角色下拉: 当前登录用户自己的行禁用, 防止自降权限 -->
      <el-table-column label="角色" width="150">
        <template #default="{ row }">
          <el-select
            :model-value="row.role"
            :disabled="row.id === userStore.userInfo?.id"
            size="small"
            @change="(role: UserRole) => changeRole(row, role)"
          >
            <el-option label="质检员" value="inspector" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </template>
      </el-table-column>

      <!-- 启停开关: 自己的行禁用 -->
      <el-table-column label="状态" width="120">
        <template #default="{ row }">
          <el-switch
            :model-value="row.status"
            :disabled="row.id === userStore.userInfo?.id"
            active-text="启用"
            inactive-text="禁用"
            @change="() => toggleStatus(row)"
          />
        </template>
      </el-table-column>

      <el-table-column prop="created_at" label="注册时间" width="180" />
      <el-table-column label="最近登录" width="180">
        <template #default="{ row }">{{ row.last_login ?? "从未登录" }}</template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
