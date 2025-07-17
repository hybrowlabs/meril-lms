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
				<Button variant="solid" @click="sendManualReminders">
					<template #prefix>
						<Send class="h-4 w-4" />
					</template>
					{{ __('Send Reminders') }}
				</Button>
			</div>
		</header>

		<div class="p-5">
			<!-- Main KPI Cards -->
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
				<!-- Total Distributors -->
				<div class="bg-white border rounded-lg p-6 cursor-pointer hover:shadow-md transition-shadow" @click="showDistributorsDialog('total')">
					<div class="flex items-center justify-between">
						<div>
							<p class="text-sm text-gray-600">{{ __('Total Distributors') }}</p>
							<p class="text-2xl font-semibold text-gray-900">
								{{ kpiData.total_distributors || 0 }}
							</p>
						</div>
						<Users class="h-8 w-8 text-blue-600" />
					</div>
				</div>

				<!-- Logged In Distributors -->
				<div class="bg-white border rounded-lg p-6 cursor-pointer hover:shadow-md transition-shadow" @click="showDistributorsDialog('logged_in')">
					<div class="flex items-center justify-between">
						<div>
							<p class="text-sm text-gray-600">{{ __('Logged In') }}</p>
							<p class="text-2xl font-semibold text-green-600">
								{{ kpiData.logged_in_distributors || 0 }}
							</p>
							<p class="text-xs text-gray-500">
								{{ Math.round((kpiData.logged_in_distributors / kpiData.total_distributors) * 100) || 0 }}% success rate
							</p>
						</div>
						<CheckCircle class="h-8 w-8 text-green-600" />
					</div>
				</div>

				<!-- Never Logged In -->
				<div class="bg-white border rounded-lg p-6 cursor-pointer hover:shadow-md transition-shadow" @click="showDistributorsDialog('never_logged_in')">
					<div class="flex items-center justify-between">
						<div>
							<p class="text-sm text-gray-600">{{ __('Never Logged In') }}</p>
							<p class="text-2xl font-semibold text-red-600">
								{{ kpiData.never_logged_in || 0 }}
							</p>
							<p class="text-xs text-gray-500">
								{{ kpiData.avg_reminders_sent || 0 }} avg reminders sent
							</p>
						</div>
						<AlertTriangle class="h-8 w-8 text-red-600" />
					</div>
				</div>

				<!-- Total Reminders Sent -->
				<div class="bg-white border rounded-lg p-6 cursor-pointer hover:shadow-md transition-shadow" @click="showRemindersDialog">
					<div class="flex items-center justify-between">
						<div>
							<p class="text-sm text-gray-600">{{ __('Total Reminders') }}</p>
							<p class="text-2xl font-semibold text-purple-600">
								{{ kpiData.total_reminders_sent || 0 }}
							</p>
							<p class="text-xs text-gray-500">
								{{ kpiData.reminders_sent_today || 0 }} sent today
							</p>
						</div>
						<Mail class="h-8 w-8 text-purple-600" />
					</div>
				</div>
			</div>

			<!-- Detailed Analytics Cards -->
			<div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
				<!-- Login Activity Timeline -->
				<div class="bg-white border rounded-lg p-6">
					<h3 class="text-lg font-semibold text-gray-900 mb-4">{{ __('Recent Login Activity') }}</h3>
					<div class="space-y-3 max-h-64 overflow-y-auto">
						<div v-if="recentLogins.length === 0" class="text-center text-gray-500 py-4">
							{{ __('No recent login activity') }}
						</div>
						<div v-for="login in recentLogins" :key="login.distributor_id" class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
							<div class="flex items-center">
								<div class="w-3 h-3 bg-green-500 rounded-full mr-3"></div>
								<div>
									<p class="font-medium text-gray-900">{{ login.distributor_name }}</p>
									<p class="text-sm text-gray-600">{{ login.company_name }}</p>
								</div>
							</div>
							<div class="text-right">
								<p class="text-sm text-gray-900">{{ formatDateTime(login.last_login_date) }}</p>
								<p class="text-xs text-gray-500">
									<span v-if="login.is_first_login" class="text-green-600 font-medium">First login!</span>
									<span v-else>Regular login</span>
								</p>
							</div>
						</div>
					</div>
				</div>

				<!-- Reminder Statistics -->
				<div class="bg-white border rounded-lg p-6">
					<h3 class="text-lg font-semibold text-gray-900 mb-4">{{ __('Reminder Effectiveness') }}</h3>
					<div class="space-y-4">
						<div class="flex justify-between items-center">
							<span class="text-gray-600">{{ __('Response Rate') }}</span>
							<span class="text-lg font-semibold text-green-600">{{ kpiData.response_rate || 0 }}%</span>
						</div>
						<div class="flex justify-between items-center">
							<span class="text-gray-600">{{ __('Avg Time to First Login') }}</span>
							<span class="text-lg font-semibold text-blue-600">{{ kpiData.avg_time_to_login || 0 }} days</span>
						</div>
						<div class="flex justify-between items-center">
							<span class="text-gray-600">{{ __('Most Effective Day') }}</span>
							<span class="text-lg font-semibold text-purple-600">{{ kpiData.most_effective_day || 'N/A' }}</span>
						</div>
					</div>
				</div>
			</div>

			<!-- Distributors Table -->
			<div class="bg-white border rounded-lg overflow-hidden">
				<div class="px-6 py-4 border-b bg-gray-50">
					<div class="flex justify-between items-center">
						<div>
							<h3 class="text-lg font-semibold text-gray-900">{{ __('Distributor Status Overview') }}</h3>
							<p class="text-sm text-gray-600">{{ __('Login status and reminder tracking for all distributors') }}</p>
						</div>
						<div class="flex items-center space-x-3">
							<FormControl
								v-model="searchTerm"
								:placeholder="__('Search distributors...')"
								type="text"
								class="w-64"
								@input="filterDistributors"
							>
								<template #prefix>
									<Search class="h-4 w-4 text-gray-400" />
								</template>
							</FormControl>
							<Select
								v-model="statusFilter"
								:options="statusFilterOptions"
								:placeholder="__('Filter by status')"
								@change="filterDistributors"
							/>
						</div>
					</div>
				</div>

				<div v-if="loading" class="p-8 text-center">
					<div class="animate-spin h-8 w-8 mx-auto mb-4 border-2 border-blue-600 border-t-transparent rounded-full"></div>
					<p class="text-gray-600">{{ __('Loading distributor data...') }}</p>
				</div>

				<div v-else-if="filteredDistributors.length === 0" class="p-8 text-center">
					<Users class="h-12 w-12 mx-auto mb-4 text-gray-400" />
					<p class="text-gray-600">{{ __('No distributors found') }}</p>
				</div>

				<div v-else class="overflow-x-auto">
					<table class="min-w-full divide-y divide-gray-200">
						<thead class="bg-gray-50">
							<tr>
								<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									{{ __('Distributor') }}
								</th>
								<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									{{ __('Login Status') }}
								</th>
								<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									{{ __('Last Login') }}
								</th>
								<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									{{ __('Reminders Sent') }}
								</th>
								<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									{{ __('Days Since Created') }}
								</th>
								<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
									{{ __('Actions') }}
								</th>
							</tr>
						</thead>
						<tbody class="bg-white divide-y divide-gray-200">
							<tr v-for="distributor in filteredDistributors" :key="distributor.name">
								<td class="px-6 py-4 whitespace-nowrap">
									<div class="flex items-center">
										<UserAvatar :user="{ name: distributor.user_id }" class="mr-3" />
										<div>
											<div class="text-sm font-medium text-gray-900">
												{{ distributor.atendee_name }}
											</div>
											<div class="text-sm text-gray-500">
												{{ distributor.distributor_company_name }}
											</div>
											<div class="text-xs text-gray-400">
												{{ distributor.distributor_email_address }}
											</div>
										</div>
									</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									<div class="flex items-center">
										<div v-if="distributor.first_login_date" class="flex items-center">
											<div class="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
											<Badge theme="green" variant="subtle">{{ __('Logged In') }}</Badge>
										</div>
										<div v-else class="flex items-center">
											<div class="w-3 h-3 bg-red-500 rounded-full mr-2"></div>
											<Badge theme="red" variant="subtle">{{ __('Never Logged In') }}</Badge>
											<AlertTriangle 
												v-if="distributor.login_reminder_count >= 5" 
												class="h-4 w-4 text-red-600 ml-2" 
												:title="`${distributor.login_reminder_count} reminders sent`"
											/>
										</div>
									</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
									<div v-if="distributor.last_login_date">
										<div>{{ formatDateTime(distributor.last_login_date) }}</div>
										<div class="text-xs text-gray-500">
											{{ getTimeDifference(distributor.last_login_date) }} ago
										</div>
									</div>
									<div v-else class="text-gray-400">{{ __('Never') }}</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									<div class="flex items-center">
										<Badge 
											:theme="getReminderBadgeTheme(distributor.login_reminder_count)"
											variant="subtle"
											class="mr-2"
										>
											{{ distributor.login_reminder_count || 0 }}
										</Badge>
										<div v-if="distributor.login_reminder_count >= 10" class="flex items-center ml-2">
											<AlertTriangle class="h-4 w-4 text-red-600" />
											<span class="text-xs text-red-600 ml-1">High Alert</span>
										</div>
									</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
									{{ getDaysSinceCreated(distributor.credentials_sent_date) }} days
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
									<div class="flex items-center space-x-2">
										<Button
											variant="outline"
											size="sm"
											@click="sendManualReminder(distributor)"
											:disabled="distributor.first_login_date"
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
			</div>
		</div>

		<!-- Distributors Details Dialog -->
		<Dialog v-model="showDistributorsDetailsDialog" :options="{ size: 'xl' }">
			<template #body>
				<div class="p-6">
					<div class="flex items-center mb-4">
						<Users class="h-6 w-6 text-blue-600 mr-2" />
						<h3 class="text-lg font-semibold">{{ distributorsDialogTitle }}</h3>
					</div>
					
					<div class="max-h-96 overflow-y-auto">
						<div v-if="distributorsDialogData.length === 0" class="text-center text-gray-500 py-8">
							{{ __('No distributors found in this category') }}
						</div>
						<div v-else class="space-y-3">
							<div 
								v-for="distributor in distributorsDialogData" 
								:key="distributor.name"
								class="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
							>
								<div class="flex items-center">
									<UserAvatar :user="{ name: distributor.user_id }" class="mr-3" />
									<div>
										<div class="font-medium text-gray-900">{{ distributor.atendee_name }}</div>
										<div class="text-sm text-gray-600">{{ distributor.distributor_company_name }}</div>
										<div class="text-xs text-gray-500">{{ distributor.distributor_email_address }}</div>
									</div>
								</div>
								<div class="text-right">
									<div v-if="distributor.first_login_date" class="text-sm text-green-600 font-medium">
										{{ formatDateTime(distributor.first_login_date) }}
									</div>
									<div v-else class="text-sm text-red-600">
										{{ distributor.login_reminder_count || 0 }} reminders sent
									</div>
								</div>
							</div>
						</div>
					</div>

					<div class="flex justify-end mt-6">
						<Button variant="subtle" @click="showDistributorsDetailsDialog = false">
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
						<h3 class="text-lg font-semibold">{{ __('Reminder Details') }}</h3>
					</div>
					
					<div class="space-y-4">
						<div class="grid grid-cols-2 gap-4">
							<div class="bg-gray-50 p-4 rounded-lg">
								<p class="text-sm text-gray-600">{{ __('Total Sent') }}</p>
								<p class="text-2xl font-semibold text-purple-600">{{ kpiData.total_reminders_sent || 0 }}</p>
							</div>
							<div class="bg-gray-50 p-4 rounded-lg">
								<p class="text-sm text-gray-600">{{ __('Sent Today') }}</p>
								<p class="text-2xl font-semibold text-blue-600">{{ kpiData.reminders_sent_today || 0 }}</p>
							</div>
						</div>

						<div class="border rounded-lg p-4">
							<h4 class="font-medium mb-3">{{ __('Reminder Breakdown by Count') }}</h4>
							<div class="space-y-2">
								<div v-for="breakdown in reminderBreakdown" :key="breakdown.count" class="flex justify-between items-center">
									<span class="text-gray-600">{{ breakdown.count }} {{ __('reminders') }}</span>
									<Badge :theme="getReminderBadgeTheme(breakdown.count)" variant="subtle">
										{{ breakdown.distributors_count }} {{ __('distributors') }}
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
import { computed, onMounted, ref, onUnmounted } from 'vue'
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
import router from '../router'

