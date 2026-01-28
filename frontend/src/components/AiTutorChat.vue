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
							{{ msg.text }}<span v-if="msg.isStreaming" class="animate-pulse">|</span>
						</div>
					</div>
				</div>
			</div>

			<!-- Typing indicator (only show when waiting for stream to start) -->
			<div v-if="isLoading && !isStreaming" class="flex justify-start">
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
import { ref, watch, onMounted, onUnmounted, computed, inject } from 'vue'
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

const socket = inject('$socket')
const messages = ref([])
const inputMessage = ref('')
const isLoading = ref(false)
const isStreaming = ref(false)
const currentRequestId = ref(null)
const streamingMessageIndex = ref(null)

// localStorage key for persistence
const storageKey = computed(() => `ai_tutor_${props.courseName}_${props.lessonName}`)

// Load messages from localStorage on mount
onMounted(() => {
	loadMessages()
	setupSocketListeners()
})

// Clean up socket listeners on unmount
onUnmounted(() => {
	cleanupSocketListeners()
})

// Watch for lesson changes and load appropriate history
watch(() => props.lessonName, () => {
	loadMessages()
})

const loadMessages = () => {
	const stored = localStorage.getItem(storageKey.value)
	if (stored) {
		try {
			const parsed = JSON.parse(stored)
			// Filter out any incomplete streaming messages from previous sessions
			messages.value = parsed.filter(msg => !msg.isStreaming)
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
	// Don't save messages that are still streaming
	const toSave = newMessages.map(msg => ({
		...msg,
		isStreaming: false,
	}))
	localStorage.setItem(storageKey.value, JSON.stringify(toSave))
}, { deep: true })

// Socket.IO event handlers
const setupSocketListeners = () => {
	socket.on('ai_tutor_stream_start', handleStreamStart)
	socket.on('ai_tutor_stream_chunk', handleStreamChunk)
	socket.on('ai_tutor_stream_end', handleStreamEnd)
	socket.on('ai_tutor_stream_error', handleStreamError)
}

const cleanupSocketListeners = () => {
	socket.off('ai_tutor_stream_start', handleStreamStart)
	socket.off('ai_tutor_stream_chunk', handleStreamChunk)
	socket.off('ai_tutor_stream_end', handleStreamEnd)
	socket.off('ai_tutor_stream_error', handleStreamError)
}

const handleStreamStart = (data) => {
	if (data.request_id !== currentRequestId.value) return

	isStreaming.value = true

	// Add empty streaming message
	streamingMessageIndex.value = messages.value.length
	messages.value.push({
		text: '',
		isUser: false,
		isStreaming: true,
	})
}

const handleStreamChunk = (data) => {
	if (data.request_id !== currentRequestId.value) return
	if (streamingMessageIndex.value === null) return

	// Append chunk to the streaming message
	const msg = messages.value[streamingMessageIndex.value]
	if (msg) {
		msg.text += data.chunk
	}
}

const handleStreamEnd = (data) => {
	if (data.request_id !== currentRequestId.value) return

	// Finalize the message
	if (streamingMessageIndex.value !== null) {
		const msg = messages.value[streamingMessageIndex.value]
		if (msg) {
			msg.isStreaming = false
			// Use complete response from server if available
			if (data.complete_response) {
				msg.text = data.complete_response
			}
		}
	}

	// Reset streaming state
	isStreaming.value = false
	isLoading.value = false
	currentRequestId.value = null
	streamingMessageIndex.value = null
}

const handleStreamError = (data) => {
	if (data.request_id !== currentRequestId.value) return

	console.error('AI Tutor streaming error:', data.error_type, data.message)

	// Update or add error message
	if (streamingMessageIndex.value !== null) {
		const msg = messages.value[streamingMessageIndex.value]
		if (msg) {
			msg.text = 'I encountered an error. Please try again.'
			msg.isStreaming = false
		}
	} else {
		messages.value.push({
			text: 'I encountered an error. Please try again.',
			isUser: false,
			isStreaming: false,
		})
	}

	// Reset streaming state
	isStreaming.value = false
	isLoading.value = false
	currentRequestId.value = null
	streamingMessageIndex.value = null
}

const sendMessage = async () => {
	const message = inputMessage.value.trim()
	if (!message || isLoading.value) return

	// Add user message
	messages.value.push({ text: message, isUser: true })
	inputMessage.value = ''
	isLoading.value = true

	try {
		const response = await call('lms.langchain.tutor_chat.api.ask_tutor', {
			message: message,
			current_lesson: props.lessonName,
			course_name: props.courseName,
		})

		console.log('response.mode: ', response.mode);
		if (response?.mode === 'streaming') {
			// Streaming mode - wait for Socket.IO events
			currentRequestId.value = response.request_id
			// The stream_start event will add the streaming message
		} else {
			// Sync mode - use response directly
			const tutorResponse = response?.response || 'I encountered an error. Please try again.'
			messages.value.push({ text: tutorResponse, isUser: false })
			isLoading.value = false
		}
	} catch (error) {
		console.error('AI Tutor error:', error)
		messages.value.push({
			text: 'I encountered an error. Please try again.',
			isUser: false,
		})
		isLoading.value = false
		isStreaming.value = false
		currentRequestId.value = null
		streamingMessageIndex.value = null
	}
}
</script>
