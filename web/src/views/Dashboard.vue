<template>
  <div class="dashboard">
    <h1>Dashboard</h1>

    <!-- Stats Row -->
    <div class="stats-row">
      <div class="card stat">
        <div class="stat-label">Current Day</div>
        <div class="stat-value">{{ currentDay }} / 84</div>
        <div class="stat-sub">{{ phaseName }}</div>
      </div>
      <div class="card stat">
        <div class="stat-label">Streak</div>
        <div class="stat-value">🔥 {{ streak }}</div>
        <div class="stat-sub">Max: {{ progress?.max_streak || 0 }}</div>
      </div>
      <div class="card stat">
        <div class="stat-label">Days Until Job</div>
        <div class="stat-value">{{ daysUntilJob ?? '—' }}</div>
        <div class="stat-sub">{{ daysUntilJob ? 'days left' : 'not set' }}</div>
      </div>
    </div>

    <!-- Phase Progress -->
    <div class="card" v-if="phaseInfo">
      <h3>Phase {{ phaseInfo.phase_id }}: {{ phaseName }}</h3>
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: phaseProgress + '%' }"></div>
      </div>
      <div class="progress-text">Day {{ phaseInfo.day_in_phase }} / {{ phaseInfo.total_in_phase }} ({{ phaseProgress }}%)</div>
    </div>

    <!-- Today's Tasks -->
    <div class="card">
      <h3>Today's Tasks</h3>
      <div v-if="loading" class="muted">Loading...</div>
      <div v-else-if="!tasks.length" class="muted">No tasks for today</div>
      <div v-else>
        <div v-for="task in tasks" :key="task.id" class="task-item">
          <span :class="['task-status', task.done ? 'done' : '']">{{ task.done ? '✅' : '⬜' }}</span>
          <span class="task-text">{{ task.id }}: {{ task.title || task.description || task.id }}</span>
          <div class="task-actions" v-if="!task.done">
            <button class="btn btn-success btn-sm" @click="handleDone(task.id)">Done</button>
            <button class="btn btn-danger btn-sm" @click="handleSkip(task.id)">Skip</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useProgressStore } from '../stores/progress'
import axios from 'axios'

const api = axios.create({ baseURL: '/api' })
const store = useProgressStore()
const tasks = ref([])
const loading = ref(false)

const currentDay = computed(() => store.currentDay)
const phaseInfo = computed(() => store.phaseInfo)
const phaseName = computed(() => store.phaseName)
const phaseProgress = computed(() => store.phaseProgress)
const streak = computed(() => store.streak)
const progress = computed(() => store.progress)
const daysUntilJob = computed(() => store.daysUntilJob)

onMounted(async () => {
  loading.value = true
  try {
    const { data } = await api.get('/daily-tasks')
    const raw = data.tasks || ''
    const completed = store.progress?.completed_tasks || []
    // Parse tasks from text output
    const lines = raw.split('\n').filter(l => l.trim())
    tasks.value = lines.map(l => ({
      id: l.trim(),
      title: l.replace(/^[#\s]+/, ''),
      done: completed.some(c => l.includes(c)),
    }))
  } catch {
    tasks.value = []
  } finally {
    loading.value = false
  }
})

async function handleDone(taskId) {
  await store.markDone(taskId)
  tasks.value = tasks.value.map(t => t.id === taskId ? { ...t, done: true } : t)
}

async function handleSkip(taskId) {
  await store.markSkip(taskId)
  tasks.value = tasks.value.filter(t => t.id !== taskId)
}
</script>

<style scoped>
.stats-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 20px; }
.stat { text-align: center; }
.stat-label { font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
.stat-value { font-size: 28px; font-weight: 700; }
.stat-sub { font-size: 12px; color: #94a3b8; margin-top: 4px; }
.progress-bar { background: #334155; border-radius: 8px; height: 12px; overflow: hidden; margin: 12px 0; }
.progress-fill { height: 100%; background: linear-gradient(90deg, #3b82f6, #22c55e); border-radius: 8px; transition: width .3s; }
.progress-text { font-size: 13px; color: #94a3b8; }
.task-item { display: flex; align-items: center; gap: 12px; padding: 10px 0; border-bottom: 1px solid #334155; }
.task-item:last-child { border-bottom: none; }
.task-status.done { opacity: .6; }
.task-text { flex: 1; font-size: 14px; }
.task-actions { display: flex; gap: 6px; }
.btn-sm { padding: 4px 10px; font-size: 12px; }
.muted { color: #94a3b8; font-size: 14px; }
h1 { margin-bottom: 20px; }
h3 { margin-bottom: 12px; font-size: 16px; }
.card { margin-bottom: 16px; }
</style>
