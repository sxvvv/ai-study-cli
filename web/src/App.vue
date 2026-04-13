<template>
  <div class="app">
    <NavBar />
    <main class="main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import NavBar from './components/NavBar.vue'
import { useProgressStore } from './stores/progress'

const store = useProgressStore()
store.fetchProgress()
store.fetchStreak()
</script>

<style>
:root {
  --bg: #0f172a;
  --card: #1e293b;
  --border: #334155;
  --text: #e2e8f0;
  --muted: #94a3b8;
  --accent: #3b82f6;
  --green: #22c55e;
  --red: #ef4444;
  --yellow: #eab308;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: var(--bg); color: var(--text); }
a { color: var(--accent); text-decoration: none; }
.card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; }
.btn { padding: 8px 16px; border-radius: 8px; border: none; cursor: pointer; font-size: 14px; font-weight: 500; transition: opacity .2s; }
.btn:hover { opacity: .85; }
.btn-primary { background: var(--accent); color: #fff; }
.btn-success { background: var(--green); color: #fff; }
.btn-danger { background: var(--red); color: #fff; }
.btn-warning { background: var(--yellow); color: #000; }
.main { max-width: 960px; margin: 0 auto; padding: 24px 16px; }
</style>
