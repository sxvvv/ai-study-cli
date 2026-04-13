<template>
  <div class="skills">
    <h1>Skill Map</h1>
    <div class="sub">MetaX (沐曦) — AI Inference Acceleration Engineer</div>

    <div v-if="loading" class="muted">Loading...</div>

    <template v-else>
      <!-- Must-Have -->
      <div class="card" v-if="summary?.must_have">
        <h3>Must-Have Skills ({{ summary.must_have.percentage }}%)</h3>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: summary.must_have.percentage + '%' }"></div>
        </div>
        <div class="skill-list">
          <div v-for="s in summary.must_have.skills" :key="s.id" class="skill-row">
            <span class="skill-name">{{ s.name }}</span>
            <div class="skill-bar-wrap">
              <div class="skill-bar" :style="{ width: (s.current_level / s.max_level * 100) + '%' }"></div>
            </div>
            <span class="skill-level">{{ s.current_level }}/{{ s.max_level }}</span>
            <div class="skill-actions">
              <button v-for="lv in s.max_level" :key="lv" class="lvl-btn" :class="{ active: lv <= s.current_level }" @click="setLevel(s.id, lv)">{{ lv }}</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Nice-to-Have -->
      <div class="card" v-if="summary?.nice_to_have">
        <h3>Nice-to-Have Skills ({{ summary.nice_to_have.percentage }}%)</h3>
        <div class="progress-bar">
          <div class="progress-fill secondary" :style="{ width: summary.nice_to_have.percentage + '%' }"></div>
        </div>
        <div class="skill-list">
          <div v-for="s in summary.nice_to_have.skills" :key="s.id" class="skill-row">
            <span class="skill-name">{{ s.name }}</span>
            <div class="skill-bar-wrap">
              <div class="skill-bar secondary" :style="{ width: (s.current_level / s.max_level * 100) + '%' }"></div>
            </div>
            <span class="skill-level">{{ s.current_level }}/{{ s.max_level }}</span>
            <div class="skill-actions">
              <button v-for="lv in s.max_level" :key="lv" class="lvl-btn" :class="{ active: lv <= s.current_level }" @click="setLevel(s.id, lv)">{{ lv }}</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Gaps -->
      <div class="card" v-if="gaps.length">
        <h3>Top Gaps</h3>
        <div class="gap-list">
          <div v-for="g in gaps.slice(0, 10)" :key="g.id" class="gap-row">
            <span :class="['gap-tag', g.jd_relevance === 'must-have' ? 'must' : 'nice']">{{ g.jd_relevance === 'must-have' ? 'Must' : 'Nice' }}</span>
            <span class="gap-name">{{ g.name }}</span>
            <span class="gap-delta">-{{ g.gap }} levels ({{ g.current_level }}/{{ g.max_level }})</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useSkillStore } from '../stores/progress'

const store = useSkillStore()
const { summary, gaps, loading } = store

onMounted(() => {
  store.fetchSummary()
  store.fetchGaps()
})

async function setLevel(skillId, level) {
  await store.updateLevel(skillId, level)
}
</script>

<style scoped>
.sub { color: #94a3b8; font-size: 14px; margin-bottom: 20px; }
.progress-bar { background: #334155; border-radius: 8px; height: 10px; overflow: hidden; margin: 8px 0 16px; }
.progress-fill { height: 100%; background: linear-gradient(90deg, #3b82f6, #22c55e); border-radius: 8px; transition: width .3s; }
.progress-fill.secondary { background: linear-gradient(90deg, #8b5cf6, #a78bfa); }
.skill-row, .gap-row { display: flex; align-items: center; gap: 12px; padding: 8px 0; border-bottom: 1px solid #334155; }
.skill-row:last-child, .gap-row:last-child { border-bottom: none; }
.skill-name { width: 160px; font-size: 14px; flex-shrink: 0; }
.skill-bar-wrap { flex: 1; background: #334155; border-radius: 6px; height: 8px; overflow: hidden; }
.skill-bar { height: 100%; background: #3b82f6; border-radius: 6px; transition: width .3s; }
.skill-bar.secondary { background: #8b5cf6; }
.skill-level { font-size: 13px; color: #94a3b8; width: 40px; text-align: right; }
.skill-actions { display: flex; gap: 2px; }
.lvl-btn { width: 24px; height: 24px; border-radius: 4px; border: 1px solid #475569; background: transparent; color: #94a3b8; font-size: 11px; cursor: pointer; transition: all .15s; }
.lvl-btn.active { background: #3b82f6; border-color: #3b82f6; color: #fff; }
.lvl-btn:hover { border-color: #3b82f6; }
.gap-tag { font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: 600; }
.gap-tag.must { background: #ef444420; color: #ef4444; }
.gap-tag.nice { background: #8b5cf620; color: #a78bfa; }
.gap-name { flex: 1; font-size: 14px; }
.gap-delta { font-size: 13px; color: #f97316; }
.muted { color: #94a3b8; }
h1 { margin-bottom: 4px; }
h3 { margin-bottom: 4px; font-size: 16px; }
.card { margin-bottom: 16px; }
</style>
