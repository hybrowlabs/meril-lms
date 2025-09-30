<template>
  <div class="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center p-4">
    <div class="w-full max-w-4xl max-h-[90vh] overflow-y-auto bg-white rounded-lg shadow-xl">
      <!-- Modal Header -->
      <div class="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 rounded-t-lg">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-xl font-semibold text-gray-900">
              {{ distributor.distributor_company_name || 'Distributor Details' }}
            </h2>
            <p class="text-sm text-gray-600 mt-1">
              Course: {{ distributor.course || 'N/A' }}
            </p>
          </div>
          <button
            @click="$emit('close')"
            class="text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 rounded-lg p-2"
            aria-label="Close modal"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      <div class="px-6 py-6 space-y-6">
        <!-- Distributor Information -->
        <div class="bg-gray-50 border border-gray-200 rounded-lg p-6">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Distributor Information</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700">Company Name</label>
              <p class="mt-1 text-sm text-gray-900">{{ distributor.distributor_company_name || 'N/A' }}</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">Contact Person</label>
              <p class="mt-1 text-sm text-gray-900">{{ distributor.attendee_name || 'N/A' }}</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">Division</label>
              <p class="mt-1 text-sm text-gray-900">{{ distributor.division || 'General' }}</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">Course</label>
              <p class="mt-1 text-sm text-gray-900">{{ distributor.course || 'N/A' }}</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">Status</label>
              <span :class="getStatusBadgeClass(distributor.status)" class="mt-1 inline-block">
                {{ getStatusLabel(distributor.status) }}
              </span>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">Last Updated</label>
              <p class="mt-1 text-sm text-gray-900">{{ formatDateTime(distributor.last_updated) }}</p>
            </div>
          </div>
        </div>

        <!-- Progress Overview -->
        <div class="bg-white border border-gray-200 rounded-lg p-6">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Progress Overview</h3>
          <div class="space-y-4">
            <!-- Overall Progress -->
            <div>
              <div class="flex items-center justify-between mb-2">
                <span class="text-sm font-medium text-gray-700">Overall Progress</span>
                <span class="text-sm font-medium text-gray-900">{{ distributor.progress }}%</span>
              </div>
              <div class="w-full bg-gray-200 rounded-full h-3">
                <div
                  class="bg-gray-900 h-3 rounded-full transition-all duration-300"
                  :style="{ width: `${distributor.progress}%` }"
                ></div>
              </div>
            </div>

            <!-- Document Progress -->
            <div v-if="distributor.documents && distributor.documents.length > 0">
              <h4 class="text-sm font-medium text-gray-700 mb-3">Document Status</h4>
              <div class="space-y-2">
                <div
                  v-for="document in distributor.documents"
                  :key="document.name"
                  class="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg"
                >
                  <div class="flex items-center">
                    <div
                      class="w-3 h-3 rounded-full mr-3"
                      :class="document.status === 'uploaded' ? 'bg-green-500' : 'bg-yellow-500'"
                    ></div>
                    <span class="text-sm text-gray-900">{{ document.name }}</span>
                  </div>
                  <span
                    class="text-xs px-2 py-1 rounded-full"
                    :class="document.status === 'uploaded' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'"
                  >
                    {{ document.status === 'uploaded' ? 'Uploaded' : 'Pending' }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Document Timeline -->
        <div class="bg-white border border-gray-200 rounded-lg p-6">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Document Timeline</h3>
          <div class="space-y-4">
            <!-- Timeline items -->
            <div
              v-for="(event, index) in mockTimeline"
              :key="index"
              class="flex items-start"
            >
              <div class="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center mr-4"
                   :class="event.completed ? 'bg-green-100' : 'bg-gray-100'"
              >
                <svg v-if="event.completed" class="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                </svg>
                <div v-else class="w-2 h-2 bg-gray-400 rounded-full"></div>
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center justify-between">
                  <p class="text-sm font-medium text-gray-900">{{ event.title }}</p>
                  <p class="text-sm text-gray-500">{{ formatDate(event.date) }}</p>
                </div>
                <p class="text-sm text-gray-600 mt-1">{{ event.description }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Available Documents -->
        <div v-if="distributor.documents && distributor.documents.length > 0" class="bg-white border border-gray-200 rounded-lg p-6">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-medium text-gray-900">Available Documents</h3>
            <Button
              theme="gray"
              variant="outline"
              @click="downloadAllDocuments"
              :disabled="isDownloadingAll"
            >
              <Spinner v-if="isDownloadingAll" class="w-4 h-4 mr-2" />
              <svg v-else class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Download All
            </Button>
          </div>

          <div class="space-y-3">
            <div
              v-for="document in distributor.documents"
              :key="document.name"
              class="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div class="flex items-center">
                <div class="flex-shrink-0 w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mr-3">
                  <svg class="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zm0 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V8zm0 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1v-2z" clip-rule="evenodd" />
                  </svg>
                </div>
                <div>
                  <p class="text-sm font-medium text-gray-900">{{ document.name }}</p>
                  <p class="text-xs text-gray-500">
                    {{ document.status === 'uploaded' ? 'Uploaded document' : 'System document' }}
                  </p>
                </div>
              </div>
              <Button
                theme="gray"
                variant="outline"
                size="sm"
                @click="downloadDocument(document)"
                :disabled="downloadingDocs.has(document.name)"
              >
                <Spinner v-if="downloadingDocs.has(document.name)" class="w-4 h-4 mr-1" />
                <svg v-else class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M7 10l5 5m0 0l5-5m-5 5V4" />
                </svg>
                Download
              </Button>
            </div>
          </div>
        </div>

        <!-- Additional Actions -->
        <div class="bg-gray-50 border border-gray-200 rounded-lg p-6">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Actions</h3>
          <div class="flex flex-wrap gap-3">
            <Button theme="gray" variant="outline" @click="sendReminder">
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              Send Reminder
            </Button>
            <Button theme="gray" variant="outline" @click="exportDistributorData">
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Export Data
            </Button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Button, Spinner, toast } from 'frappe-ui'

const props = defineProps({
  distributor: {
    type: Object,
    required: true
  }
})

defineEmits(['close'])

const downloadingDocs = ref(new Set())
const isDownloadingAll = ref(false)

const mockTimeline = computed(() => [
  {
    title: 'Course Enrollment',
    description: 'Distributor enrolled in the compliance course',
    date: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString(),
    completed: true
  },
  {
    title: 'Course Completed',
    description: 'Successfully completed all course modules',
    date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
    completed: props.distributor.status !== 'not_started'
  },
  {
    title: 'Documents Generated',
    description: 'Compliance documents were generated and made available',
    date: new Date(Date.now() - 6 * 24 * 60 * 60 * 1000).toISOString(),
    completed: props.distributor.status !== 'not_started'
  },
  {
    title: 'Documents Submitted',
    description: 'All required documents were uploaded and submitted',
    date: props.distributor.last_updated,
    completed: props.distributor.status === 'completed'
  }
])

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

const formatDateTime = (dateString) => {
  if (!dateString) return 'N/A'
  try {
    return new Date(dateString).toLocaleString()
  } catch {
    return 'Invalid Date'
  }
}

const downloadDocument = async (document) => {
  if (downloadingDocs.value.has(document.name)) return

  try {
    downloadingDocs.value.add(document.name)

    // Simulate download
    await new Promise(resolve => setTimeout(resolve, 1500))

    toast.success(`${document.name} downloaded successfully`)
  } catch (error) {
    console.error('Download error:', error)
    toast.error(`Failed to download ${document.name}`)
  } finally {
    downloadingDocs.value.delete(document.name)
  }
}

const downloadAllDocuments = async () => {
  if (isDownloadingAll.value) return

  try {
    isDownloadingAll.value = true

    // Simulate bulk download
    await new Promise(resolve => setTimeout(resolve, 3000))

    toast.success('All documents downloaded successfully')
  } catch (error) {
    console.error('Bulk download error:', error)
    toast.error('Failed to download documents')
  } finally {
    isDownloadingAll.value = false
  }
}

const sendReminder = () => {
  // Simulate sending reminder
  toast.success(`Reminder sent to ${props.distributor.distributor_company_name}`)
}

const exportDistributorData = () => {
  const data = {
    'Distributor Company': props.distributor.distributor_company_name,
    'Contact Person': props.distributor.attendee_name,
    'Course': props.distributor.course,
    'Division': props.distributor.division,
    'Status': getStatusLabel(props.distributor.status),
    'Progress': `${props.distributor.progress}%`,
    'Last Updated': formatDateTime(props.distributor.last_updated),
    'Documents': props.distributor.documents?.map(d => d.name).join(', ') || 'None'
  }

  const csv = Object.entries(data).map(([key, value]) => `"${key}","${value}"`).join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `distributor-${props.distributor.distributor_company_name?.replace(/\s+/g, '-') || 'data'}.csv`
  link.click()
  URL.revokeObjectURL(link.href)

  toast.success('Distributor data exported successfully')
}
</script>