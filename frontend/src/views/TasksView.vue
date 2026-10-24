<!-- 任务管理: 全部任务列表 + 状态筛选, 点击行进详情. -->
<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { listTasks } from "../api/tasks";
import type { TaskOut, TaskStatus } from "../api/types";
import { useUserStore } from "../stores/user";

const router = useRouter();
const userStore = useUserStore();

const tasks = ref<TaskOut[]>([]);   // 后端返回的全部任务
const loading = ref(false);
const statusFilter = ref<TaskStatus | "">(""); // 选中的筛选状态("" = 全部)

// computed: 筛选是前端本地过滤(数据量小), tasks 变化时自动重算
const filtered = computed(() =>
  statusFilter.value ? tasks.value.filter((t) => t.status === statusFilter.value) : tasks.value
);

async function load() {
  loading.value = true;
  try {
    tasks.value = await listTasks();
  } finally {
    loading.value = false;
  }
}

// el-table 的状态列: 不同状态显示不同颜色的标签
const statusTag: Record<TaskStatus, { label: string; type: "info" | "warning" | "success" | "danger" }> = {
  pending: { label: "排队中", type: "info" },
  running: { label: "检测中", type: "warning" },
  completed: { label: "已完成", type: "success" },
  failed: { label: "失败", type: "danger" },
};

onMounted(load);
</script>

<template>
  <el-card>
    <div class="toolbar">
      <el-select v-model="statusFilter" placeholder="按状态筛选" clearable style="width: 160px">
        <el-option label="排队中" value="pending" />
        <el-option label="检测中" value="running" />
        <el-option label="已完成" value="completed" />
        <el-option label="失败" value="failed" />
      </el-select>
      <el-button :loading="loading" @click="load">刷新</el-button>
    </div>

    <el-table :data="filtered" v-loading="loading" @row-click="(row: TaskOut) => router.push(`/tasks/${row.task_no}`)">
      <el-table-column prop="task_no" label="任务号" width="220" />
      <el-table-column prop="task_name" label="任务名称" min-width="160" />
      <!-- 检测人列: 仅 admin 显示(inspector 只看得到自己的任务, 该列无意义) -->
      <el-table-column v-if="userStore.isAdmin" label="检测人" width="110">
        <template #default="{ row }">
          <!-- 自己创建的任务用醒目的 me 标签, 他人显示用户名 -->
          <el-tag v-if="row.username === userStore.userInfo?.username" type="warning" size="small">me</el-tag>
          <span v-else>{{ row.username ?? "-" }}</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusTag[row.status as TaskStatus].type">
            {{ statusTag[row.status as TaskStatus].label }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="进度" width="120">
        <template #default="{ row }">{{ row.completed_images }} / {{ row.total_images }}</template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180" />
      <el-table-column label="操作" width="100">
        <template #default="{ row }">
          <el-button link type="primary" @click.stop="router.push(`/tasks/${row.task_no}`)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
}
/* 行可点击的视觉暗示 */
.el-table :deep(tbody tr) {
  cursor: pointer;
}
</style>
