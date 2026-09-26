<template>
  <section class="page">
    <header class="page-head">
      <div>
        <h2>运营概览</h2>
        <p class="page-desc">汇总各业务模块的关键指标，先看总量再看异常。</p>
      </div>
    </header>
    <div class="stat-row">
      <article v-for="card in cards" :key="card.label" class="stat-card">
        <span class="stat-label">{{ card.label }}</span>
        <strong class="stat-value">{{ card.value }}</strong>
      </article>
    </div>
    <table class="data-table">
      <thead>
        <tr><th>业务模块</th><th>今日新增</th><th>待处理</th><th>异常量</th></tr>
      </thead>
      <tbody>
        <tr
          v-for="row in moduleRows"
          :key="row.name"
          class="module-row"
          @click="openModule(row.name)"
        >
          <td>{{ moduleLabel(row.name) }}</td>
          <td>{{ row.created }}</td>
          <td>{{ row.pending }}</td>
          <td>{{ row.abnormal }}</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { fetchJson } from '@/api/client'

type Overview = {
  cards: { label: string; value: number }[]
  modules: { name: string; created: number; pending: number; abnormal: number }[]
}

// 概览接口返回的是模块英文键，这里补一层中文名与跳转路径的映射
const MODULE_META: Record<string, { label: string; path: string }> = {
  script: { label: '剧本管理', path: '/script' },
  scene: { label: '分场大纲', path: '/scene' },
  casting: { label: '角色选角', path: '/casting' },
  crew: { label: '剧组人员', path: '/crew' },
  notice: { label: '拍摄通告', path: '/notice' },
  location: { label: '场地租用', path: '/location' },
  prop: { label: '道具管理', path: '/prop' },
  costume: { label: '服装造型', path: '/costume' },
  makeup: { label: '化妆造型', path: '/makeup' },
  equipment: { label: '器材管理', path: '/equipment' },
  shooting: { label: '拍摄进度', path: '/shooting' },
  footage: { label: '素材管理', path: '/footage' },
  edit: { label: '后期剪辑', path: '/edit' },
  vfx: { label: '特效制作', path: '/vfx' },
  review: { label: '审片意见', path: '/review' },
  budget: { label: '预算科目', path: '/budget' },
  expense: { label: '费用报销', path: '/expense' },
  schedule: { label: '档期协调', path: '/schedule' },
  permit: { label: '外景许可', path: '/permit' },
  wrap: { label: '杀青结算', path: '/wrap' },
}

const router = useRouter()
const cards = ref<Overview['cards']>([])
const moduleRows = ref<Overview['modules']>([])

function moduleLabel(name: string): string {
  return MODULE_META[name]?.label ?? name
}

function openModule(name: string) {
  const path = MODULE_META[name]?.path
  if (path) {
    void router.push(path)
  }
}

onMounted(async () => {
  try {
    const payload = await fetchJson<Overview>('/api/overview')
    cards.value = payload.cards
    moduleRows.value = payload.modules
  } catch {
    cards.value = [{"label": "业务模块", "value": 0}, {"label": "今日新增", "value": 0}]
    moduleRows.value = [{"name": "剧本管理", "created": 0, "pending": 0, "abnormal": 0}, {"name": "分场大纲", "created": 0, "pending": 0, "abnormal": 0}, {"name": "角色选角", "created": 0, "pending": 0, "abnormal": 0}, {"name": "剧组人员", "created": 0, "pending": 0, "abnormal": 0}, {"name": "拍摄通告", "created": 0, "pending": 0, "abnormal": 0}, {"name": "场地租用", "created": 0, "pending": 0, "abnormal": 0}, {"name": "道具管理", "created": 0, "pending": 0, "abnormal": 0}, {"name": "服装造型", "created": 0, "pending": 0, "abnormal": 0}, {"name": "化妆造型", "created": 0, "pending": 0, "abnormal": 0}, {"name": "器材管理", "created": 0, "pending": 0, "abnormal": 0}, {"name": "拍摄进度", "created": 0, "pending": 0, "abnormal": 0}, {"name": "素材管理", "created": 0, "pending": 0, "abnormal": 0}, {"name": "后期剪辑", "created": 0, "pending": 0, "abnormal": 0}, {"name": "特效制作", "created": 0, "pending": 0, "abnormal": 0}, {"name": "审片意见", "created": 0, "pending": 0, "abnormal": 0}, {"name": "预算科目", "created": 0, "pending": 0, "abnormal": 0}, {"name": "费用报销", "created": 0, "pending": 0, "abnormal": 0}, {"name": "档期协调", "created": 0, "pending": 0, "abnormal": 0}, {"name": "外景许可", "created": 0, "pending": 0, "abnormal": 0}, {"name": "杀青结算", "created": 0, "pending": 0, "abnormal": 0}]
  }
})
</script>

<style scoped>
.module-row { cursor: pointer; }
.module-row:hover { background: #f1f5f9; }
</style>
