<template>
	<div>
		<!-- Welcome/Empty State -->
		<div v-if="messages.length === 0" class="mb-6">
			<div class="text-ink-gray-6 text-sm leading-relaxed">
				{{ __('Have questions about this lesson? Ask me anything and I\'ll help explain concepts, clarify content, or answer your questions.') }}
			</div>
		</div>

		<!-- Messages Area -->
		<div v-if="messages.length > 0" class="space-y-4 mb-6">
			<div v-for="(msg, index) in messages" :key="index">
				<!-- User message -->
				<div v-if="msg.isUser" class="flex justify-end">
					<div class="max-w-[85%] bg-surface-gray-2 rounded-lg px-4 py-3">
						<div class="text-sm text-ink-gray-8 whitespace-pre-wrap leading-relaxed">
							{{ msg.text }}
						</div>
					</div>
				</div>
				<!-- Tutor message -->
				<div v-else class="flex justify-start">
					<div class="max-w-[85%]">
						<div class="flex items-center mb-1">
							<Sparkles class="size-3 text-blue-600 mr-1" />
							<span class="text-xs font-medium text-blue-600">AI Tutor</span>
						</div>
						<div class="text-sm text-ink-gray-8 whitespace-pre-wrap leading-relaxed">
							{{ msg.text }}
						</div>
					</div>
				</div>
			</div>

			<!-- Typing indicator -->
			<div v-if="isLoading" class="flex justify-start">
				<div>
					<div class="flex items-center mb-1">
						<Sparkles class="size-3 text-blue-600 mr-1" />
						<span class="text-xs font-medium text-blue-600">AI Tutor</span>
					</div>
					<div class="flex items-center space-x-1">
						<div class="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style="animation-delay: 0ms"></div>
						<div class="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style="animation-delay: 150ms"></div>
						<div class="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style="animation-delay: 300ms"></div>
					</div>
				</div>
			</div>
		</div>

		<!-- Input Area -->
		<div class="flex space-x-2">
			<input
				v-model="inputMessage"
				type="text"
				:placeholder="__('Ask about this lesson...')"
				class="flex-1 px-4 py-2.5 border border-gray-200 rounded-lg text-sm
					   focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
					   bg-surface-white"
				@keypress.enter="sendMessage"
				:disabled="isLoading"
			/>
			<Button
				variant="solid"
				@click="sendMessage"
				:disabled="isLoading || !inputMessage.trim()"
			>
				<template #icon>
					<Send class="size-4" />
				</template>
			</Button>
		</div>
	</div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue'
import { Button, call } from 'frappe-ui'
import { Sparkles, Send } from 'lucide-vue-next'

const props = defineProps({
	courseName: {
		type: String,
		required: true,
	},
	lessonName: {
		type: String,
		required: true,
	},
})

const messages = ref([])
const inputMessage = ref('')
const isLoading = ref(false)

// localStorage key for persistence
const storageKey = computed(() => `ai_tutor_${props.courseName}_${props.lessonName}`)

// Load messages from localStorage on mount
onMounted(() => {
	loadMessages()
})

// Watch for lesson changes and load appropriate history
watch(() => props.lessonName, () => {
	loadMessages()
})

const loadMessages = () => {
	const stored = localStorage.getItem(storageKey.value)
	if (stored) {
		try {
			messages.value = JSON.parse(stored)
		} catch (e) {
			console.warn('Failed to parse stored AI tutor messages')
			messages.value = []
		}
	} else {
		messages.value = []
	}
}

// Save messages to localStorage when they change
watch(messages, (newMessages) => {
	localStorage.setItem(storageKey.value, JSON.stringify(newMessages))
}, { deep: true })

const sendMessage = async () => {
	const message = inputMessage.value.trim()
	if (!message || isLoading.value) return

	// Add user message
	messages.value.push({ text: message, isUser: true })
	inputMessage.value = ''
	isLoading.value = true

	try {
		const response = await call('lms.langchain.tutor.ask_tutor', {
			message: message,
			current_lesson: props.lessonName,
			course_name: props.courseName,
		})
		
		const tutorResponse = response?.response || 'I encountered an error. Please try again.'
		messages.value.push({ text: tutorResponse, isUser: false })
	} catch (error) {
		console.error('AI Tutor error:', error)
		messages.value.push({
			text: 'I encountered an error. Please try again.',
			isUser: false,
		})
	} finally {
		isLoading.value = false
	}
}
</script>
