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
        :class="{ active: activeStatus === item.status }"
        role="button"
        tabindex="0"
        @click="toggleStatus(item.status)"
        @keydown.enter="toggleStatus(item.status)"
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
      <label class="filter-item">
        <span>当前状态</span>
        <select v-model="activeStatus">
          <option value="">全部状态</option>
          <option v-for="status in statuses" :key="status" :value="status">{{ status }}</option>
        </select>
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
          <td v-for="column in columns" :key="column">{{ row[column] ?? '—' }}</td>
          <td class="row-actions">
            <button
              v-for="action in actions"
              :key="action"
              class="link"
              type="button"
              :disabled="acting"
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
import { onMounted, ref } from 'vue'

import { fetchJson, request } from '@/api/client'

type Row = Record<string, string | number | null>
type StatItem = { label: string; status: string; value: number }
type ActionPayload = { ok: boolean; message?: string }

const ENDPOINT = '/api/costume'
const columns = ["服装编号", "服装名称", "角色归属", "尺码规格", "造型师", "使用场次", "当前状态", "清洗记录"]
const actions = ["安排定妆", "确认使用", "归还服装"]
const statuses = ["待定妆", "已定妆", "使用中", "已归还"]

const rows = ref<Row[]>([])
const total = ref(0)
const stats = ref<StatItem[]>([])
const activeStatus = ref('')
const acting = ref(false)
const errorMessage = ref('')
const filters = ref<Record<string, string>>({})
const filterFields = columns.slice(0, 1)

function resetFilters() {
  filters.value = {}
  activeStatus.value = ''
  void reload()
}

function toggleStatus(status: string) {
  activeStatus.value = activeStatus.value === status ? '' : status
  void reload()
}

function exportRows() {
  window.open(`${ENDPOINT}/export`, '_blank')
}

function openCreate() {
  errorMessage.value = '戏服登记入口尚未接入审批流'
}

async function runAction(action: string, row: Row) {
  if (acting.value) {
    return
  }
  acting.value = true
  errorMessage.value = ''
  try {
    const response = await request(`${ENDPOINT}/${row.id}/actions`, {
      method: 'POST',
      body: JSON.stringify({ action }),
    })
    const payload = (await response.json().catch(() => null)) as ActionPayload | null
    if (!response.ok || !payload?.ok) {
      throw new Error(payload?.message || '服装造型动作未生效，请稍后重试')
    }
    await Promise.all([reload(), reloadStats()])
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '服装造型操作失败'
  } finally {
    acting.value = false
  }
}

async function reload() {
  errorMessage.value = ''
  const query = new URLSearchParams()
  const keyword = (filters.value['服装编号'] ?? '').trim()
  if (keyword) {
    query.set('keyword', keyword)
  }
  if (activeStatus.value) {
    query.set('status', activeStatus.value)
  }
  try {
    const response = await request(`${ENDPOINT}?${query.toString()}`)
    if (!response.ok) {
      throw new Error('戏服列表读取失败')
    }
    const payload = await response.json()
    rows.value = payload.items ?? []
    total.value = payload.total ?? rows.value.length
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '服装造型列表读取失败'
  }
}

async function reloadStats() {
  try {
    const payload = await fetchJson<{ stats: StatItem[] }>(`${ENDPOINT}/stats`)
    stats.value = payload.stats ?? []
  } catch {
    stats.value = []
  }
}

onMounted(() => {
  void reload()
  void reloadStats()
})
</script>