const { user, isLoggedIn } = sessionStore()

// Reactive data
const kpiData = ref({})
const distributors = ref([])
const filteredDistributors = ref([])
const recentLogins = ref([])
const reminderBreakdown = ref([])
const loading = ref(true)
const searchTerm = ref('')
const statusFilter = ref(null)

// Dialog states
const showDistributorsDetailsDialog = ref(false)
const showRemindersDetailsDialog = ref(false)
const distributorsDialogData = ref([])
const distributorsDialogTitle = ref('')

// Auto-refresh interval
let refreshInterval = null

const statusFilterOptions = ref([
	{ label: 'All Status', value: null },
	{ label: 'Logged In', value: 'logged_in' },
	{ label: 'Never Logged In', value: 'never_logged_in' },
	{ label: 'High Reminders (5+)', value: 'high_reminders' }
])

onMounted(() => {
	checkPermissions()
	loadData()
	// Auto-refresh every 30 seconds
	refreshInterval = setInterval(loadData, 30000)
})

onUnmounted(() => {
	if (refreshInterval) {
		clearInterval(refreshInterval)
	}
})

const checkPermissions = () => {
	if (!isLoggedIn || !user.roles?.some(role => ['System Manager', 'Administrator'].includes(role))) {
		router.push({ name: 'NotPermitted' })
	}
}

