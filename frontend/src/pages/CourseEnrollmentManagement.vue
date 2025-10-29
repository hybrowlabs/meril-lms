<template>
	<div>
		<header
			class="sticky top-0 z-10 flex items-center justify-between border-b bg-surface-white px-3 py-2.5 sm:px-5"
		>
			<Breadcrumbs :items="breadcrumbs" />
			<div class="flex items-center space-x-3">
				<Button variant="outline" @click="refreshData">
					<template #prefix>
						<RefreshCw class="h-4 w-4" />
					</template>
					{{ __('Refresh') }}
				</Button>
				<Button variant="solid" @click="showBulkReEnrollDialog = true">
					<template #prefix>
						<Users class="h-4 w-4" />
					</template>
					{{ __('Bulk Re-enroll') }}
				</Button>
			</div>
		</header>

		<div class="p-5">
			<!-- Analytics Cards -->
			<div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
				<div class="bg-white border rounded-lg p-6">
					<div class="flex items-center justify-between">
						<div>
							<p class="text-sm text-gray-600">{{ __('Total Completed') }}</p>
							<p class="text-2xl font-semibold text-gray-900">
								{{ analytics.completed_enrollments || 0 }}
							</p>
						</div>
						<CheckCircle class="h-8 w-8 text-green-600" />
					</div>
				</div>
				<div class="bg-white border rounded-lg p-6">
					<div class="flex items-center justify-between">
						<div>
							<p class="text-sm text-gray-600">{{ __('Re-enrolled') }}</p>
							<p class="text-2xl font-semibold text-gray-900">
								{{ analytics.re_enrolled_count || 0 }}
							</p>
						</div>
						<RotateCcw class="h-8 w-8 text-blue-600" />
					</div>
				</div>
				<div class="bg-white border rounded-lg p-6">
					<div class="flex items-center justify-between">
						<div>
							<p class="text-sm text-gray-600">{{ __('Completion Rate') }}</p>
							<p class="text-2xl font-semibold text-gray-900">
								{{ Math.round(analytics.completion_rate || 0) }}%
							</p>
						</div>
						<TrendingUp class="h-8 w-8 text-purple-600" />
					</div>
				</div>
			</div>

			<!-- Filters -->
			<div class="bg-white border rounded-lg p-4 mb-6">
				<div class="flex flex-wrap items-center gap-4">
					<div class="flex-1 min-w-64">
						<FormControl
							v-model="searchTerm"
							:placeholder="__('Search by user name or email')"
							type="text"
							@input="filterCompletedEnrollments"
						>
							<template #prefix>
								<Search class="h-4 w-4 text-gray-400" />
							</template>
						</FormControl>
					</div>
					<div class="min-w-48">
						<Select
							v-model="selectedCourse"
							:options="courseOptions"
							:placeholder="__('Filter by Course')"
							@change="filterCompletedEnrollments"
						/>
					</div>
					<div class="min-w-48">
						<Select
							v-model="memberTypeFilter"
							:options="memberTypeOptions"
							:placeholder="__('Filter by Member Type')"
							@change="filterCompletedEnrollments"
						/>
					</div>
					<Button variant="outline" @click="clearFilters">
						{{ __('Clear Filters') }}
					</Button>
				</div>
			</div>

			<!-- Completed Enrollments Table -->
			<div class="bg-white border rounded-lg overflow-hidden">
				<div class="px-6 py-4 border-b bg-gray-50">
					<h3 class="text-lg font-semibold text-gray-900">
						{{ __('Completed Course Enrollments') }}
					</h3>
					<p class="text-sm text-gray-600">
						{{ __('Users who have completed courses and need re-enrollment for access') }}
					</p>
				</div>

				<div v-if="loading" class="p-8 text-center">
					<div class="animate-spin h-8 w-8 mx-auto mb-4 border-2 border-blue-600 border-t-transparent rounded-full"></div>
					<p class="text-gray-600">{{ __('Loading enrollments...') }}</p>
				</div>

				<div v-else-if="filteredEnrollments.length === 0" class="p-8 text-center">
					<Users class="h-12 w-12 mx-auto mb-4 text-gray-400" />
					<p class="text-gray-600">{{ __('No completed enrollments found') }}</p>
				</div>

				<div v-else class="overflow-x-auto">
					<table class="min-w-full divide-y divide-gray-200">
						<thead class="bg-gray-50">
							<tr>
								<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									<input
										type="checkbox"
										v-model="selectAll"
										@change="toggleSelectAll"
										class="rounded border-gray-300"
									/>
								</th>
								<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									{{ __('User') }}
								</th>
								<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									{{ __('Course') }}
								</th>
								<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									{{ __('Member Type') }}
								</th>
								<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									{{ __('Completed On') }}
								</th>
								<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									{{ __('Progress') }}
								</th>
								<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									{{ __('Actions') }}
								</th>
							</tr>
						</thead>
						<tbody class="bg-white divide-y divide-gray-200">
							<tr
								v-for="enrollment in filteredEnrollments"
								:key="enrollment.name"
								:class="{ 'bg-blue-50': selectedEnrollments.includes(enrollment.name) }"
							>
								<td class="px-6 py-4 whitespace-nowrap">
									<input
										type="checkbox"
										:value="enrollment.name"
										v-model="selectedEnrollments"
										class="rounded border-gray-300"
									/>
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									<div class="flex items-center">
										<UserAvatar :user="{ name: enrollment.member }" class="mr-3" />
										<div>
											<div class="text-sm font-medium text-gray-900">
												{{ enrollment.member_name }}
											</div>
											<div class="text-sm text-gray-500">
												{{ enrollment.member }}
											</div>
										</div>
									</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									<div class="text-sm text-gray-900">{{ enrollment.course_title }}</div>
									<div class="text-sm text-gray-500">{{ enrollment.course }}</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									<Badge
										:theme="getMemberTypeBadgeTheme(enrollment.member_type)"
										variant="subtle"
									>
										{{ enrollment.member_type }}
									</Badge>
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
									{{ formatDate(enrollment.completed_on) }}
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									<div class="text-sm text-gray-900">{{ enrollment.progress }}%</div>
									<div class="w-full bg-gray-200 rounded-full h-2">
										<div
											class="bg-green-600 h-2 rounded-full"
											:style="{ width: enrollment.progress + '%' }"
										></div>
									</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
									<div class="flex items-center space-x-2">
										<Button
											variant="outline"
											size="sm"
											@click="reEnrollSingleUser(enrollment)"
										>
											<template #prefix>
												<RotateCcw class="h-4 w-4" />
											</template>
											{{ __('Re-enroll') }}
										</Button>
									</div>
								</td>
							</tr>
						</tbody>
					</table>
				</div>
			</div>
		</div>

		<!-- Bulk Re-enrollment Dialog -->
		<Dialog v-model="showBulkReEnrollDialog">
			<template #body>
				<div class="p-6">
					<div class="flex items-center mb-4">
						<Users class="h-6 w-6 text-blue-600 mr-2" />
						<h3 class="text-lg font-semibold">{{ __('Bulk Re-enrollment') }}</h3>
					</div>
					
					<p class="text-sm text-gray-600 mb-4">
						{{ __('Re-enroll selected users in their completed courses. This will restore their access.') }}
					</p>

					<div class="space-y-4">
						<FormControl
							v-model="resetProgressOnReEnroll"
							:label="__('Reset course progress to 0%')"
							type="checkbox"
						/>
						
						<div v-if="selectedEnrollments.length > 0" class="border rounded-lg p-4 bg-gray-50">
							<h4 class="font-medium mb-2">{{ __('Selected Enrollments') }}: {{ selectedEnrollments.length }}</h4>
							<div class="max-h-32 overflow-y-auto">
								<div
									v-for="enrollmentId in selectedEnrollments"
									:key="enrollmentId"
									class="text-sm text-gray-600"
								>
									{{ getEnrollmentDisplayName(enrollmentId) }}
								</div>
							</div>
						</div>
					</div>

					<div class="flex justify-end space-x-3 mt-6">
						<Button variant="subtle" @click="showBulkReEnrollDialog = false">
							{{ __('Cancel') }}
						</Button>
						<Button
							variant="solid"
							@click="executeBulkReEnrollment"
							:loading="bulkReEnrollLoading"
							:disabled="selectedEnrollments.length === 0"
						>
							{{ __('Re-enroll Selected') }}
						</Button>
					</div>
				</div>
			</template>
		</Dialog>

		<!-- Single Re-enrollment Dialog -->
		<Dialog v-model="showSingleReEnrollDialog">
			<template #body>
				<div class="p-6" v-if="selectedEnrollmentForReEnroll">
					<div class="flex items-center mb-4">
						<RotateCcw class="h-6 w-6 text-blue-600 mr-2" />
						<h3 class="text-lg font-semibold">{{ __('Re-enroll User') }}</h3>
					</div>
					
					<p class="text-sm text-gray-600 mb-4">
						{{ __('Re-enroll {0} in {1}?', [selectedEnrollmentForReEnroll.member_name, selectedEnrollmentForReEnroll.course_title]) }}
					</p>

					<FormControl
						v-model="resetProgressOnSingleReEnroll"
						:label="__('Reset course progress to 0%')"
						type="checkbox"
					/>

					<div class="flex justify-end space-x-3 mt-6">
						<Button variant="subtle" @click="showSingleReEnrollDialog = false">
							{{ __('Cancel') }}
						</Button>
						<Button
							variant="solid"
							@click="executeSingleReEnrollment"
							:loading="singleReEnrollLoading"
						>
							{{ __('Re-enroll') }}
						</Button>
					</div>
				</div>
			</template>
		</Dialog>
	</div>
