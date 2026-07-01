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
				<Button variant="solid" @click="sendCourseReminders">
					<template #prefix>
						<Send class="h-4 w-4" />
					</template>
					{{ __('Send Course Reminders') }}
				</Button>
			</div>
		</header>

		<div class="p-5">
			<!-- Main KPI Cards -->
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
				<!-- Total Enrolled Users -->
				<div class="bg-white border rounded-lg p-6 cursor-pointer hover:shadow-md transition-shadow" @click="showUsersDialog('total')">
					<div class="flex items-center justify-between">
						<div>
							<p class="text-sm text-gray-600">{{ __('Total Enrolled Users') }}</p>
							<p class="text-2xl font-semibold text-gray-900">
								{{ (kpiData && kpiData.total_enrolled_users) || 0 }}
							</p>
						</div>
						<Users class="h-8 w-8 text-blue-600" />
					</div>
				</div>

				<!-- Completed Courses -->
				<div class="bg-white border rounded-lg p-6 cursor-pointer hover:shadow-md transition-shadow" @click="showUsersDialog('completed')">
					<div class="flex items-center justify-between">
						<div>
							<p class="text-sm text-gray-600">{{ __('Completed Courses') }}</p>
							<p class="text-2xl font-semibold text-green-600">
								{{ (kpiData && kpiData.completed_courses) || 0 }}
							</p>
							<p class="text-xs text-gray-500">
								{{ Math.round(((kpiData && kpiData.completed_courses) || 0) / ((kpiData && kpiData.total_enrolled_users) || 1) * 100) || 0 }}% completion rate
							</p>
						</div>
						<CheckCircle class="h-8 w-8 text-green-600" />
					</div>
				</div>

				<!-- Pending Completions -->
				<div class="bg-white border rounded-lg p-6 cursor-pointer hover:shadow-md transition-shadow" @click="showUsersDialog('pending')">
					<div class="flex items-center justify-between">
						<div>
							<p class="text-sm text-gray-600">{{ __('Pending Completions') }}</p>
							<p class="text-2xl font-semibold text-red-600">
								{{ (kpiData && kpiData.pending_completions) || 0 }}
							</p>
							<p class="text-xs text-gray-500">
								{{ (kpiData && kpiData.avg_reminders_sent) || 0 }} avg reminders sent
							</p>
						</div>
						<AlertTriangle class="h-8 w-8 text-red-600" />
					</div>
				</div>

				<!-- Total Reminders Sent -->
				<div class="bg-white border rounded-lg p-6 cursor-pointer hover:shadow-md transition-shadow" @click="showRemindersDialog">
					<div class="flex items-center justify-between">
						<div>
							<p class="text-sm text-gray-600">{{ __('Course Reminders') }}</p>
							<p class="text-2xl font-semibold text-purple-600">
								{{ (kpiData && kpiData.total_course_reminders_sent) || 0 }}
							</p>
							<p class="text-xs text-gray-500">
								{{ (kpiData && kpiData.reminders_sent_today) || 0 }} sent today
							</p>
						</div>
						<Mail class="h-8 w-8 text-purple-600" />
					</div>
				</div>
			</div>

			<!-- Detailed Analytics Cards -->
			<div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
				<!-- Recent Course Completions -->
				<div class="bg-white border rounded-lg p-6">
					<h3 class="text-lg font-semibold text-gray-900 mb-4">{{ __('Recent Course Completions') }}</h3>
					<div class="space-y-3 max-h-64 overflow-y-auto">
						<div v-if="recentCompletions.length === 0" class="text-center text-gray-500 py-4">
							{{ __('No recent course completions') }}
						</div>
						<div v-for="completion in recentCompletions" :key="completion.enrollment_id" class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
							<div class="flex items-center">
								<div class="w-3 h-3 bg-green-500 rounded-full mr-3"></div>
								<div>
									<p class="font-medium text-gray-900">{{ completion.user_name }}</p>
									<p class="text-sm text-gray-600">{{ completion.course_title }}</p>
								</div>
							</div>
							<div class="text-right">
								<p class="text-sm text-gray-900">{{ formatDateTime(completion.completed_on) }}</p>
								<p class="text-xs text-gray-500">
									<span class="text-green-600 font-medium">{{ completion.progress }}% Complete</span>
								</p>
							</div>
						</div>
					</div>
				</div>

				<!-- Course Reminder Statistics -->
				<div class="bg-white border rounded-lg p-6">
					<h3 class="text-lg font-semibold text-gray-900 mb-4">{{ __('Course Completion Effectiveness') }}</h3>
					<div class="space-y-4">
						<div class="flex justify-between items-center">
							<span class="text-gray-600">{{ __('Completion Rate') }}</span>
							<span class="text-lg font-semibold text-green-600">{{ (kpiData && kpiData.completion_rate) || 0 }}%</span>
						</div>
						<div class="flex justify-between items-center">
							<span class="text-gray-600">{{ __('Avg Time to Complete') }}</span>
							<span class="text-lg font-semibold text-blue-600">{{ (kpiData && kpiData.avg_time_to_complete) || 0 }} days</span>
						</div>
						<div class="flex justify-between items-center">
							<span class="text-gray-600">{{ __('Most Active Course') }}</span>
							<span class="text-lg font-semibold text-purple-600">{{ (kpiData && kpiData.most_active_course) || 'N/A' }}</span>
						</div>
					</div>
				</div>
			</div>

			<!-- Users Table -->
			<div class="bg-white border rounded-lg overflow-hidden">
				<div class="px-6 py-4 border-b bg-gray-50">
					<div class="flex justify-between items-center">
						<div>
							<h3 class="text-lg font-semibold text-gray-900">{{ __('Course Enrollment Overview') }} ({{ filteredUsers.length }})</h3>
							<p class="text-sm text-gray-600">{{ __('Course completion status and reminder tracking for all users') }}</p>
						</div>
						<div class="flex items-center space-x-3">
							<FormControl
								v-model="searchTerm"
								:placeholder="__('Search users...')"
								type="text"
								class="w-64"
								@input="filterUsers"
							>
								<template #prefix>
									<Search class="h-4 w-4 text-gray-400" />
								</template>
							</FormControl>
							<Select
								v-model="statusFilter"
								:options="statusFilterOptions"
								:placeholder="__('Filter by status')"
								@change="filterUsers"
							/>
						</div>
					</div>
				</div>

				<div v-if="loading" class="p-8 text-center">
					<div class="animate-spin h-8 w-8 mx-auto mb-4 border-2 border-blue-600 border-t-transparent rounded-full"></div>
					<p class="text-gray-600">{{ __('Loading user data...') }}</p>
				</div>

				<div v-else-if="filteredUsers.length === 0" class="p-8 text-center">
					<Users class="h-12 w-12 mx-auto mb-4 text-gray-400" />
					<p class="text-gray-600">{{ __('No users found') }}</p>
				</div>

				<div v-else class="overflow-x-auto">
					<table class="min-w-full divide-y divide-gray-200">
						<thead class="bg-gray-50">
							<tr>
								<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									{{ __('User') }}
								</th>
								<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									{{ __('Course Status') }}
								</th>
								<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									{{ __('Progress') }}
								</th>
								<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									{{ __('Reminders Sent') }}
								</th>
								<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									{{ __('Days Since Enrolled') }}
								</th>
								<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									{{ __('Actions') }}
								</th>
							</tr>
						</thead>
						<tbody class="bg-white divide-y divide-gray-200">
							<tr v-for="user in paginatedUsers" :key="user.enrollment_id">
								<td class="px-6 py-4 whitespace-nowrap">
									<div class="flex items-center">
										<UserAvatar :user="{ name: user.user_id }" class="mr-3" />
										<div>
											<div class="text-sm font-medium text-gray-900">
												{{ user.user_name }}
											</div>
											<div class="text-sm text-gray-500">
												{{ user.course_title }}
											</div>
											<div class="text-xs text-gray-400">
												{{ user.user_email }}
											</div>
										</div>
									</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									<div class="flex items-center">
										<div v-if="user.completed_on" class="flex items-center">
											<div class="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
											<Badge theme="green" variant="subtle">{{ __('Completed') }}</Badge>
										</div>
										<div v-else class="flex items-center">
											<div class="w-3 h-3 bg-yellow-500 rounded-full mr-2"></div>
											<Badge theme="yellow" variant="subtle">{{ __('In Progress') }}</Badge>
											<AlertTriangle 
												v-if="user.course_reminder_count >= 5" 
												class="h-4 w-4 text-red-600 ml-2" 
												:title="`${user.course_reminder_count} reminders sent`"
											/>
										</div>
									</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
									<div class="flex items-center">
										<div class="w-full bg-gray-200 rounded-full h-2 mr-2">
											<div 
												class="bg-blue-600 h-2 rounded-full" 
												:style="`width: ${user.progress || 0}%`"
											></div>
										</div>
										<span class="text-xs">{{ Math.round(user.progress || 0) }}%</span>
									</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									<div class="flex items-center">
										<Badge 
											:theme="getReminderBadgeTheme(user.course_reminder_count)"
											variant="subtle"
											class="mr-2"
										>
											{{ user.course_reminder_count || 0 }}
										</Badge>
										<div v-if="user.course_reminder_count >= 10" class="flex items-center ml-2">
											<AlertTriangle class="h-4 w-4 text-red-600" />
											<span class="text-xs text-red-600 ml-1">High Alert</span>
										</div>
									</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
									{{ getDaysSinceEnrolled(user.creation) }} days
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
									<div class="flex items-center space-x-2">
										<Button
											variant="outline"
											size="sm"
											@click="sendCourseReminder(user)"
											:disabled="user.completed_on"
										>
											<template #prefix>
												<Send class="h-4 w-4" />
											</template>
											{{ __('Send Reminder') }}
										</Button>
									</div>
								</td>
							</tr>
						</tbody>
					</table>
				</div>

				<!-- Pagination -->
				<div
					v-if="filteredUsers.length > pageSize"
					class="flex items-center justify-between px-6 py-3 border-t"
				>
					<div class="text-sm text-gray-600">
						Showing {{ (currentPage - 1) * pageSize + 1 }}–{{ Math.min(currentPage * pageSize, filteredUsers.length) }} of {{ filteredUsers.length }}
					</div>
					<div class="flex items-center space-x-2">
						<Button
							variant="outline"
							:disabled="currentPage === 1"
							@click="currentPage--"
						>
							{{ __('Previous') }}
						</Button>
						<span class="text-sm text-gray-700">Page {{ currentPage }} of {{ totalPages }}</span>
						<Button
							variant="outline"
							:disabled="currentPage === totalPages"
							@click="currentPage++"
						>
							{{ __('Next') }}
						</Button>
					</div>
				</div>
			</div>
		</div>

		<!-- Users Details Dialog -->
		<Dialog v-model="showUsersDetailsDialog" :options="{ size: 'xl' }">
			<template #body>
				<div class="p-6">
					<div class="flex items-center mb-4">
						<Users class="h-6 w-6 text-blue-600 mr-2" />
						<h3 class="text-lg font-semibold">{{ usersDialogTitle }}</h3>
					</div>
					
					<div class="max-h-96 overflow-y-auto">
						<div v-if="usersDialogData.length === 0" class="text-center text-gray-500 py-8">
							{{ __('No users found in this category') }}
						</div>
						<div v-else class="space-y-3">
							<div 
								v-for="user in usersDialogData" 
								:key="user.enrollment_id"
								class="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
							>
								<div class="flex items-center">
									<UserAvatar :user="{ name: user.user_id }" class="mr-3" />
									<div>
										<div class="font-medium text-gray-900">{{ user.user_name }}</div>
										<div class="text-sm text-gray-600">{{ user.course_title }}</div>
										<div class="text-xs text-gray-500">{{ user.user_email }}</div>
									</div>
								</div>
								<div class="text-right">
									<div v-if="user.completed_on" class="text-sm text-green-600 font-medium">
										{{ formatDateTime(user.completed_on) }}
									</div>
									<div v-else class="text-sm text-yellow-600">
										{{ user.progress || 0 }}% complete
									</div>
								</div>
							</div>
						</div>
					</div>

					<div class="flex justify-end mt-6">
						<Button variant="subtle" @click="showUsersDetailsDialog = false">
							{{ __('Close') }}
						</Button>
					</div>
				</div>
			</template>
		</Dialog>

		<!-- Reminders Details Dialog -->
		<Dialog v-model="showRemindersDetailsDialog" :options="{ size: 'lg' }">
			<template #body>
				<div class="p-6">
					<div class="flex items-center mb-4">
						<Mail class="h-6 w-6 text-purple-600 mr-2" />
						<h3 class="text-lg font-semibold">{{ __('Course Reminder Details') }}</h3>
					</div>
					
					<div class="space-y-4">
						<div class="grid grid-cols-2 gap-4">
							<div class="bg-gray-50 p-4 rounded-lg">
								<p class="text-sm text-gray-600">{{ __('Total Sent') }}</p>
								<p class="text-2xl font-semibold text-purple-600">{{ (kpiData && kpiData.total_course_reminders_sent) || 0 }}</p>
							</div>
							<div class="bg-gray-50 p-4 rounded-lg">
								<p class="text-sm text-gray-600">{{ __('Sent Today') }}</p>
								<p class="text-2xl font-semibold text-blue-600">{{ (kpiData && kpiData.reminders_sent_today) || 0 }}</p>
							</div>
						</div>

						<div class="border rounded-lg p-4">
							<h4 class="font-medium mb-3">{{ __('Reminder Breakdown by Count') }}</h4>
							<div class="space-y-2">
								<div v-for="breakdown in reminderBreakdown" :key="breakdown.count" class="flex justify-between items-center">
									<span class="text-gray-600">{{ breakdown.count }} {{ __('reminders') }}</span>
									<Badge :theme="getReminderBadgeTheme(breakdown.count)" variant="subtle">
										{{ breakdown.users_count }} {{ __('users') }}
									</Badge>
								</div>
							</div>
						</div>
					</div>

					<div class="flex justify-end mt-6">
						<Button variant="subtle" @click="showRemindersDetailsDialog = false">
							{{ __('Close') }}
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
import { computed, onMounted, ref, onUnmounted, watch } from 'vue'
import {
	RefreshCw,
	Users,
	CheckCircle,
	AlertTriangle,
	Mail,
	Send,
	Search,
} from 'lucide-vue-next'
import { sessionStore } from '@/stores/session'
import UserAvatar from '@/components/UserAvatar.vue'