const loadData = async () => {
	loading.value = true
	try {
		await Promise.all([
			loadKPIData(),
			loadDistributors(),
			loadRecentLogins(),
			loadReminderBreakdown()
		])
	} catch (error) {
		console.error('Failed to load dashboard data:', error)
	} finally {
		loading.value = false
	}
}

const loadKPIData = async () => {
	try {
		const data = await call('lms.lms.api.get_distributor_login_stats')
		kpiData.value = data
	} catch (error) {
		console.error('Failed to load KPI data:', error)
	}
}

const loadDistributors = async () => {
	try {
		const data = await call('lms.lms.api.get_distributors_with_login_status')
		distributors.value = data
		filteredDistributors.value = data
	} catch (error) {
		console.error('Failed to load distributors:', error)
	}
}

const loadRecentLogins = async () => {
	try {
		const data = await call('lms.lms.api.get_recent_distributor_logins')
		recentLogins.value = data
	} catch (error) {
		console.error('Failed to load recent logins:', error)
	}
}

const loadReminderBreakdown = async () => {
	try {
		const data = await call('lms.lms.api.get_reminder_breakdown')
		reminderBreakdown.value = data
	} catch (error) {
		console.error('Failed to load reminder breakdown:', error)
	}
}

const filterDistributors = () => {
	let filtered = distributors.value

	if (searchTerm.value) {
		const search = searchTerm.value.toLowerCase()
		filtered = filtered.filter(distributor => 
			distributor.atendee_name.toLowerCase().includes(search) ||
			distributor.distributor_company_name.toLowerCase().includes(search) ||
			distributor.distributor_email_address.toLowerCase().includes(search)
		)
	}

	if (statusFilter.value) {
		if (statusFilter.value === 'logged_in') {
			filtered = filtered.filter(d => d.first_login_date)
		} else if (statusFilter.value === 'never_logged_in') {
			filtered = filtered.filter(d => !d.first_login_date)
		} else if (statusFilter.value === 'high_reminders') {
			filtered = filtered.filter(d => (d.login_reminder_count || 0) >= 5)
		}
	}

	filteredDistributors.value = filtered
}