</template>

<script setup>
import {
	Breadcrumbs,
	Button,
	call,
	FormControl,
	Select,
	Badge,
	Dialog,
	usePageMeta,
} from 'frappe-ui'
import { computed, onMounted, ref } from 'vue'
import {
	RefreshCw,
	Users,
	CheckCircle,
	RotateCcw,
	TrendingUp,
	Search,
} from 'lucide-vue-next'
import { sessionStore } from '@/stores/session'
import UserAvatar from '@/components/UserAvatar.vue'

const { user } = sessionStore()

// Reactive data
const completedEnrollments = ref([])
const filteredEnrollments = ref([])
const analytics = ref({})
const loading = ref(true)
const searchTerm = ref('')
const selectedCourse = ref(null)
const memberTypeFilter = ref(null)
const courseOptions = ref([{ label: 'All Courses', value: null }])
const memberTypeOptions = ref([
	{ label: 'All Types', value: null },
	{ label: 'Student', value: 'Student' },
	{ label: 'Mentor', value: 'Mentor' },
	{ label: 'Staff', value: 'Staff' }
])

// Selection and bulk operations
const selectedEnrollments = ref([])
const selectAll = ref(false)
const showBulkReEnrollDialog = ref(false)
const bulkReEnrollLoading = ref(false)
const resetProgressOnReEnroll = ref(false)

