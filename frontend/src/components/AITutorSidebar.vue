<template>
  <div class="flex h-full">
    <!-- Main content area -->
    <div class="flex-1 transition-all duration-300" :class="{ 'mr-0': !showSidebar, 'mr-[500px]': showSidebar }">
      <slot />
    </div>
    
    <!-- Collapsible Sidebar -->
    <div 
      class="fixed right-0 top-0 h-full bg-white border-l border-gray-300 shadow-lg transition-transform duration-300 z-40"
      :class="{ 'translate-x-0': showSidebar, 'translate-x-full': !showSidebar }"
      :style="{ width: '500px', minWidth: '500px' }"
    >
      <!-- Sidebar Header -->
      <div class="bg-blue-600 text-white p-3 flex justify-between items-center">
        <h3 class="font-semibold">{{ __("AI Tutor") }}</h3>
        <button @click="toggleSidebar" class="text-white hover:text-gray-200" :title="__('Close')">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>

      <!-- Chat Messages -->
      <div ref="messagesContainer" class="flex-1 p-4 overflow-y-auto bg-gray-50" style="height: calc(100vh - 140px);">
        <div v-for="(message, index) in messages" :key="index" class="mb-4">
          <div :class="message.sender === 'You' ? 'text-right' : 'text-left'">
            <div :class="[
              'inline-block p-3 rounded-lg max-w-sm',
              message.sender === 'You'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-800 border shadow-sm'
            ]">
              <div class="font-semibold text-xs mb-2">{{ message.sender }}</div>
              <div class="text-sm leading-relaxed whitespace-pre-wrap">{{ message.text }}</div>
            </div>
          </div>
        </div>
        <div v-if="isWaiting" class="text-left">
          <div class="inline-block p-3 rounded-lg bg-white text-gray-800 border shadow-sm">
            <div class="font-semibold text-xs mb-2">{{ __("Tutor") }}</div>
            <div class="text-sm flex items-center">
              <div class="animate-pulse">{{ __("Typing...") }}</div>
              <div class="ml-2 flex space-x-1">
                <div class="w-1 h-1 bg-gray-400 rounded-full animate-bounce"></div>
                <div class="w-1 h-1 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                <div class="w-1 h-1 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Chat Input -->
      <div class="p-4 border-t bg-white">
        <div class="flex space-x-3">
          <input 
            v-model="currentMessage" 
            @keyup.enter="sendMessage" 
            :disabled="isWaiting" 
            type="text"
            :placeholder="__('Ask your question about this course...')"
            class="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm" 
          />
          <button 
            @click="sendMessage" 
            :disabled="isWaiting || !currentMessage.trim()"
            class="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium transition-colors"
          >
            {{ __("Send") }}
          </button>
        </div>
      </div>
    </div>

    <!-- Toggle Button (when sidebar is closed) -->
    <div v-if="!showSidebar" class="fixed right-4 top-1/2 transform -translate-y-1/2 z-50">
      <button 
        @click="toggleSidebar"
        class="bg-blue-600 text-white p-3 rounded-l-lg shadow-lg hover:bg-blue-700 transition-colors"
        :title="__('Open AI Tutor')"
      >
        <MessageSquareText class="w-5 h-5 text-white stroke-1.5" />
        <div v-if="unreadMessages > 0"
          class="absolute -top-1 -left-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
          {{ unreadMessages }}
        </div>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, inject, onMounted } from 'vue'
import { MessageSquareText } from 'lucide-vue-next'
import { createResource } from 'frappe-ui'

const props = defineProps({
  courseName: String,
  lessonTitle: String
})

const showSidebar = ref(true) // Default to open
const currentMessage = ref('')
const messages = ref([])
const isWaiting = ref(false)
const messagesContainer = ref(null)
const unreadMessages = ref(0)

const user = inject('$user')

const chatResource = createResource({
  url: 'ai_tutor_chat.api.chat.ask_tutor',
  makeParams(values) {
    return {
      user_id: user.data?.name || 'guest',
      message: values.message,
      current_lesson: props.lessonTitle || 'Course Overview',
      course_name: props.courseName
    }
  }
})

onMounted(() => {
  // Add welcome message on mount since sidebar is open by default
  if (messages.value.length === 0) {
    messages.value.push({
      sender: __("Tutor"),
      text: __("Hello! I'm your AI tutor. I'm here to help you with any questions about this course. What would you like to know?")
    })
  }
})

const toggleSidebar = () => {
  showSidebar.value = !showSidebar.value
  if (showSidebar.value) {
    unreadMessages.value = 0
    if (messages.value.length === 0) {
      // Add welcome message
      messages.value.push({
        sender: __("Tutor"),
        text: __("Hello! I'm your AI tutor. I'm here to help you with any questions about this course. What would you like to know?")
      })
    }
  }
}

const sendMessage = async () => {
  if (!currentMessage.value.trim() || isWaiting.value) return

  const message = currentMessage.value.trim()

  // Add user message
  messages.value.push({
    sender: __("You"),
    text: message
  })

  currentMessage.value = ''
  isWaiting.value = true

  // Scroll to bottom
  await nextTick()
  scrollToBottom()

  try {
    const result = await chatResource.submit({ message })

    // Add tutor response
    const tutorMessage = {
      sender: __("Tutor"),
      text: result?.data?.response || __("I apologize, but I encountered an error. Please try again.")
    }

    messages.value.push(tutorMessage)

    // If sidebar is closed, increment unread counter
    if (!showSidebar.value) {
      unreadMessages.value++
    }

  } catch (error) {
    console.error('Chat error:', error)
    messages.value.push({
      sender: __("Tutor"),
      text: __("I apologize, but I encountered an error. Please try again.")
    })
  } finally {
    isWaiting.value = false
    await nextTick()
    scrollToBottom()
  }
}

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}
</script>

<style scoped>
@keyframes bounce {
  0%,
  80%,
  100% {
    transform: scale(0);
  }

  40% {
    transform: scale(1);
  }
}

.animate-bounce {
  animation: bounce 1.4s infinite ease-in-out both;
}
</style>
