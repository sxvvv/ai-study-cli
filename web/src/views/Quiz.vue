<template>
  <div class="quiz">
    <h1>Quiz</h1>

    <div v-if="loading" class="muted">Loading questions...</div>

    <div v-else-if="!questions.length" class="card">
      <p class="muted">No quiz questions available. Try again later.</p>
      <button class="btn btn-primary" @click="loadQuiz" style="margin-top:12px">Retry</button>
    </div>

    <div v-else>
      <div v-for="(q, i) in questions" :key="q.id" class="card quiz-card">
        <div class="quiz-num">Q{{ i + 1 }}</div>
        <div class="quiz-id">{{ q.id }}</div>
        <div class="quiz-question">{{ q.question }}</div>
        <div v-if="q.hint" class="quiz-hint">Hint: {{ q.hint }}</div>
        <div class="quiz-options">
          <button class="btn btn-success" @click="answer(q.id, 'understand')">✅ Understand</button>
          <button class="btn btn-warning" @click="answer(q.id, 'fuzzy')">🟡 Fuzzy</button>
          <button class="btn btn-danger" @click="answer(q.id, 'not_understand')">❌ Don't know</button>
        </div>
        <div v-if="results[q.id]" class="quiz-result">{{ results[q.id] }}</div>
      </div>
    </div>

    <div class="card" style="margin-top:20px">
      <button class="btn btn-primary" @click="loadQuiz">New Quiz (3 questions)</button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useQuizStore } from '../stores/progress'

const store = useQuizStore()
const questions = ref([])
const loading = ref(false)
const results = reactive({})

async function loadQuiz() {
  loading.value = true
  Object.keys(results).forEach(k => delete results[k])
  await store.fetchQuestions(3)
  questions.value = store.questions
  loading.value = false
}

async function answer(quizId, confidence) {
  const data = await store.answer(quizId, confidence)
  const labels = { understand: '✅ Understood', fuzzy: '🟡 Fuzzy', not_understand: '❌ Need review' }
  results[quizId] = labels[confidence] || confidence
}

onMounted(loadQuiz)
</script>

<style scoped>
.quiz-card { margin-bottom: 16px; }
.quiz-num { font-size: 12px; color: #3b82f6; font-weight: 700; text-transform: uppercase; }
.quiz-id { font-size: 12px; color: #94a3b8; margin-bottom: 8px; }
.quiz-question { font-size: 16px; line-height: 1.6; margin-bottom: 12px; }
.quiz-hint { font-size: 13px; color: #94a3b8; margin-bottom: 12px; padding: 8px; background: #33415540; border-radius: 6px; }
.quiz-options { display: flex; gap: 10px; flex-wrap: wrap; }
.quiz-result { margin-top: 10px; padding: 8px 12px; background: #22c55e15; border-radius: 6px; font-size: 14px; color: #22c55e; }
.muted { color: #94a3b8; font-size: 14px; }
h1 { margin-bottom: 20px; }
</style>