const showDistributorsDialog = (type) => {
	let data = []
	let title = ''

	switch (type) {
		case 'total':
			data = distributors.value
			title = 'All Distributors'
			break
		case 'logged_in':
			data = distributors.value.filter(d => d.first_login_date)
			title = 'Distributors Who Have Logged In'
			break
		case 'never_logged_in':
			data = distributors.value.filter(d => !d.first_login_date)
			title = 'Distributors Who Never Logged In'
			break
	}

	distributorsDialogData.value = data
	distributorsDialogTitle.value = title
	showDistributorsDetailsDialog.value = true
}

const showRemindersDialog = () => {
	showRemindersDetailsDialog.value = true
}

const sendManualReminder = async (distributor) => {
	try {
		await call('lms.lms.user.send_manual_login_reminder', {
			distributor_id: distributor.name
		})
		alert('Reminder sent successfully!')
		await loadData()
	} catch (error) {
		console.error('Failed to send reminder:', error)
		alert('Failed to send reminder: ' + error.message)
	}
}

const sendManualReminders = async () => {
	try {
		const result = await call('lms.lms.user.send_daily_login_reminders')
		alert(`Reminders sent: ${result.count} distributors notified`)
		await loadData()
	} catch (error) {
		console.error('Failed to send reminders:', error)
		alert('Failed to send reminders: ' + error.message)
	}
}

const refreshData = async () => {
	await loadData()
}

const formatDateTime = (dateString) => {
	if (!dateString) return ''
	return new Date(dateString).toLocaleString()
}

const getTimeDifference = (dateString) => {
	if (!dateString) return ''
	const now = new Date()
	const date = new Date(dateString)
	const diffMs = now - date
	const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
	const diffDays = Math.floor(diffHours / 24)
	
	if (diffDays > 0) return `${diffDays} days`
	return `${diffHours} hours`
}

const getDaysSinceCreated = (dateString) => {
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
		label: 'Reminders Management',
		route: { name: 'RemindersManagementDashboard' },
	},
])

usePageMeta(() => {
	return {
		title: 'Reminders Management Dashboard',
		description: 'Track distributor login activities and manage reminders'
	}
})
</script> 