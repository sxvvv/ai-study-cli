<template>
  <div class="streak">
    <h1>Streak</h1>

    <!-- Current streak -->
    <div class="card streak-hero">
      <div class="streak-number">🔥 {{ streak }}</div>
      <div class="streak-label">当前连续天数</div>
      <div class="streak-meta">
        <span>最长: {{ maxStreak }}天</span>
        <span>今日层级: {{ layerLabel }}</span>
        <span :class="['micro-badge', microDone ? 'done' : '']">
          今日Micro: {{ microDone ? '✅' : '❌' }}
        </span>
      </div>
      <div class="streak-actions" v-if="!microDone">
        <router-link to="/quiz" class="btn btn-primary">做Quiz维持连胜</router-link>
        <router-link to="/flashcards" class="btn btn-primary">复习闪卡</router-link>
      </div>
    </div>

    <!-- Heat map -->
    <div class="card">
      <h3>学习日历 (近30天)</h3>
      <div class="heatmap">
        <div
          v-for="(d, i) in heatmapDays"
          :key="i"
          :class="['heat-cell', d.level]"
          :title="d.date"
        ></div>
      </div>
      <div class="heatmap-legend">
        <span class="heat-cell empty"></span> 无
        <span class="heat-cell micro"></span> Micro
        <span class="heat-cell plan"></span> Plan
        <span class="heat-cell demo"></span> Demo
      </div>
    </div>

    <!-- History -->
    <div class="card">
      <h3>学习记录 (近7天)</h3>
      <div v-for="(log, date) in recentLogs" :key="date" class="log-row">
        <span class="log-date">{{ date }}</span>
        <span class="log-completed">✅ {{ log.completed?.length || 0 }}</span>
        <span v-if="log.plan_achieved" class="log-badge plan">Plan</span>
        <span v-if="log.demo_achieved" class="log-badge demo">Demo</span>
        <span v-if="log.micro_achieved" class="log-badge micro">Micro</span>
      </div>
      <div v-if="!Object.keys(recentLogs).length" class="muted">暂无记录</div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useProgressStore } from '../stores/progress'

const store = useProgressStore()
const streak = computed(() => store.streak)
const maxStreak = computed(() => store.progress?.max_streak || 0)
const streakLayer = computed(() => store.streakLayer)
const microDone = ref(false)

const layerLabels = { micro: '最低门槛 ✅', plan: '计划完成 🏆', demo: '技能验证 🎯', none: '未完成' }
const layerLabel = computed(() => layerLabels[streakLayer.value] || '未完成')

const recentLogs = computed(() => {
  const logs = store.progress?.daily_logs || {}
  const sorted = Object.keys(logs).sort().reverse().slice(0, 7)
  const result = {}
  for (const d of sorted) result[d] = logs[d]
  return result
})

const heatmapDays = computed(() => {
  const logs = store.progress?.daily_logs || {}
  const days = []
  const today = new Date()
  for (let i = 29; i >= 0; i--) {
    const d = new Date(today)
    d.setDate(d.getDate() - i)
    const key = d.toISOString().slice(0, 10)
    const log = logs[key]
    let level = 'empty'
    if (log) {
      if (log.demo_achieved) level = 'demo'
      else if (log.plan_achieved) level = 'plan'
      else if (log.micro_achieved || log.completed?.length) level = 'micro'
    }
    days.push({ date: key, level })
  }
  return days
})

onMounted(async () => {
  await store.fetchStreak()
  await store.fetchProgress()
  const { data } = await (await import('axios')).default.get('/api/streak')
  microDone.value = data.micro_achieved_today
})
</script>

<style scoped>
.streak-hero { text-align: center; padding: 32px 20px; margin-bottom: 20px; }
.streak-number { font-size: 56px; font-weight: 800; background: linear-gradient(135deg, #f97316, #ef4444); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.streak-label { font-size: 16px; color: #94a3b8; margin-top: 4px; }
.streak-meta { display: flex; justify-content: center; gap: 20px; margin-top: 16px; font-size: 13px; color: #94a3b8; }
.micro-badge.done { color: #22c55e; }
.streak-actions { display: flex; justify-content: center; gap: 12px; margin-top: 20px; }
.streak-actions .btn { text-decoration: none; }
.heatmap { display: grid; grid-template-columns: repeat(15, 1fr); gap: 4px; margin: 16px 0; }
.heat-cell { width: 100%; aspect-ratio: 1; border-radius: 4px; min-width: 16px; min-height: 16px; }
.heat-cell.empty { background: #1e293b; }
.heat-cell.micro { background: #3b82f6; }
.heat-cell.plan { background: #22c55e; }
.heat-cell.demo { background: #f97316; }
.heatmap-legend { display: flex; align-items: center; gap: 8px; font-size: 12px; color: #94a3b8; }
.heatmap-legend .heat-cell { width: 14px; height: 14px; min-width: 14px; min-height: 14px; }
.log-row { display: flex; align-items: center; gap: 12px; padding: 8px 0; border-bottom: 1px solid #334155; font-size: 14px; }
.log-row:last-child { border-bottom: none; }
.log-date { color: #94a3b8; width: 100px; }
.log-completed { flex: 1; }
.log-badge { font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: 600; }
.log-badge.micro { background: #3b82f620; color: #3b82f6; }
.log-badge.plan { background: #22c55e20; color: #22c55e; }
.log-badge.demo { background: #f9731620; color: #f97316; }
.muted { color: #94a3b8; font-size: 14px; }
h1 { margin-bottom: 20px; }
h3 { margin-bottom: 12px; font-size: 16px; }
.card { margin-bottom: 16px; }
</style>
