<template>
	<header
		class="sticky top-0 z-10 flex items-center justify-between border-b bg-surface-white px-3 py-2.5 sm:px-5"
	>
		<Breadcrumbs :items="breadcrumbs" />
		<Button variant="subtle" @click="refreshData">
			<template #prefix>
				<RefreshCw class="h-4 w-4" />
			</template>
			{{ __('Refresh') }}
		</Button>
	</header>

	<div class="p-5">
		<!-- Overview Cards -->
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
			<div class="bg-white rounded-lg border p-4">
				<div class="text-sm text-ink-gray-5">
					{{ __('Total Learners') }}
				</div>
				<div class="text-2xl font-semibold">
					{{ overview.data?.total_learners || 0 }}
				</div>
			</div>
			<div class="bg-white rounded-lg border p-4">
				<div class="text-sm text-ink-gray-5">{{ __('Avg Quiz Score') }}</div>
				<div class="text-2xl font-semibold">
					{{ overview.data?.average_quiz_score || 0 }}%
				</div>
			</div>
			<div class="bg-white rounded-lg border p-4">
				<div class="text-sm text-ink-gray-5">
					{{ __('Total Quizzes Taken') }}
				</div>
				<div class="text-2xl font-semibold">
					{{ overview.data?.total_quizzes_taken || 0 }}
				</div>
			</div>
			<div class="bg-white rounded-lg border p-4">
				<div class="text-sm text-ink-gray-5">
					{{ __('Certificates Issued') }}
				</div>
				<div class="text-2xl font-semibold">
					{{ overview.data?.total_certificates_issued || 0 }}
				</div>
			</div>
		</div>

		<!-- Search -->
		<div class="mb-4">
			<FormControl
				v-model="searchQuery"
				type="text"
				:placeholder="__('Search by name or email...')"
				@input="debouncedSearch"
			>
				<template #prefix>
					<Search class="h-4 w-4 text-ink-gray-5" />
				</template>
			</FormControl>
		</div>

		<!-- Learners Table -->
		<div class="bg-white rounded-lg border overflow-hidden">
			<table class="w-full">
				<thead class="bg-surface-gray-2">
					<tr>
						<th
							class="px-4 py-3 text-left text-sm font-medium text-ink-gray-5 cursor-pointer hover:text-ink-gray-7"
							@click="sortBy('full_name')"
						>
							<div class="flex items-center gap-1">
								{{ __('Name') }}
								<ArrowUpDown
									v-if="currentSort === 'full_name'"
									class="h-3 w-3"
								/>
							</div>
						</th>
						<th
							class="px-4 py-3 text-left text-sm font-medium text-ink-gray-5 cursor-pointer hover:text-ink-gray-7"
							@click="sortBy('email')"
						>
							<div class="flex items-center gap-1">
								{{ __('Email') }}
								<ArrowUpDown v-if="currentSort === 'email'" class="h-3 w-3" />
							</div>
						</th>
						<th class="px-4 py-3 text-left text-sm font-medium text-ink-gray-5">
							{{ __('Courses') }}
						</th>
						<th class="px-4 py-3 text-left text-sm font-medium text-ink-gray-5">
							{{ __('Avg Score') }}
						</th>
						<th class="px-4 py-3 text-left text-sm font-medium text-ink-gray-5">
							{{ __('Certificates') }}
						</th>
						<th
							class="px-4 py-3 text-left text-sm font-medium text-ink-gray-5 cursor-pointer hover:text-ink-gray-7"
							@click="sortBy('last_activity')"
						>
							<div class="flex items-center gap-1">
								{{ __('Last Activity') }}
								<ArrowUpDown
									v-if="currentSort === 'last_activity'"
									class="h-3 w-3"
								/>
							</div>
						</th>
					</tr>
				</thead>
				<tbody>
					<tr
						v-for="learner in learners.data?.learners || []"
						:key="learner.frappe_user_id"
						class="border-t hover:bg-surface-gray-1 cursor-pointer"
						@click="openLearner(learner)"
					>
						<td class="px-4 py-3">{{ learner.full_name || '-' }}</td>
						<td class="px-4 py-3">{{ learner.email }}</td>
						<td class="px-4 py-3">{{ learner.total_courses }}</td>
						<td class="px-4 py-3">{{ learner.avg_quiz_score }}%</td>
						<td class="px-4 py-3">{{ learner.total_certificates }}</td>
						<td class="px-4 py-3 text-ink-gray-5">
							{{ formatDate(learner.last_activity) }}
						</td>
					</tr>
					<tr v-if="!learners.data?.learners?.length && !learners.loading">
						<td colspan="6" class="px-4 py-8 text-center text-ink-gray-5">
							{{ __('No learners found') }}
						</td>
					</tr>
					<tr v-if="learners.loading">
						<td colspan="6" class="px-4 py-8 text-center text-ink-gray-5">
							{{ __('Loading...') }}
						</td>
					</tr>
				</tbody>
			</table>
		</div>

		<!-- Pagination -->
		<div class="flex justify-between items-center mt-4">
			<span class="text-sm text-ink-gray-5">
				{{
					__('Showing {0} - {1} of {2}').format(
						skip + 1,
						Math.min(skip + limit, learners.data?.total || 0),
						learners.data?.total || 0
					)
				}}
			</span>
			<div class="flex gap-2">
				<Button variant="subtle" :disabled="skip === 0" @click="prevPage">
					{{ __('Previous') }}
				</Button>
				<Button
					variant="subtle"
					:disabled="skip + limit >= (learners.data?.total || 0)"
					@click="nextPage"
				>
					{{ __('Next') }}
				</Button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, computed, inject, onMounted } from 'vue'
