<template>
	<header
		class="sticky top-0 z-10 flex items-center justify-between border-b bg-surface-white px-3 py-2.5 sm:px-5"
	>
		<Breadcrumbs :items="breadcrumbs" />
		<div class="flex items-center gap-2">
			<Button variant="subtle" @click="goBack">
				<template #prefix>
					<ChevronLeft class="h-4 w-4" />
				</template>
				{{ __('Back') }}
			</Button>
			<Button variant="subtle" @click="refreshData">
				<template #prefix>
					<RefreshCw class="h-4 w-4" />
				</template>
				{{ __('Refresh') }}
			</Button>
		</div>
	</header>

	<div class="p-5 space-y-6">
		<section class="rounded-xl border bg-surface-white p-5 shadow-sm">
			<div
				class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between"
			>
				<div>
					<div class="text-xs uppercase tracking-wide text-ink-gray-5">
						{{ __('Learner') }}
					</div>
					<div class="text-2xl font-semibold text-ink-gray-9">
						{{ learnerName }}
					</div>
					<div class="mt-1 text-sm text-ink-gray-6">
						{{ learnerEmail }}
					</div>
					<div class="mt-2 text-xs text-ink-gray-5">
						{{ __('User ID') }}: <span class="font-mono">{{ learnerId }}</span>
					</div>
					<div v-if="learnerPreferences" class="mt-3 flex flex-wrap gap-2">
						<span
							class="rounded-full bg-surface-gray-1 px-2 py-1 text-xs text-ink-gray-7"
						>
							{{ __('Pace') }}: {{ learnerPreferences.pace }}
						</span>
						<span
							class="rounded-full bg-surface-gray-1 px-2 py-1 text-xs text-ink-gray-7"
						>
							{{ __('Narrative') }}:
							{{ learnerPreferences.narrative ? __('On') : __('Off') }}
						</span>
						<span
							class="rounded-full bg-surface-gray-1 px-2 py-1 text-xs text-ink-gray-7"
						>
							{{ __('Tone') }}: {{ learnerPreferences.tone }}
						</span>
						<span
							class="rounded-full bg-surface-gray-1 px-2 py-1 text-xs text-ink-gray-7"
						>
							{{ __('Language') }}: {{ learnerPreferences.language }}
						</span>
					</div>
				</div>
				<div class="flex flex-col gap-1 text-sm text-ink-gray-6">
					<span class="text-xs uppercase tracking-wide text-ink-gray-5">
						{{ __('Last Activity') }}
					</span>
					<span class="text-base font-medium text-ink-gray-8">
						{{ formatDate(learnerLastActivity) }}
					</span>
				</div>
			</div>
		</section>

		<section class="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
			<div class="rounded-lg border bg-white p-4">
				<div class="text-sm text-ink-gray-5">{{ __('Courses Enrolled') }}</div>
				<div class="text-2xl font-semibold text-ink-gray-9">
					{{ stats.total_courses_enrolled || 0 }}
				</div>
			</div>
			<div class="rounded-lg border bg-white p-4">
				<div class="text-sm text-ink-gray-5">{{ __('Avg Quiz Score') }}</div>
				<div class="text-2xl font-semibold text-ink-gray-9">
					{{ stats.average_quiz_score || 0 }}%
				</div>
			</div>
			<div class="rounded-lg border bg-white p-4">
				<div class="text-sm text-ink-gray-5">
					{{ __('Total Quizzes Taken') }}
				</div>
				<div class="text-2xl font-semibold text-ink-gray-9">
					{{ stats.total_quiz_count || 0 }}
				</div>
			</div>
			<div class="rounded-lg border bg-white p-4">
				<div class="text-sm text-ink-gray-5">
					{{ __('Certificates Issued') }}
				</div>
				<div class="text-2xl font-semibold text-ink-gray-9">
					{{ stats.total_certificates || 0 }}
				</div>
			</div>
		</section>

		<section class="rounded-xl border bg-white p-5">
			<div class="mb-4 flex items-center justify-between">
				<div class="text-base font-semibold text-ink-gray-9">
					{{ __('Courses Enrolled') }}
				</div>
				<span class="text-xs text-ink-gray-5"
					>{{ courses.length }} {{ __('total') }}</span
				>
			</div>
			<div v-if="courses.length" class="flex flex-wrap gap-2">
				<span
					v-for="course in courses"
					:key="course"
					class="rounded-full border bg-surface-gray-1 px-3 py-1 text-xs text-ink-gray-7"
				>
					{{ course }}
				</span>
			</div>
			<div v-else class="text-sm text-ink-gray-5">
				{{ __('No courses enrolled yet') }}
			</div>
		</section>

		<section class="rounded-xl border bg-white p-5">
			<div class="mb-4 flex items-center justify-between">
				<div class="text-base font-semibold text-ink-gray-9">
					{{ __('Course Progress') }}
				</div>
				<span class="text-xs text-ink-gray-5"
					>{{ courseProgressRows.length }} {{ __('courses') }}</span
				>
			</div>
			<div class="overflow-hidden rounded-lg border">
				<table class="w-full">
					<thead class="bg-surface-gray-2">
						<tr>
							<th
								class="px-4 py-3 text-left text-sm font-medium text-ink-gray-5"
							>
								{{ __('Course') }}
							</th>
							<th
								class="px-4 py-3 text-left text-sm font-medium text-ink-gray-5"
							>
								{{ __('Progress') }}
							</th>
							<th
								class="px-4 py-3 text-left text-sm font-medium text-ink-gray-5"
							>
								{{ __('Last Lesson') }}
							</th>
							<th
								class="px-4 py-3 text-left text-sm font-medium text-ink-gray-5"
							>
								{{ __('Last Updated') }}
							</th>
						</tr>
					</thead>
					<tbody>
						<tr
							v-for="row in courseProgressRows"
							:key="row.course"
							class="border-t"
						>
							<td class="px-4 py-3 text-sm text-ink-gray-8">
								{{ row.course }}
							</td>
							<td class="px-4 py-3 text-sm text-ink-gray-8">
								{{ row.progress }}%
							</td>
							<td class="px-4 py-3 text-sm text-ink-gray-6">
								{{ row.last_lesson || '-' }}
							</td>
							<td class="px-4 py-3 text-sm text-ink-gray-6">
								{{ formatDate(row.last_updated) }}
							</td>
						</tr>
						<tr v-if="!courseProgressRows.length">
							<td
								colspan="4"
								class="px-4 py-6 text-center text-sm text-ink-gray-5"
							>
								{{ __('No course progress data yet') }}
							</td>
						</tr>
					</tbody>
				</table>
			</div>
		</section>

		<section class="rounded-xl border bg-white p-5">
			<div class="mb-4 flex items-center justify-between">
				<div class="text-base font-semibold text-ink-gray-9">
					{{ __('Certificates') }}
				</div>
				<span class="text-xs text-ink-gray-5"
					>{{ certificates.length }} {{ __('issued') }}</span
				>
			</div>
			<div class="overflow-hidden rounded-lg border">
				<table class="w-full">
					<thead class="bg-surface-gray-2">
						<tr>
							<th
								class="px-4 py-3 text-left text-sm font-medium text-ink-gray-5"
							>
								{{ __('Course') }}
							</th>
							<th
								class="px-4 py-3 text-left text-sm font-medium text-ink-gray-5"
							>
								{{ __('Issue Date') }}
							</th>
						</tr>
					</thead>
					<tbody>
						<tr
							v-for="cert in certificates"
							:key="cert.course_title"
							class="border-t"
						>
							<td class="px-4 py-3 text-sm text-ink-gray-8">
								{{ cert.course_title || '-' }}
							</td>
							<td class="px-4 py-3 text-sm text-ink-gray-6">
								{{ formatDate(cert.issue_date) }}
							</td>
						</tr>
						<tr v-if="!certificates.length">
							<td
								colspan="2"
								class="px-4 py-6 text-center text-sm text-ink-gray-5"
							>
								{{ __('No certificates issued yet') }}
							</td>
						</tr>
					</tbody>
				</table>
			</div>
		</section>

		<section class="rounded-xl border bg-white p-5">
			<div class="mb-4 flex items-center justify-between">
				<div class="text-base font-semibold text-ink-gray-9">
					{{ __('Assignments') }}
				</div>
				<span class="text-xs text-ink-gray-5"
					>{{ assignments.length }} {{ __('records') }}</span
				>
			</div>
			<div class="overflow-hidden rounded-lg border">
				<table class="w-full">
					<thead class="bg-surface-gray-2">
						<tr>
							<th
								class="px-4 py-3 text-left text-sm font-medium text-ink-gray-5"
							>
								{{ __('Title') }}
							</th>
							<th
								class="px-4 py-3 text-left text-sm font-medium text-ink-gray-5"
							>
								{{ __('Status') }}
							</th>
							<th
								class="px-4 py-3 text-left text-sm font-medium text-ink-gray-5"
							>
								{{ __('Course') }}
							</th>
							<th
								class="px-4 py-3 text-left text-sm font-medium text-ink-gray-5"
							>
								{{ __('Timestamp') }}
							</th>
						</tr>
					</thead>
					<tbody>
						<tr
							v-for="assignment in assignments"
							:key="assignmentKey(assignment)"
							class="border-t"
						>
							<td class="px-4 py-3 text-sm text-ink-gray-8">
								{{ assignment.title || '-' }}
							</td>
							<td class="px-4 py-3 text-sm">
								<span
									:class="statusClass(assignment.status)"
									class="inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium"
								>
									{{ assignment.status || __('Submitted') }}
								</span>
							</td>
							<td class="px-4 py-3 text-sm text-ink-gray-6">
								{{ assignment.course || '-' }}
							</td>
							<td class="px-4 py-3 text-sm text-ink-gray-6">
								{{ formatDate(assignment.timestamp) }}
							</td>
						</tr>
						<tr v-if="!assignments.length">
							<td
								colspan="4"
								class="px-4 py-6 text-center text-sm text-ink-gray-5"
							>
								{{ __('No assignments recorded yet') }}
							</td>
						</tr>
					</tbody>
				</table>
			</div>
		</section>

		<section v-if="detail.loading" class="rounded-lg border bg-white p-5">
			<div class="text-sm text-ink-gray-5">
				{{ __('Loading learner data...') }}
			</div>
		</section>

		<section
			v-if="!detail.loading && detail.error"
			class="rounded-lg border bg-white p-5"
		>
			<div class="text-sm text-ink-gray-5">
				{{ __('Unable to load learner details.') }}
			</div>
		</section>
	</div>
