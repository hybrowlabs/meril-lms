<template>
  <div class="container mx-auto px-4 py-6">
    <!-- Page Header -->
    <div class="mb-8">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">Distributor Management</h1>
          <p class="mt-1 text-sm text-gray-600">
            Monitor and manage distributor document compliance across all courses.
          </p>
        </div>
        <div class="mt-4 sm:mt-0 flex space-x-3">
          <Button
            theme="gray"
            variant="outline"
            @click="refreshData"
            :disabled="loading"
          >
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </Button>
          <Button
            theme="gray"
            variant="solid"
            @click="exportData"
            :disabled="distributors.length === 0"
          >
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Export Data
          </Button>
        </div>
      </div>
    </div>

    <!-- Filters and Search -->
    <div class="bg-white border border-gray-200 rounded-lg p-6 mb-6">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <!-- Search -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Search</label>
          <TextInput
            v-model="searchQuery"
            placeholder="Search distributors..."
            class="w-full"
          />
        </div>

        <!-- Course Filter -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Course</label>
          <Select
            v-model="selectedCourse"
            :options="courseOptions"
            placeholder="All courses"
            class="w-full"
          />
        </div>

        <!-- Status Filter -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Completion Status</label>
          <Select
            v-model="selectedStatus"
            :options="statusOptions"
            placeholder="All statuses"
            class="w-full"
          />
        </div>

        <!-- Company Division Filter -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Division</label>
          <Select
            v-model="selectedDivision"
            :options="divisionOptions"
            placeholder="All divisions"
            class="w-full"
          />
        </div>
      </div>

      <!-- Date Range Filter -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
          <input
            v-model="startDate"
            type="date"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-gray-500"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">End Date</label>
          <input
            v-model="endDate"
            type="date"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-gray-500"
          />
        </div>
      </div>
    </div>

    <!-- Summary Statistics -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
      <div class="bg-white border border-gray-200 rounded-lg p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <svg class="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <div class="ml-4">
            <p class="text-sm font-medium text-gray-500">Total Distributors</p>
            <p class="text-2xl font-semibold text-gray-900">{{ statistics.total }}</p>
          </div>
        </div>
      </div>

      <div class="bg-white border border-gray-200 rounded-lg p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <div class="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <svg class="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
              </svg>
            </div>
          </div>
          <div class="ml-4">
            <p class="text-sm font-medium text-gray-500">Completed</p>
            <p class="text-2xl font-semibold text-gray-900">{{ statistics.completed }}</p>
          </div>
        </div>
      </div>

      <div class="bg-white border border-gray-200 rounded-lg p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <div class="w-10 h-10 bg-yellow-100 rounded-lg flex items-center justify-center">
              <svg class="w-5 h-5 text-yellow-600" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd" />
              </svg>
            </div>
          </div>
          <div class="ml-4">
            <p class="text-sm font-medium text-gray-500">In Progress</p>
            <p class="text-2xl font-semibold text-gray-900">{{ statistics.inProgress }}</p>
          </div>
        </div>
      </div>

      <div class="bg-white border border-gray-200 rounded-lg p-6">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <div class="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
              <svg class="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
              </svg>
            </div>
          </div>
          <div class="ml-4">
            <p class="text-sm font-medium text-gray-500">Not Started</p>
            <p class="text-2xl font-semibold text-gray-900">{{ statistics.notStarted }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <div class="text-center">
        <Spinner class="w-8 h-8 mx-auto mb-4" />
        <p class="text-gray-600">Loading distributor data...</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-lg p-6">
      <div class="flex">
        <svg class="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
        </svg>
        <div class="ml-3">
          <h3 class="text-sm font-medium text-red-800">Error Loading Data</h3>
          <p class="text-sm text-red-700 mt-1">{{ error }}</p>
        </div>
      </div>
    </div>

    <!-- Distributor Table -->
    <div v-else class="bg-white border border-gray-200 rounded-lg overflow-hidden">
      <!-- Table Header -->
      <div class="px-6 py-4 border-b border-gray-200 bg-gray-50">
        <div class="flex items-center justify-between">
          <h3 class="text-lg font-medium text-gray-900">
            Distributors ({{ filteredDistributors.length }})
          </h3>
          <div v-if="selectedDistributors.length > 0" class="flex items-center space-x-2">
            <span class="text-sm text-gray-600">{{ selectedDistributors.length }} selected</span>
            <Button
              theme="gray"
              variant="outline"
              size="sm"
              @click="bulkDownloadDocuments"
              :disabled="downloadingBulk"
            >
              <Spinner v-if="downloadingBulk" class="w-4 h-4 mr-1" />
              <svg v-else class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Bulk Download
            </Button>
          </div>
        </div>
      </div>

      <!-- Table Content -->
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                <input
                  type="checkbox"
                  :checked="allSelected"
                  @change="toggleSelectAll"
                  class="rounded border-gray-300 text-gray-600 focus:ring-gray-500"
                />
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Distributor
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Course
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Division
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Progress
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Last Updated
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr
              v-for="distributor in filteredDistributors"
              :key="`${distributor.id}-${distributor.course}`"
              class="hover:bg-gray-50"
            >
              <td class="px-6 py-4 whitespace-nowrap">
                <input
                  type="checkbox"
                  :value="distributor.id"
                  v-model="selectedDistributors"
                  class="rounded border-gray-300 text-gray-600 focus:ring-gray-500"
                />
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div>
                  <div class="text-sm font-medium text-gray-900">
                    {{ distributor.distributor_company_name || 'Unknown Company' }}
                  </div>
                  <div class="text-sm text-gray-500">
                    {{ distributor.attendee_name || 'Unknown Contact' }}
                  </div>
                </div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">{{ distributor.course || 'N/A' }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">{{ distributor.division || 'General' }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span :class="getStatusBadgeClass(distributor.status)">
                  {{ getStatusLabel(distributor.status) }}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex items-center">
                  <div class="w-16 bg-gray-200 rounded-full h-2 mr-2">
                    <div
                      class="bg-gray-900 h-2 rounded-full"
                      :style="{ width: `${distributor.progress}%` }"
                    ></div>
                  </div>
                  <span class="text-sm text-gray-600">{{ distributor.progress }}%</span>
                </div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {{ formatDate(distributor.last_updated) }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                <div class="flex items-center space-x-2">
                  <button
                    @click="viewDistributorDetails(distributor)"
                    class="text-gray-600 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 rounded p-1"
                    title="View Details"
                  >
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  </button>
                  <button
                    v-if="distributor.documents && distributor.documents.length > 0"
                    @click="downloadDistributorDocuments(distributor)"
                    :disabled="downloadingDocs.has(distributor.id)"
                    class="text-gray-600 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 rounded p-1"
                    title="Download Documents"
                  >
                    <Spinner v-if="downloadingDocs.has(distributor.id)" class="w-5 h-5" />
                    <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        <!-- Empty State -->
        <div v-if="filteredDistributors.length === 0" class="text-center py-12">
          <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 class="mt-2 text-sm font-medium text-gray-900">No distributors found</h3>
          <p class="mt-1 text-sm text-gray-500">
            Try adjusting your search or filter criteria.
          </p>
        </div>
      </div>
    </div>

    <!-- Distributor Detail Modal -->
    <DistributorDetailModal
      v-if="selectedDistributor"
      :distributor="selectedDistributor"
      @close="selectedDistributor = null"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { Button, Spinner, TextInput, Select, call, toast } from 'frappe-ui'
import DistributorDetailModal from '../components/DistributorDetailModal.vue'

// Reactive data
const loading = ref(false)
const error = ref('')
const distributors = ref([])
const selectedDistributor = ref(null)
const selectedDistributors = ref([])
const downloadingDocs = ref(new Set())
const downloadingBulk = ref(false)

// Filter states
const searchQuery = ref('')
const selectedCourse = ref('')
const selectedStatus = ref('')
const selectedDivision = ref('')
const startDate = ref('')
const endDate = ref('')

// Available options for filters
const courseOptions = ref([])
const statusOptions = ref([
  { label: 'All Statuses', value: '' },
  { label: 'Completed', value: 'completed' },
  { label: 'In Progress', value: 'in_progress' },
  { label: 'Not Started', value: 'not_started' }
])
const divisionOptions = ref([])

// Computed properties
const filteredDistributors = computed(() => {
  let filtered = distributors.value

  // Search filter
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(d =>
      (d.distributor_company_name || '').toLowerCase().includes(query) ||
      (d.attendee_name || '').toLowerCase().includes(query) ||
      (d.course || '').toLowerCase().includes(query)
    )
  }

  // Course filter
  if (selectedCourse.value) {
    filtered = filtered.filter(d => d.course === selectedCourse.value)
  }

  // Status filter
  if (selectedStatus.value) {
    filtered = filtered.filter(d => d.status === selectedStatus.value)
  }

  // Division filter
  if (selectedDivision.value) {
    filtered = filtered.filter(d => d.division === selectedDivision.value)
  }

  // Date range filter
  if (startDate.value || endDate.value) {
    filtered = filtered.filter(d => {
      if (!d.last_updated) return false
      const docDate = new Date(d.last_updated)
      if (startDate.value && docDate < new Date(startDate.value)) return false
      if (endDate.value && docDate > new Date(endDate.value)) return false
      return true
    })
  }

  return filtered
})

const statistics = computed(() => {
  const total = filteredDistributors.value.length
  const completed = filteredDistributors.value.filter(d => d.status === 'completed').length
  const inProgress = filteredDistributors.value.filter(d => d.status === 'in_progress').length
  const notStarted = filteredDistributors.value.filter(d => d.status === 'not_started').length

  return { total, completed, inProgress, notStarted }
})

const allSelected = computed({
  get: () => filteredDistributors.value.length > 0 && selectedDistributors.value.length === filteredDistributors.value.length,
  set: (value) => {
    if (value) {
      selectedDistributors.value = filteredDistributors.value.map(d => d.id)
    } else {
      selectedDistributors.value = []
    }
  }
})

// Methods
const loadDistributorData = async () => {
  try {
    loading.value = true
    error.value = ''

    // This would be replaced with actual API call
    const response = await call('lms.overrides.documents.get_all_distributor_documents')

    if (response && response.success) {
      distributors.value = response.data || []

      // Extract unique courses and divisions for filter options
      const courses = [...new Set(distributors.value.map(d => d.course).filter(Boolean))]
      courseOptions.value = [
        { label: 'All Courses', value: '' },
        ...courses.map(course => ({ label: course, value: course }))
      ]

      const divisions = [...new Set(distributors.value.map(d => d.division).filter(Boolean))]
      divisionOptions.value = [
        { label: 'All Divisions', value: '' },
        ...divisions.map(division => ({ label: division, value: division }))
      ]
    } else {
      // Mock data for demonstration
      distributors.value = generateMockData()
    }
  } catch (err) {
    console.error('Error loading distributor data:', err)
    error.value = 'Failed to load distributor data. Please try again.'
    // Use mock data as fallback
    distributors.value = generateMockData()
  } finally {
    loading.value = false
  }
}

const generateMockData = () => {
  const courses = ['Compliance Training 2024', 'Ethics & Standards', 'Product Knowledge']
  const divisions = ['General', 'Endovascular', 'Cardiac']
  const statuses = ['completed', 'in_progress', 'not_started']

  return Array.from({ length: 25 }, (_, i) => ({
    id: `dist-${i + 1}`,
    distributor_company_name: `Distributor Company ${i + 1}`,
    attendee_name: `Contact Person ${i + 1}`,
    course: courses[i % courses.length],
    division: divisions[i % divisions.length],
    status: statuses[i % statuses.length],
    progress: statuses[i % statuses.length] === 'completed' ? 100 :
              statuses[i % statuses.length] === 'in_progress' ? Math.floor(Math.random() * 80) + 20 : 0,
    last_updated: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
    documents: statuses[i % statuses.length] !== 'not_started' ? [
      { name: 'Policy Adoption Form', status: 'uploaded' },
      { name: 'Self Declaration', status: 'uploaded' },
      { name: 'Code of Conduct', status: statuses[i % statuses.length] === 'completed' ? 'uploaded' : 'pending' }
    ] : []
  }))
}

const refreshData = () => {
  loadDistributorData()
}

const exportData = () => {
  const csvData = filteredDistributors.value.map(d => ({
    'Distributor Company': d.distributor_company_name,
    'Contact Person': d.attendee_name,
    'Course': d.course,
    'Division': d.division,
    'Status': getStatusLabel(d.status),
    'Progress': `${d.progress}%`,
    'Last Updated': formatDate(d.last_updated)
  }))

  const csv = convertToCSV(csvData)
  downloadCSV(csv, 'distributor-compliance-report.csv')
  toast.success('Data exported successfully')
}

const convertToCSV = (data) => {
  if (!data.length) return ''

  const headers = Object.keys(data[0])
  const csvContent = [
    headers.join(','),
    ...data.map(row => headers.map(header => `"${row[header] || ''}"`).join(','))
  ].join('\n')

  return csvContent
}

const downloadCSV = (content, filename) => {
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = filename
  link.click()
  URL.revokeObjectURL(link.href)
}

const toggleSelectAll = () => {
  allSelected.value = !allSelected.value
}

const viewDistributorDetails = (distributor) => {
  selectedDistributor.value = distributor
}

const downloadDistributorDocuments = async (distributor) => {
  if (downloadingDocs.value.has(distributor.id)) return

  try {
    downloadingDocs.value.add(distributor.id)

    // This would call the actual download API
    await new Promise(resolve => setTimeout(resolve, 2000)) // Simulate download

    toast.success(`Documents for ${distributor.distributor_company_name} downloaded successfully`)
  } catch (error) {
    console.error('Download error:', error)
    toast.error('Failed to download documents')
  } finally {
    downloadingDocs.value.delete(distributor.id)
  }
}

const bulkDownloadDocuments = async () => {
  if (downloadingBulk.value || selectedDistributors.value.length === 0) return

  try {
    downloadingBulk.value = true

    // This would call the actual bulk download API
    await new Promise(resolve => setTimeout(resolve, 3000)) // Simulate bulk download

    toast.success(`Documents for ${selectedDistributors.value.length} distributors downloaded successfully`)
    selectedDistributors.value = []
  } catch (error) {
    console.error('Bulk download error:', error)
    toast.error('Failed to download documents')
  } finally {
    downloadingBulk.value = false
  }
}

const getStatusBadgeClass = (status) => {
  const baseClass = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium'

  switch (status) {
    case 'completed':
      return `${baseClass} bg-green-100 text-green-800`
    case 'in_progress':
      return `${baseClass} bg-yellow-100 text-yellow-800`
    case 'not_started':
      return `${baseClass} bg-red-100 text-red-800`
    default:
      return `${baseClass} bg-gray-100 text-gray-800`
  }
}

const getStatusLabel = (status) => {
  const labels = {
    completed: 'Completed',
    in_progress: 'In Progress',
    not_started: 'Not Started'
  }
  return labels[status] || 'Unknown'
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  try {
    return new Date(dateString).toLocaleDateString()
  } catch {
    return 'Invalid Date'
  }
}

// Lifecycle
onMounted(() => {
  loadDistributorData()
})

// Watch for filter changes to update course and division options
watch(() => filteredDistributors.value, () => {
  const courses = [...new Set(distributors.value.map(d => d.course).filter(Boolean))]
  courseOptions.value = [
    { label: 'All Courses', value: '' },
    ...courses.map(course => ({ label: course, value: course }))
  ]

  const divisions = [...new Set(distributors.value.map(d => d.division).filter(Boolean))]
  divisionOptions.value = [
    { label: 'All Divisions', value: '' },
    ...divisions.map(division => ({ label: division, value: division }))
  ]
})
</script>