const { user } = sessionStore()

// Reactive data
const kpiData = ref({})
const users = ref([])
const filteredUsers = ref([])
const recentCompletions = ref([])
const reminderBreakdown = ref([])
const loading = ref(true)
const searchTerm = ref('')
const statusFilter = ref(null)
const currentPage = ref(1)
const pageSize = 10

// Dialog states
const showUsersDetailsDialog = ref(false)
const showRemindersDetailsDialog = ref(false)
const usersDialogData = ref([])
const usersDialogTitle = ref('')

// Auto-refresh interval
let refreshInterval = null

// Watch for user authentication changes
watch(
	() => [user.name],
	([newUserName], [oldUserName]) => {
		console.log('User auth state changed:', { newUserName, oldUserName })
		if (newUserName && (!oldUserName)) {
			// User just logged in or session initialized
			console.log('User session initialized, loading data...')
			loadData()
		}
	},
	{ immediate: false }
)

const statusFilterOptions = ref([
	{ label: 'All Status', value: null },
	{ label: 'Completed', value: 'completed' },
	{ label: 'In Progress', value: 'in_progress' },
	{ label: 'High Reminders (5+)', value: 'high_reminders' }
])

const totalPages = computed(() => Math.max(1, Math.ceil(filteredUsers.value.length / pageSize)))
const paginatedUsers = computed(() => {
	const start = (currentPage.value - 1) * pageSize
	return filteredUsers.value.slice(start, start + pageSize)
})

