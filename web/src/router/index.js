import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'dashboard', component: () => import('../views/Dashboard.vue') },
  { path: '/skills', name: 'skills', component: () => import('../views/Skills.vue') },
  { path: '/streak', name: 'streak', component: () => import('../views/Streak.vue') },
  { path: '/quiz', name: 'quiz', component: () => import('../views/Quiz.vue') },
  { path: '/flashcards', name: 'flashcards', component: () => import('../views/Flashcards.vue') },
  { path: '/showcase', name: 'showcase', component: () => import('../views/Showcase.vue') },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
