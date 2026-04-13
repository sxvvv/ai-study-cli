<template>
  <nav class="navbar">
    <div class="nav-inner">
      <router-link to="/" class="logo">AI Study</router-link>
      <div class="nav-links">
        <router-link to="/">Dashboard</router-link>
        <router-link to="/skills">Skills</router-link>
        <router-link to="/streak">Streak</router-link>
        <router-link to="/quiz">Quiz</router-link>
        <router-link to="/flashcards">Flashcards</router-link>
        <router-link to="/showcase">Showcase</router-link>
      </div>
      <div class="streak-badge" v-if="streak > 0">
        🔥 {{ streak }}天
      </div>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useProgressStore } from '../stores/progress'
const store = useProgressStore()
const streak = computed(() => store.streak)
</script>

<style scoped>
.navbar { background: #1e293b; border-bottom: 1px solid #334155; position: sticky; top: 0; z-index: 10; }
.nav-inner { max-width: 960px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; }
.logo { font-weight: 700; font-size: 18px; color: #e2e8f0; }
.nav-links { display: flex; gap: 20px; }
.nav-links a { color: #94a3b8; font-size: 14px; padding: 4px 0; border-bottom: 2px solid transparent; transition: all .2s; }
.nav-links a:hover, .nav-links a.router-link-active { color: #e2e8f0; border-bottom-color: #3b82f6; }
.streak-badge { background: linear-gradient(135deg, #f97316, #ef4444); padding: 4px 12px; border-radius: 20px; font-size: 13px; font-weight: 600; }
</style>
