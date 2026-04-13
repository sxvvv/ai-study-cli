<template>
  <div class="flashcards">
    <h1>Flashcards</h1>

    <div v-if="loading" class="muted">Loading cards...</div>

    <div v-else-if="!cards.length" class="card">
      <p class="muted">No flashcards due for review today!</p>
      <button class="btn btn-primary" @click="loadCards" style="margin-top:12px">Refresh</button>
    </div>

    <div v-else>
      <div class="count">Due today: {{ cards.length }}</div>

      <div v-for="card in cards" :key="card.id" class="card fc-card">
        <div class="fc-meta">{{ card.topic || '' }} | {{ card.day || '' }}</div>

        <!-- Front -->
        <div v-if="!revealed[card.id]" class="fc-front">
          <div class="fc-question">{{ card.front }}</div>
          <button class="btn btn-primary" @click="reveal(card.id)">Show Answer</button>
        </div>

        <!-- Back -->
        <div v-else class="fc-back">
          <div class="fc-answer">{{ card.back }}</div>
          <div v-if="card.source" class="fc-source">Ref: {{ card.source }}</div>
          <div class="fc-actions">
            <button class="btn btn-danger" @click="handleReview(card.id, false)">Didn't remember</button>
            <button class="btn btn-success" @click="handleReview(card.id, true)">Remembered</button>
          </div>
        </div>

        <div v-if="reviewed[card.id]" class="fc-result">{{ reviewed[card.id] }}</div>
      </div>
    </div>

    <div class="card" style="margin-top:20px">
      <button class="btn btn-primary" @click="loadCards">Reload Cards</button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useFlashcardStore } from '../stores/progress'

const store = useFlashcardStore()
const cards = ref([])
const loading = ref(false)
const revealed = reactive({})
const reviewed = reactive({})

async function loadCards() {
  loading.value = true
  Object.keys(revealed).forEach(k => delete revealed[k])
  Object.keys(reviewed).forEach(k => delete reviewed[k])
  await store.fetchCards(10)
  cards.value = store.cards
  loading.value = false
}

function reveal(cardId) { revealed[cardId] = true }

async function handleReview(cardId, remembered) {
  const data = await store.review(cardId, remembered)
  reviewed[cardId] = remembered ? '✅ Marked as remembered' : '❌ Will review again soon'
}

onMounted(loadCards)
</script>

<style scoped>
.count { font-size: 14px; color: #94a3b8; margin-bottom: 16px; }
.fc-card { margin-bottom: 16px; }
.fc-meta { font-size: 12px; color: #94a3b8; margin-bottom: 12px; }
.fc-question { font-size: 16px; line-height: 1.6; margin-bottom: 16px; }
.fc-answer { font-size: 15px; line-height: 1.7; margin-bottom: 12px; padding: 12px; background: #3b82f610; border-radius: 8px; border-left: 3px solid #3b82f6; }
.fc-source { font-size: 12px; color: #94a3b8; margin-bottom: 12px; }
.fc-actions { display: flex; gap: 10px; }
.fc-result { margin-top: 10px; font-size: 14px; color: #22c55e; }
.muted { color: #94a3b8; }
h1 { margin-bottom: 8px; }
</style>