import {
	Breadcrumbs,
	Button,
	FormControl,
	createResource,
	usePageMeta,
} from 'frappe-ui'
import { sessionStore } from '@/stores/session'
import { useRouter } from 'vue-router'
import { RefreshCw, Search, ArrowUpDown } from 'lucide-vue-next'
import { debounce } from 'lodash'

const { brand } = sessionStore()
const user = inject('$user')
const dayjs = inject('$dayjs')
const router = useRouter()

// Access control
onMounted(() => {
	if (!user.data?.is_moderator && !user.data?.is_instructor && !user.data?.is_evaluator) {
		router.push({ name: 'Courses' })
	}
})

const breadcrumbs = computed(() => {
	return [
		{
			label: __('Learner Analytics'),
			route: {
				name: 'LearnerAnalytics',
			},
		},
	]
})

usePageMeta(() => {
	return {
		title: __('Learner Analytics'),
		icon: brand.favicon,
	}
})

// State
const searchQuery = ref('')
const currentSort = ref('last_activity')
const skip = ref(0)
const limit = ref(50)

// API resources
const overview = createResource({
	url: 'lms.shared_data_service.api.get_profile_stats_overview',
	auto: true,
})

const learners = createResource({
	url: 'lms.shared_data_service.api.get_profile_learners_stats',
	params: computed(() => ({
		skip: skip.value,
		limit: limit.value,
		search: searchQuery.value,
		sort_by: currentSort.value,
	})),
	auto: true,
})

// Actions
const refreshData = () => {
	overview.reload()
	learners.reload()
}

const debouncedSearch = debounce(() => {
	skip.value = 0
	learners.reload()
}, 300)

const sortBy = (field) => {
	currentSort.value = field
	learners.reload()
}

const prevPage = () => {
	skip.value = Math.max(0, skip.value - limit.value)
	learners.reload()
}

const nextPage = () => {
	skip.value += limit.value
	learners.reload()
}

const formatDate = (date) => {
	return date ? dayjs(date).format('MMM D, YYYY h:mm A') : '-'
}

const openLearner = (learner) => {
	if (!learner?.frappe_user_id) return
	router.push({
		name: 'LearnerAnalyticsDetails',
		params: { userId: learner.frappe_user_id },
	})
}
</script>