</template>

<script setup>
import { computed, inject, onMounted } from 'vue'
import { Breadcrumbs, Button, createResource, usePageMeta } from 'frappe-ui'
import { sessionStore } from '@/stores/session'
import { useRoute, useRouter } from 'vue-router'
import { ChevronLeft, RefreshCw } from 'lucide-vue-next'

const { brand } = sessionStore()
const user = inject('$user')
const dayjs = inject('$dayjs')
const route = useRoute()
const router = useRouter()

onMounted(() => {
	if (
		!user.data?.is_moderator &&
		!user.data?.is_instructor &&
		!user.data?.is_evaluator
	) {
		router.push({ name: 'Courses' })
	}
})

const learnerId = computed(() => route.params.userId || '')

const detail = createResource({
	url: 'lms.shared_data_service.api.get_profile_learner_detail',
	makeParams: () => ({
		user_id: learnerId.value,
	}),
	auto: true,
})

const stats = computed(() => detail.data?.learning_stats || {})

const learnerName = computed(
	() => detail.data?.full_name || detail.data?.email || __('Unknown Learner'),
)
const learnerEmail = computed(() => detail.data?.email || __('No email'))
const learnerLastActivity = computed(() => detail.data?.last_activity || null)

const learnerPreferences = computed(
	() => detail.data?.metadata?.preferences || null,
)