onMounted(() => {
	loadData()
	// Auto-refresh every 30 seconds
	refreshInterval = setInterval(loadData, 30000)
})

onUnmounted(() => {
	if (refreshInterval) {
		clearInterval(refreshInterval)
	}
})

const loadData = async () => {
	loading.value = true
	console.log('Starting data load...')
	console.log('Current user session:', user.name, user.enabled)
	
	try {
		// Load data with individual error handling to prevent one failure from stopping others
		const results = await Promise.allSettled([
			loadKPIData(),
			loadUsers(),
			loadRecentCompletions(),
			loadReminderBreakdown()
		])
		
		// Log any rejected promises for debugging
		results.forEach((result, index) => {
			if (result.status === 'rejected') {
				const functionNames = ['KPI Data', 'Users', 'Recent Completions', 'Reminder Breakdown']
				console.error(`Failed to load ${functionNames[index]}:`, result.reason)
			} else {
				const functionNames = ['KPI Data', 'Users', 'Recent Completions', 'Reminder Breakdown']
				console.log(`Successfully loaded ${functionNames[index]}`)
			}
		})
		
		// Log final state for debugging
		console.log('Final data state:', {
			kpiData: kpiData.value,
			usersCount: users.value.length,
			recentCompletionsCount: recentCompletions.value.length,
			reminderBreakdownCount: reminderBreakdown.value.length
		})
		
		// If critical data (users) failed to load, try again after a short delay
		if (users.value.length === 0 && results[1].status === 'rejected') {
			console.log('Retrying user data load...')
			setTimeout(() => loadUsers(), 1000)
		}
		
	} catch (error) {
		console.error('Failed to load dashboard data:', error)
	} finally {
		loading.value = false
		console.log('Data load completed. Users loaded:', users.value.length)
	}
}

