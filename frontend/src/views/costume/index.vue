<template>
  <section class="page" data-module="costume">
    <header class="page-head">
      <div>
        <h2>服装造型管理</h2>
        <p class="page-desc">维护戏服，围绕服装编号、服装名称、角色归属、尺码规格做登记、筛选与状态流转。</p>
      </div>
      <div class="page-actions">
        <button class="btn primary" type="button" @click="openCreate">登记戏服</button>
        <button class="btn" type="button" @click="exportRows">导出服装造型清单</button>
      </div>
    </header>

    <div class="stat-row">
      <article
        v-for="item in stats"
        :key="item.label"
        class="stat-card clickable"
        :class="{ active: filters.status === item.status }"
        role="button"
        tabindex="0"
        @click="filterByStatus(item.status)"
        @keyup.enter="filterByStatus(item.status)"
      >
        <span class="stat-label">{{ item.label }}</span>
        <strong class="stat-value">{{ item.value }}</strong>
      </article>
    </div>

    <form class="filter-bar" @submit.prevent="reload">
      <label v-for="field in filterFields" :key="field" class="filter-item">
        <span>{{ field }}</span>
        <input v-model="filters[field]" :placeholder="`按${field}检索`" />
      </label>
      <button class="btn" type="submit">查询</button>
      <button class="btn ghost" type="button" @click="resetFilters">重置条件</button>
    </form>

    <table class="data-table">
      <thead>
        <tr>
          <th v-for="column in columns" :key="column">{{ column }}</th>
          <th>可执行动作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="String(row.id)">
          <td v-for="column in columns" :key="column">{{ displayValue(row, column) }}</td>
          <td class="row-actions">
            <button
              v-for="action in actions"
              :key="action"
              class="link"
              type="button"
              :disabled="busyId === String(row.id) || !canRun(action, row)"
              @click="runAction(action, row)"
            >
              {{ action }}
            </button>
          </td>
        </tr>
        <tr v-if="!rows.length">
          <td :colspan="columns.length + 1" class="empty-state">暂无服装造型数据，可先登记戏服</td>
        </tr>
      </tbody>
    </table>

    <footer class="page-foot">
      <span>共 {{ total }} 条服装造型记录</span>
      <span v-if="errorMessage" class="error-text">{{ errorMessage }}</span>
    </footer>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { request } from '@/api/client'

type Row = Record<string, string | number | null>

const ENDPOINT = '/api/costume'
const columns = ["服装编号", "服装名称", "角色归属", "尺码规格", "造型师", "使用场次", "当前状态", "清洗记录"]
const actions = ["安排定妆", "确认使用", "归还服装"]
const statuses = ["待定妆", "已定妆", "使用中", "已归还"]
// 动作只允许在指定状态下发起，与后端流转规则保持一致，避免重复归还
const actionSources: Record<string, string[]> = {
  "安排定妆": ["待定妆"],
  "确认使用": ["已定妆"],
  "归还服装": ["使用中"],
}
const statCards = [
  { label: "待定妆服装", status: "待定妆" },
  { label: "使用中服装", status: "使用中" },
  { label: "待清洗服装", status: "已归还" },
]

const rows = ref<Row[]>([])
const total = ref(0)
const errorMessage = ref('')
const filters = ref<Record<string, string>>({})
const filterFields = columns.slice(0, 3)
const busyId = ref<string | null>(null)
// 各状态全量计数，驱动顶部统计卡；不随筛选条件变化
const statusCounts = ref<Record<string, number>>({})

const stats = computed(() =>
  statCards.map((card) => ({
    ...card,
    value: statusCounts.value[card.status] ?? 0,
  })),
)

function displayValue(row: Row, column: string): string | number | null {
  if (column === "当前状态") {
    return row["当前状态"] ?? row.status ?? '—'
  }
  const value = row[column]
  return value === '' || value === null || value === undefined ? '—' : value
}

function rowStatus(row: Row): string {
  return String(row.status ?? row["当前状态"] ?? '')
}

function canRun(action: string, row: Row): boolean {
  return actionSources[action]?.includes(rowStatus(row)) ?? false
}

function filterByStatus(status: string) {
  if (filters.value.status === status) {
    delete filters.value.status
  } else {
    filters.value.status = status
  }
  void reload()
}

function resetFilters() {
  filters.value = {}
  void reload()
}

function exportRows() {
  window.open(`${ENDPOINT}/export`, '_blank')
}

function openCreate() {
  errorMessage.value = '戏服登记入口尚未接入审批流'
}

async function runAction(action: string, row: Row) {
  if (busyId.value !== null || !canRun(action, row)) {
    return
  }
  errorMessage.value = ''
  busyId.value = String(row.id)
  try {
    const response = await request(`${ENDPOINT}/${row.id}/actions`, {
      method: 'POST',
      body: JSON.stringify({ action }),
    })
    if (!response.ok) {
      throw new Error('服装造型动作未生效，请稍后重试')
    }
    const payload = await response.json()
    // 业务失败（如重复归还）同样是 HTTP 200，需按 ok 字段提示，不能当成已生效
    if (!payload.ok) {
      throw new Error(payload.message || '服装造型动作未生效')
    }
    await reload()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '服装造型操作失败'
  } finally {
    busyId.value = null
  }
}

async function reload() {
  errorMessage.value = ''
  const query = new URLSearchParams(filters.value as Record<string, string>).toString()
  try {
    const response = await request(`${ENDPOINT}?${query}`)
    if (!response.ok) {
      throw new Error('戏服列表读取失败')
    }
    const payload = await response.json()
    rows.value = payload.items ?? []
    total.value = payload.total ?? rows.value.length
    await reloadStats()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '服装造型列表读取失败'
  }
}

async function reloadStats() {
  const counts: Record<string, number> = {}
  await Promise.all(
    statCards.map(async (card) => {
      const response = await request(`${ENDPOINT}?status=${encodeURIComponent(card.status)}&size=1`)
      if (response.ok) {
        const payload = await response.json()
        counts[card.status] = payload.total ?? 0
      }
    }),
  )
  statusCounts.value = counts
}

onMounted(reload)
</script>