const courses = computed(() => stats.value.courses_enrolled || [])

const courseProgressRows = computed(() => {
	const progressMap = stats.value.course_progress || {}
	return Object.entries(progressMap).map(([course, data]) => ({
		course,
		progress: Math.round(data?.progress || 0),
		last_lesson: data?.last_lesson || null,
		last_updated: data?.last_updated || null,
	}))
})

const certificates = computed(() => {
	const list = stats.value.certificates || []
	return [...list].sort((a, b) => {
		return new Date(b.issue_date || 0) - new Date(a.issue_date || 0)
	})
})

const assignments = computed(() => {
	const list = stats.value.assignments || []
	return [...list].sort((a, b) => {
		return new Date(b.timestamp || 0) - new Date(a.timestamp || 0)
	})
})

const breadcrumbs = computed(() => {
	return [
		{
			label: __('Learner Analytics'),
			route: { name: 'LearnerAnalytics' },
		},
		{
			label: learnerName.value,
			route: {
				name: 'LearnerAnalyticsDetails',
				params: { userId: learnerId.value },
			},
		},
	]
})

usePageMeta(() => ({
	title: `${__('Learner Analytics')} — ${learnerName.value}`,
	icon: brand.favicon,
}))

const refreshData = () => {
	detail.reload()
}

const goBack = () => {
	router.push({ name: 'LearnerAnalytics' })
}

const formatDate = (date) => {
	return date ? dayjs(date).format('MMM D, YYYY h:mm A') : '-'
}

const assignmentKey = (assignment) => {
	return `${assignment?.title || 'assignment'}-${assignment?.timestamp || ''}`
}

const statusClass = (status) => {
	const normalized = (status || '').toLowerCase()
	if (['passed', 'complete', 'completed', 'approved'].includes(normalized)) {
		return 'bg-green-50 text-green-700'
	}
	if (['failed', 'rejected', 'incomplete'].includes(normalized)) {
		return 'bg-red-50 text-red-700'
	}
	if (['pending', 'submitted', 'in-review'].includes(normalized)) {
		return 'bg-yellow-50 text-yellow-800'
	}
	return 'bg-surface-gray-2 text-ink-gray-7'
}
</script>