// Single re-enrollment
const showSingleReEnrollDialog = ref(false)
const selectedEnrollmentForReEnroll = ref(null)
const singleReEnrollLoading = ref(false)
const resetProgressOnSingleReEnroll = ref(false)

onMounted(() => {
	loadData()
})

const loadData = async () => {
	loading.value = true
	try {
		// Load data with individual error handling
		const results = await Promise.allSettled([
			loadCompletedEnrollments(),
			loadAnalytics()
		])
		
		// Log any failures for debugging
		results.forEach((result, index) => {
			if (result.status === 'rejected') {
				const functionNames = ['Completed Enrollments', 'Analytics']
				console.error(`Failed to load ${functionNames[index]}:`, result.reason)
			}
		})
	} catch (error) {
		console.error('Failed to load data:', error)
	} finally {
		loading.value = false
	}
}

const loadCompletedEnrollments = async () => {
	try {
		const data = await call('lms.lms.api.get_users_for_re_enrollment')
		completedEnrollments.value = data || []
		filteredEnrollments.value = data || []
		
		// Build course options
		const courses = [...new Set((data || []).map(e => e.course_title))]
		courseOptions.value = [
			{ label: 'All Courses', value: null },
			...courses.map(course => ({ label: course, value: course }))
		]
	} catch (error) {
		console.error('Failed to load completed enrollments:', error)
		completedEnrollments.value = []
		filteredEnrollments.value = []
	}
}

const loadAnalytics = async () => {
	try {
		const data = await call('lms.lms.api.get_course_completion_analytics')
		analytics.value = data || {}
	} catch (error) {
		console.error('Failed to load analytics:', error)
		analytics.value = {}
	}
}

const filterCompletedEnrollments = () => {
	let filtered = completedEnrollments.value

	if (searchTerm.value) {
		const search = searchTerm.value.toLowerCase()
		filtered = filtered.filter(enrollment => 
			enrollment.member_name.toLowerCase().includes(search) ||
			enrollment.member.toLowerCase().includes(search)
		)
	}

	if (selectedCourse.value) {
		filtered = filtered.filter(enrollment => 
			enrollment.course_title === selectedCourse.value
		)
	}

	if (memberTypeFilter.value) {
		filtered = filtered.filter(enrollment => 
			enrollment.member_type === memberTypeFilter.value
		)
	}

	filteredEnrollments.value = filtered
	selectedEnrollments.value = []
	selectAll.value = false
}

const clearFilters = () => {
	searchTerm.value = ''
	selectedCourse.value = null
	memberTypeFilter.value = null
	filterCompletedEnrollments()
}

