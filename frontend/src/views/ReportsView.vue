<!-- 报告中心: 任务列表 + 一键下载 Word 检测报告(仅已结束的任务可导出). -->
<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { downloadReport, listTasks } from "../api/tasks";
import type { TaskOut } from "../api/types";
import { useUserStore } from "../stores/user";

const userStore = useUserStore();

const tasks = ref<TaskOut[]>([]);
const loading = ref(false);
const exportingNo = ref(""); // 正在导出的任务号(按钮转圈用)

async function load() {
  loading.value = true;
  try {
    tasks.value = await listTasks();
  } finally {
    loading.value = false;
  }
}

/** 下载当前任务的检测报告(与任务详情页的导出按钮同一套逻辑) */
async function download(task: TaskOut) {
  exportingNo.value = task.task_no;
  try {
    const blob = await downloadReport(task.task_no);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${task.task_no}.docx`;
    a.click();
    URL.revokeObjectURL(url);
    ElMessage.success("报告已下载");
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail ?? "导出失败");
  } finally {
    exportingNo.value = "";
  }
}

onMounted(load);
</script>

<template>
  <el-card>
    <template #header>
      <div class="header">
        <span>检测报告</span>
        <el-button :loading="loading" @click="load">刷新</el-button>
      </div>
    </template>

    <el-table :data="tasks" v-loading="loading">
      <el-table-column prop="task_no" label="任务号" width="220" />
      <el-table-column prop="task_name" label="任务名称" min-width="160" />
      <!-- 检测人列: 仅 admin 显示(inspector 只有自己的任务, 该列无意义) -->
      <el-table-column v-if="userStore.isAdmin" label="检测人" width="110">
        <template #default="{ row }">
          <el-tag v-if="row.username === userStore.userInfo?.username" type="warning" size="small">me</el-tag>
          <span v-else>{{ row.username ?? "-" }}</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'completed' ? 'success' : row.status === 'failed' ? 'danger' : 'info'">
            {{ row.status === "completed" ? "已完成" : row.status === "failed" ? "失败" : row.status === "running" ? "检测中" : "排队中" }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <!-- 只有已结束的任务才能导出(对齐后端校验) -->
          <el-button
            v-if="row.status === 'completed' || row.status === 'failed'"
            type="primary"
            size="small"
            :loading="exportingNo === row.task_no"
            @click="download(row)"
          >
            下载报告
          </el-button>
          <span v-else class="hint">任务结束后可导出</span>
        </template>
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
.hint { color: #999; font-size: 12px; }
</style>
