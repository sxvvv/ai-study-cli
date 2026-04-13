import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const useProgressStore = defineStore('progress', () => {
  const progress = ref(null)
  const currentDay = ref(0)
  const phaseInfo = ref(null)
  const daysUntilJob = ref(null)
  const streak = ref(0)
  const streakLayer = ref('none')
  const loading = ref(false)

  const phaseName = computed(() => phaseInfo.value?.phase_name || '')
  const phaseProgress = computed(() => {
    if (!phaseInfo.value) return 0
    const { day_in_phase, total_in_phase } = phaseInfo.value
    return total_in_phase ? Math.round(day_in_phase / total_in_phase * 100) : 0
  })

  async function fetchProgress() {
    loading.value = true
    try {
      const { data } = await api.get('/progress')
      progress.value = data.progress
      currentDay.value = data.current_day
      phaseInfo.value = data.phase_info
      daysUntilJob.value = data.days_until_job
    } finally {
      loading.value = false
    }
  }

  async function fetchStreak() {
    const { data } = await api.get('/streak')
    streak.value = data.streak
    streakLayer.value = data.streak_layer
  }

  async function markDone(taskId) {
    const { data } = await api.post(`/tasks/${taskId}/done`)
    await fetchProgress()
    return data
  }

  async function markSkip(taskId, reason = '') {
    const { data } = await api.post(`/tasks/${taskId}/skip`, null, { params: { reason } })
    await fetchProgress()
    return data
  }

  return { progress, currentDay, phaseInfo, daysUntilJob, streak, streakLayer, loading, phaseName, phaseProgress, fetchProgress, fetchStreak, markDone, markSkip }
})

export const useQuizStore = defineStore('quiz', () => {
  const questions = ref([])
  const loading = ref(false)

  async function fetchQuestions(count = 3) {
    loading.value = true
    try {
      const { data } = await api.get('/quizzes', { params: { count } })
      questions.value = data.questions || []
    } finally {
      loading.value = false
    }
  }

  async function answer(quizId, confidence) {
    const { data } = await api.post('/quiz/answer', null, { params: { quiz_id: quizId, confidence } })
    return data
  }

  return { questions, loading, fetchQuestions, answer }
})

export const useFlashcardStore = defineStore('flashcard', () => {
  const cards = ref([])
  const loading = ref(false)

  async function fetchCards(count = 5) {
    loading.value = true
    try {
      const { data } = await api.get('/flashcards', { params: { count } })
      cards.value = data.cards || []
    } finally {
      loading.value = false
    }
  }

  async function review(cardId, remembered) {
    const { data } = await api.post('/flashcard/review', null, { params: { card_id: cardId, remembered } })
    return data
  }

  return { cards, loading, fetchCards, review }
})

export const useSkillStore = defineStore('skill', () => {
  const summary = ref(null)
  const gaps = ref([])
  const loading = ref(false)

  async function fetchSummary() {
    loading.value = true
    try {
      const { data } = await api.get('/skillmap/summary')
      summary.value = data
    } finally {
      loading.value = false
    }
  }

  async function fetchGaps() {
    const { data } = await api.get('/skillmap/gaps')
    gaps.value = data.gaps || []
  }

  async function updateLevel(skillId, level) {
    await api.post(`/skillmap/${skillId}/level`, null, { params: { level } })
    await fetchSummary()
  }

  return { summary, gaps, loading, fetchSummary, fetchGaps, updateLevel }
})
