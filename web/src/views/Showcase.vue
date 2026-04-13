<template>
  <div class="showcase">
    <div class="card hero">
      <div class="avatar">SX</div>
      <h1>AI Inference Acceleration Engineer</h1>
      <div class="sub">Preparing for MetaX (沐曦) — {{ daysLeft }} days until start</div>
      <div class="streak-hero">🔥 {{ streak }} day streak</div>
    </div>

    <!-- Skill radar -->
    <div class="card">
      <h3>Core Competencies</h3>
      <div class="skill-grid">
        <div v-for="s in allSkills" :key="s.id" class="showcase-skill">
          <div class="skill-name">{{ s.name }}</div>
          <div class="skill-dots">
            <span v-for="i in s.max_level" :key="i" :class="['dot', i <= s.current_level ? 'filled' : '']"></span>
          </div>
          <span class="skill-tag" :class="s.jd_relevance">{{ s.jd_relevance }}</span>
        </div>
      </div>
    </div>

    <!-- Progress overview -->
    <div class="card">
      <h3>Learning Progress</h3>
      <div class="progress-overview">
        <div class="prog-item">
          <span class="prog-label">Current Day</span>
          <span class="prog-value">{{ currentDay }} / 84</span>
        </div>
        <div class="prog-item">
          <span class="prog-label">Phase</span>
          <span class="prog-value">{{ phaseName }}</span>
        </div>
        <div class="prog-item">
          <span class="prog-label">Tasks Completed</span>
          <span class="prog-value">{{ totalCompleted }}</span>
        </div>
        <div class="prog-item">
          <span class="prog-label">Quiz Accuracy</span>
          <span class="prog-value">{{ quizAccuracy }}</span>
        </div>
      </div>
    </div>

    <!-- GitHub Projects -->
    <div class="card">
      <h3>GitHub Projects Studied</h3>
      <div v-for="r in repos" :key="r.name" class="repo-row">
        <span class="repo-name">{{ r.name }}</span>
        <span class="repo-skills">{{ r.matched_skills?.map(s => s.name).join(', ') }}</span>
      </div>
      <div v-if="!repos.length" class="muted">Connect GitHub to show studied projects</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useProgressStore, useSkillStore } from '../stores/progress'
import axios from 'axios'

const api = axios.create({ baseURL: '/api' })
const store = useProgressStore()
const skillStore = useSkillStore()

const streak = computed(() => store.streak)
const currentDay = computed(() => store.currentDay)
const phaseName = computed(() => store.phaseName)
const totalCompleted = computed(() => store.progress?.total_completed || 0)
const daysLeft = computed(() => store.daysUntilJob ?? '?')

const allSkills = computed(() => {
  const s = skillStore.summary
  if (!s) return []
  return [...(s.must_have?.skills || []), ...(s.nice_to_have?.skills || [])]
})

const quizAccuracy = computed(() => {
  const history = store.progress?.quiz_history || []
  if (!history.length) return 'N/A'
  const ok = history.filter(h => h.confidence === 'understand').length
  return Math.round(ok / history.length * 100) + '%'
})

const repos = ref([])

onMounted(async () => {
  await store.fetchProgress()
  await store.fetchStreak()
  await skillStore.fetchSummary()
  try {
    const { data } = await api.get('/github/stars')
    repos.value = (data.repos || []).filter(r => r.matched_skills?.length).slice(0, 10)
  } catch { repos.value = [] }
})
</script>

<style scoped>
.hero { text-align: center; padding: 32px 20px; margin-bottom: 20px; }
.avatar { width: 64px; height: 64px; border-radius: 50%; background: linear-gradient(135deg, #3b82f6, #8b5cf6); display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: 700; margin: 0 auto 16px; }
h1 { font-size: 22px; margin-bottom: 4px; }
.sub { color: #94a3b8; font-size: 14px; }
.streak-hero { font-size: 20px; font-weight: 700; margin-top: 16px; color: #f97316; }
.skill-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; margin-top: 12px; }
.showcase-skill { display: flex; align-items: center; gap: 8px; padding: 8px 0; }
.skill-name { font-size: 13px; width: 120px; }
.skill-dots { display: flex; gap: 3px; }
.dot { width: 10px; height: 10px; border-radius: 50%; background: #334155; }
.dot.filled { background: #3b82f6; }
.skill-tag { font-size: 10px; padding: 1px 6px; border-radius: 3px; }
.skill-tag.must-have { background: #ef444420; color: #ef4444; }
.skill-tag.nice-to-have { background: #8b5cf620; color: #a78bfa; }
.progress-overview { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-top: 12px; }
.prog-item { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #334155; }
.prog-label { color: #94a3b8; font-size: 13px; }
.prog-value { font-weight: 600; font-size: 14px; }
.repo-row { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #334155; font-size: 13px; }
.repo-name { color: #3b82f6; }
.repo-skills { color: #94a3b8; }
.muted { color: #94a3b8; font-size: 14px; }
h3 { margin-bottom: 12px; font-size: 16px; }
.card { margin-bottom: 16px; }
</style>