const loadKPIData = async () => {
	try {
		console.log('Loading KPI data...')
		const data = await call('lms.lms.api.get_course_completion_stats')
		console.log('KPI data received:', data)
		kpiData.value = data || {}
		
		// Validate the received data and log any issues
		if (!data || Object.keys(data).length === 0) {
			console.warn('No KPI data received or empty object returned')
		} else {
			console.log('KPI Data loaded successfully:', {
				total_enrolled_users: data.total_enrolled_users,
				completed_courses: data.completed_courses,
				pending_completions: data.pending_completions,
				total_course_reminders_sent: data.total_course_reminders_sent
			})
		}
	} catch (error) {
		console.error('Failed to load KPI data:', error)
		// Set default values to ensure UI doesn't break
		kpiData.value = {
			total_enrolled_users: 0,
			completed_courses: 0,
			pending_completions: 0,
			total_course_reminders_sent: 0,
			reminders_sent_today: 0,
			completion_rate: 0,
			avg_time_to_complete: 0,
			most_active_course: 'N/A',
			avg_reminders_sent: 0
		}
	}
}

// TEMP-DUMMY-DATA: verifying pagination UI, remove before shipping
const generateMockUsers = () => Array.from({ length: 25 }, (_, i) => ({
	enrollment_id: `mock-enrollment-${i + 1}`,
	user_id: `user${i + 1}@example.com`,
	user_name: `Mock User ${i + 1}`,
	user_email: `user${i + 1}@example.com`,
	course_title: `Mock Course ${(i % 4) + 1}`,
	progress: (i % 5) * 25,
	completed_on: i % 3 === 0 ? new Date(Date.now() - i * 86400000).toISOString() : null,
	course_reminder_count: i % 12,
	creation: new Date(Date.now() - i * 5 * 86400000).toISOString(),
}))

