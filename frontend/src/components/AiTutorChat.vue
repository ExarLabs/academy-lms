<template>
	<div>
		<div class="flex items-center justify-between mb-4">
			<div class="flex items-center">
				<Sparkles class="size-5 text-ink-gray-5 mr-2" />
				<div class="text-xl font-semibold text-ink-gray-9">
					{{ __('AI Tutor') }}
				</div>
			</div>
			<Button
				v-if="messages.length > 0"
				variant="ghost"
				@click="clearHistory"
			>
				<template #icon>
					<Trash2 class="size-4" />
				</template>
			</Button>
		</div>

		<!-- Chat Container -->
		<div class="border rounded-lg bg-surface-white">
			<!-- Messages Area -->
			<div
				ref="messagesContainer"
				class="p-4 space-y-4 overflow-y-auto"
				:class="messages.length > 0 ? 'h-80' : 'h-40'"
			>
				<!-- Welcome message when empty -->
				<div v-if="messages.length === 0" class="text-center py-8">
					<Sparkles class="size-8 text-ink-gray-4 mx-auto mb-3" />
					<div class="text-ink-gray-7 font-medium">
						{{ __('Ask me anything about this lesson') }}
					</div>
					<div class="text-ink-gray-5 text-sm mt-1">
						{{ __('I can help explain concepts, answer questions, or clarify content.') }}
					</div>
				</div>

				<!-- Message history -->
				<div v-for="(msg, index) in messages" :key="index">
					<!-- User message -->
					<div v-if="msg.isUser" class="flex justify-end">
						<div class="max-w-[80%] bg-surface-gray-2 rounded-lg px-4 py-2">
							<div class="text-sm text-ink-gray-8 whitespace-pre-wrap">
								{{ msg.text }}
							</div>
						</div>
					</div>
					<!-- Tutor message -->
					<div v-else class="flex justify-start">
						<div class="max-w-[80%] bg-blue-50 rounded-lg px-4 py-2">
							<div class="flex items-center mb-1">
								<Sparkles class="size-3 text-blue-600 mr-1" />
								<span class="text-xs font-medium text-blue-600">AI Tutor</span>
							</div>
							<div class="text-sm text-ink-gray-8 whitespace-pre-wrap">
								{{ msg.text }}
							</div>
						</div>
					</div>
				</div>

				<!-- Typing indicator -->
				<div v-if="isLoading" class="flex justify-start">
					<div class="bg-blue-50 rounded-lg px-4 py-2">
						<div class="flex items-center">
							<Sparkles class="size-3 text-blue-600 mr-1" />
							<span class="text-xs font-medium text-blue-600">AI Tutor</span>
						</div>
						<div class="flex items-center space-x-1 mt-1">
							<div class="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style="animation-delay: 0ms"></div>
							<div class="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style="animation-delay: 150ms"></div>
							<div class="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style="animation-delay: 300ms"></div>
						</div>
					</div>
				</div>
			</div>

			<!-- Input Area -->
			<div class="border-t p-3">
				<div class="flex space-x-2">
					<input
						v-model="inputMessage"
						type="text"
						:placeholder="__('Ask about this lesson...')"
						class="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm
							   focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
		</div>
	</div>
</template>

<script setup>
import { ref, watch, onMounted, nextTick, computed } from 'vue'
import { Button, createResource } from 'frappe-ui'
import { Sparkles, Send, Trash2 } from 'lucide-vue-next'

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
const messagesContainer = ref(null)

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
			scrollToBottom()
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

const askTutorResource = createResource({
	url: 'lms.lms.ai_tutor.ask_tutor',
})

const scrollToBottom = () => {
	nextTick(() => {
		if (messagesContainer.value) {
			messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
		}
	})
}

const sendMessage = async () => {
	const message = inputMessage.value.trim()
	if (!message || isLoading.value) return

	// Add user message
	messages.value.push({ text: message, isUser: true })
	inputMessage.value = ''
	isLoading.value = true
	scrollToBottom()

	try {
		await askTutorResource.submit({
			message: message,
			current_lesson: props.lessonName,
			course_name: props.courseName,
		})
		
		const response = askTutorResource.data?.response || 
			'I encountered an error. Please try again.'
		messages.value.push({ text: response, isUser: false })
	} catch (error) {
		console.error('AI Tutor error:', error)
		messages.value.push({
			text: 'I encountered an error. Please try again.',
			isUser: false,
		})
	} finally {
		isLoading.value = false
		scrollToBottom()
	}
}

const clearHistory = () => {
	messages.value = []
	localStorage.removeItem(storageKey.value)
}
</script>
