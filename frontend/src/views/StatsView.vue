<!-- 统计看板: 筛选栏(任务/类别) + 4 张汇总卡片 + 类别分布饼图 + 近14天趋势折线图(ECharts). -->
<script setup lang="ts">
import * as echarts from "echarts"; // 直接引完整包(学习项目够用; 生产可按需引入减体积)
import { onMounted, onUnmounted, ref, watch } from "vue";
import { getOverview } from "../api/stats";
import { listTasks } from "../api/tasks";
import type { ClassDistributionItem, StatsOverview, TaskOut } from "../api/types";

const data = ref<StatsOverview | null>(null);
const pieRef = ref<HTMLDivElement>();   // 饼图的 DOM 容器(ref 绑到 <div ref="pieRef">)
const lineRef = ref<HTMLDivElement>();  // 折线图容器

// ===== 筛选状态 =====
const taskOptions = ref<TaskOut[]>([]);               // 任务下拉的选项
const classOptions = ref<ClassDistributionItem[]>([]); // 类别下拉的选项(取自首次无筛选结果)
const filterTask = ref("");   // 选中的任务号("" = 全部)
const filterClass = ref("");  // 选中的类别名("" = 全部)

// ECharts 实例要在组件卸载时 dispose(释放 canvas 资源), 所以提出到外层
let pieChart: echarts.ECharts | null = null;
let lineChart: echarts.ECharts | null = null;

/** 拉取看板数据(带当前筛选), 并渲染图表.
 *  有筛选也重渲染: setOption 会智能合并/更新, 不需要重建实例. */
async function load() {
  const params: Record<string, string> = {};
  if (filterTask.value) params.task_no = filterTask.value;
  if (filterClass.value) params.class_name = filterClass.value;

  data.value = await getOverview(params);
  renderCharts(data.value);

  // 无筛选的那次请求, 结果里类别最全 —— 记下来当类别下拉的选项
  if (!filterTask.value && !filterClass.value) {
    classOptions.value = data.value.class_distribution;
  }
}

// 筛选变化 → 重新拉数据(watch 监听两个下拉)
watch([filterTask, filterClass], () => {
  load().catch(() => {});
});

function resetFilters() {
  filterTask.value = "";
  filterClass.value = "";
}

function renderCharts(d: StatsOverview) {
  // ===== 饼图: 类别分布 =====
  if (!pieChart && pieRef.value) pieChart = echarts.init(pieRef.value);
  pieChart?.setOption({
    title: { text: "缺陷类别分布", left: "center" },
    tooltip: { trigger: "item" },           // 鼠标悬浮显示数值
    legend: { orient: "vertical", left: "left" },
    series: [
      {
        type: "pie",
        radius: ["40%", "70%"],             // 环形饼图(内外半径)
        // 后端给了展示名和颜色, 直接映射成 ECharts 需要的 {name, value}
        data: d.class_distribution.map((c) => ({
          name: c.display_name,
          value: c.count,
          itemStyle: c.color ? { color: c.color } : undefined,
        })),
      },
    ],
  });

  // ===== 折线图: 近14天任务/图片趋势 =====
  if (!lineChart && lineRef.value) lineChart = echarts.init(lineRef.value);
  lineChart?.setOption({
    title: { text: "近 14 天趋势", left: "center" },
    tooltip: { trigger: "axis" },           // 按竖轴对齐提示
    legend: { data: ["任务数", "图片数"], top: 30 },
    xAxis: { type: "category", data: d.trend.map((t) => t.date.slice(5)) }, // 只显示月-日
    yAxis: { type: "value", minInterval: 1 }, // minInterval=1: 纵轴只显示整数
    series: [
      { name: "任务数", type: "line", data: d.trend.map((t) => t.tasks), smooth: true },
      { name: "图片数", type: "line", data: d.trend.map((t) => t.images), smooth: true },
    ],
  });
}

// 窗口尺寸变化时让图表自适应重绘
function handleResize() {
  pieChart?.resize();
  lineChart?.resize();
}

onMounted(async () => {
  taskOptions.value = await listTasks(); // 任务下拉选项(admin 全部 / inspector 自己的)
  await load();
  window.addEventListener("resize", handleResize);
});

// 组件卸载: 移除监听 + 释放图表实例(与 worker 里 finally 关会话同理, 资源要还)
onUnmounted(() => {
  window.removeEventListener("resize", handleResize);
  pieChart?.dispose();
  lineChart?.dispose();
});
</script>

<template>
  <!-- 筛选栏 -->
  <el-card class="mb">
    <div class="filters">
      <el-select
        v-model="filterTask"
        clearable
        filterable
        placeholder="全部任务"
        style="width: 280px"
      >
        <el-option
          v-for="t in taskOptions"
          :key="t.task_no"
          :label="`${t.task_name} (${t.task_no})`"
          :value="t.task_no"
        />
      </el-select>

      <el-select
        v-model="filterClass"
        clearable
        placeholder="全部类别"
        style="width: 180px"
      >
        <el-option
          v-for="c in classOptions"
          :key="c.class_name"
          :label="c.display_name"
          :value="c.class_name"
        />
      </el-select>

      <el-button @click="resetFilters">重置</el-button>
      <span class="hint">筛选后, 下方所有卡片和图表都会联动更新</span>
    </div>
  </el-card>

  <!-- 汇总卡片: 4 个指标一行排开 -->
  <el-row :gutter="16" class="mb">
    <el-col :span="6">
      <el-card><el-statistic title="任务总数" :value="data?.total_tasks ?? 0" /></el-card>
    </el-col>
    <el-col :span="6">
      <el-card><el-statistic title="图片总数" :value="data?.total_images ?? 0" /></el-card>
    </el-col>
    <el-col :span="6">
      <el-card><el-statistic title="检出目标总数" :value="data?.total_detections ?? 0" /></el-card>
    </el-col>
    <el-col :span="6">
      <el-card>
        <el-statistic title="平均推理耗时(ms)" :value="data?.avg_inference_ms ?? 0" />
      </el-card>
    </el-col>
  </el-row>

  <!-- 两个图表各占一半 -->
  <el-row :gutter="16">
    <el-col :span="12"><el-card><div ref="pieRef" class="chart" /></el-card></el-col>
    <el-col :span="12"><el-card><div ref="lineRef" class="chart" /></el-card></el-col>
  </el-row>
</template>

<style scoped>
.mb { margin-bottom: 16px; }
.chart { height: 360px; }
.filters {
  display: flex;
  gap: 12px;
  align-items: center;
}
.hint { color: #999; font-size: 12px; }
</style>