const toggleSelectAll = () => {
	if (selectAll.value) {
		selectedEnrollments.value = filteredEnrollments.value.map(e => e.name)
	} else {
		selectedEnrollments.value = []
	}
}

const reEnrollSingleUser = (enrollment) => {
	selectedEnrollmentForReEnroll.value = enrollment
	resetProgressOnSingleReEnroll.value = false
	showSingleReEnrollDialog.value = true
}

const executeSingleReEnrollment = async () => {
	singleReEnrollLoading.value = true
	try {
		// Guard: block if a re-enrollment is already running
		const guard = await call('lms.lms.api.can_re_enroll_user', {
			member_email: selectedEnrollmentForReEnroll.value.member,
			course_name: selectedEnrollmentForReEnroll.value.course
		})
		if (guard && guard.can_re_enroll === false && guard.reason === 'already_running') {
			alert('A re-enrollment is already running. Please finish the current course first.')
			return
		}
		await call('lms.lms.api.admin_re_enroll_user', {
			course_name: selectedEnrollmentForReEnroll.value.course,
			member_email: selectedEnrollmentForReEnroll.value.member,
			reset_progress: resetProgressOnSingleReEnroll.value
		})
		
		showSingleReEnrollDialog.value = false
		// Refresh all data after re-enrollment
		await loadData()
		
		// Show success message
		alert('User successfully re-enrolled!')
	} catch (error) {
		console.error('Failed to re-enroll user:', error)
		alert('Failed to re-enroll user: ' + error.message)
	} finally {
		singleReEnrollLoading.value = false
	}
}

const executeBulkReEnrollment = async () => {
	bulkReEnrollLoading.value = true
	try {
		// Guard: check all selected enrollments and skip those already running
		const checks = await Promise.all(selectedEnrollments.value.map(enrollmentId => {
			const e = completedEnrollments.value.find(x => x.name === enrollmentId)
			return call('lms.lms.api.can_re_enroll_user', {
				member_email: e.member,
				course_name: e.course
			}).then(res => ({ id: enrollmentId, ok: !!(res && res.can_re_enroll !== false), reason: res && res.reason }))
		}))

		const allowedIds = checks.filter(c => c.ok).map(c => c.id)
		const skipped = checks.filter(c => !c.ok)

		if (allowedIds.length === 0) {
			alert('All selected users already have an active re-enrollment running.')
			return
		}

		const enrollmentsData = allowedIds.map(enrollmentId => {
			const enrollment = completedEnrollments.value.find(e => e.name === enrollmentId)
			return {
				course: enrollment.course,
				member: enrollment.member,
				reset_progress: resetProgressOnReEnroll.value
			}
		})

		const results = await call('lms.lms.api.bulk_re_enroll_users', {
			enrollments_data: JSON.stringify(enrollmentsData)
		})
		
		showBulkReEnrollDialog.value = false
		selectedEnrollments.value = []
		// Refresh all data after bulk re-enrollment
		await loadData()
		
		// Show results summary (include skipped info if any)
		const successful = results.filter(r => r.success).length
		const failed = results.filter(r => !r.success).length
		const skippedMsg = skipped.length ? `, ${skipped.length} skipped (already running)` : ''
		alert(`Bulk re-enrollment completed: ${successful} successful, ${failed} failed${skippedMsg}`)
		
	} catch (error) {
		console.error('Failed to bulk re-enroll:', error)
		alert('Failed to perform bulk re-enrollment: ' + error.message)
	} finally {
		bulkReEnrollLoading.value = false
	}
}

const refreshData = async () => {
	await loadData()
}

const formatDate = (dateString) => {
	if (!dateString) return ''
	return new Date(dateString).toLocaleDateString()
}

const getMemberTypeBadgeTheme = (memberType) => {
	switch (memberType) {
		case 'Student': return 'blue'
		case 'Mentor': return 'green'
		case 'Staff': return 'purple'
		default: return 'gray'
	}
}

const getEnrollmentDisplayName = (enrollmentId) => {
	const enrollment = completedEnrollments.value.find(e => e.name === enrollmentId)
	return enrollment ? `${enrollment.member_name} - ${enrollment.course_title}` : enrollmentId
}

const breadcrumbs = computed(() => [
	{
		label: 'LMS',
		route: { name: 'Courses' },
	},
	{
		label: 'Course Enrollment Management',
		route: { name: 'CourseEnrollmentManagement' },
	},
])

usePageMeta(() => {
	return {
		title: 'Course Enrollment Management',
		description: 'Manage course completions and re-enrollments'
	}
})
</script> 