const loadUsers = async () => {
	try {
		const data = generateMockUsers() // TEMP-DUMMY-DATA
		users.value = data || []
		filteredUsers.value = data || []
		currentPage.value = 1
	} catch (error) {
		console.error('Failed to load users:', error)
		users.value = []
		filteredUsers.value = []
	}
}

const loadRecentCompletions = async () => {
	try {
		const data = await call('lms.lms.api.get_recent_course_completions')
		recentCompletions.value = data || []
	} catch (error) {
		console.error('Failed to load recent completions:', error)
		recentCompletions.value = []
	}
}

const loadReminderBreakdown = async () => {
	try {
		const data = await call('lms.lms.api.get_course_reminder_breakdown')
		reminderBreakdown.value = data || []
	} catch (error) {
		console.error('Failed to load reminder breakdown:', error)
		reminderBreakdown.value = []
	}
}

const filterUsers = () => {
	let filtered = users.value

	if (searchTerm.value) {
		const search = searchTerm.value.toLowerCase()
		filtered = filtered.filter(user => 
			user.user_name.toLowerCase().includes(search) ||
			user.course_title.toLowerCase().includes(search) ||
			user.user_email.toLowerCase().includes(search)
		)
	}

	if (statusFilter.value) {
		if (statusFilter.value === 'completed') {
			filtered = filtered.filter(u => u.completed_on)
		} else if (statusFilter.value === 'in_progress') {
			filtered = filtered.filter(u => !u.completed_on)
		} else if (statusFilter.value === 'high_reminders') {
			filtered = filtered.filter(u => (u.course_reminder_count || 0) >= 5)
		}
	}

	filteredUsers.value = filtered
	currentPage.value = 1
}

const showUsersDialog = (type) => {
	let data = []
	let title = ''

	switch (type) {
		case 'total':
			data = users.value
			title = 'All Enrolled Users'
			break
		case 'completed':
			data = users.value.filter(u => u.completed_on)
			title = 'Users Who Completed Courses'
			break
		case 'pending':
			data = users.value.filter(u => !u.completed_on)
			title = 'Users With Pending Course Completions'
			break
	}

	usersDialogData.value = data
	usersDialogTitle.value = title
	showUsersDetailsDialog.value = true
}

const showRemindersDialog = () => {
	showRemindersDetailsDialog.value = true
}

const sendCourseReminder = async (user) => {
	try {
		await call('lms.lms.user.send_manual_course_reminder', {
			enrollment_id: user.enrollment_id
		})
		alert('Course reminder sent successfully!')
		// Refresh data after sending reminder
		await loadData()
	} catch (error) {
		console.error('Failed to send course reminder:', error)
		alert('Failed to send course reminder: ' + error.message)
	}
}

const sendCourseReminders = async () => {
	try {
		const result = await call('lms.lms.user.send_daily_course_reminders')
		alert(`Course reminders sent: ${result.count} users notified`)
		// Refresh data after sending bulk reminders
		await loadData()
	} catch (error) {
		console.error('Failed to send course reminders:', error)
		alert('Failed to send course reminders: ' + error.message)
	}
}

const refreshData = async () => {
	await loadData()
}

const formatDateTime = (dateString) => {
	if (!dateString) return ''
	return new Date(dateString).toLocaleString()
}

const getDaysSinceEnrolled = (dateString) => {
	if (!dateString) return 0
	const now = new Date()
	const date = new Date(dateString)
	const diffMs = now - date
	return Math.floor(diffMs / (1000 * 60 * 60 * 24))
}

const getReminderBadgeTheme = (count) => {
	if (!count || count === 0) return 'gray'
	if (count <= 2) return 'blue'
	if (count <= 5) return 'yellow'
	if (count <= 10) return 'orange'
	return 'red'
}

const breadcrumbs = computed(() => [
	{
		label: 'LMS',
		route: { name: 'Courses' },
	},
	{
		label: 'Course Completion Management',
		route: { name: 'RemindersManagementDashboard' },
	},
])

usePageMeta(() => {
	return {
		title: 'Course Completion Management Dashboard',
		description: 'Track user course completion activities and manage reminders'
	}
})
</script> 