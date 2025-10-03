<template>
  <div v-if="state.isOpen" class="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center p-2 sm:p-4">
    <div class="w-full max-w-4xl max-h-[90vh] bg-white rounded-lg shadow-xl flex flex-col">
      <!-- Modal Header -->
      <div class="flex-shrink-0 bg-white border-b border-gray-200 px-4 sm:px-6 py-4 rounded-t-lg">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-xl font-semibold text-gray-900">
              {{ getStepTitle() }}
            </h2>
            <p class="text-sm text-gray-600 mt-1">
              {{ state.courseName ? `Course: ${state.courseName}` : 'Document Compliance Workflow' }}
            </p>
          </div>
          <button
            @click="closeModal"
            class="text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 rounded-lg p-2"
            aria-label="Close modal"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Error Display -->
      <div v-if="state.errors.general" class="mx-4 sm:mx-6 mt-4">
        <div class="bg-red-50 border border-red-200 rounded-lg p-4">
          <div class="flex">
            <svg class="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
            </svg>
            <div class="ml-3">
              <h3 class="text-sm font-medium text-red-800">Error</h3>
              <p class="text-sm text-red-700 mt-1">{{ state.errors.general }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Loading Overlay -->
      <div v-if="state.loading.initialization" class="flex items-center justify-center p-12">
        <div class="text-center">
          <Spinner class="w-8 h-8 mx-auto mb-4" />
          <p class="text-gray-600">Initializing workflow...</p>
        </div>
      </div>

      <!-- Main Content -->
      <div v-else class="flex-1 overflow-y-auto px-4 sm:px-6 py-4 sm:py-6">
        <!-- Step Indicator with proper spacing -->
        <div class="relative mb-6">
          <StepIndicator
            :current-step="state.currentStep"
            :total-steps="state.totalSteps"
            :steps="stepDefinitions"
            :allow-navigation="true"
            @step-click="goToStep"
          />
        </div>

        <!-- Step Content -->
        <div class="mt-8">
          <!-- Step 1: Certification -->
          <CertificationStep
            v-if="state.currentStep === 1"
            :user-role="state.userRole"
            :declaration-info="state.declarationInfo"
            :certification-data="state.certification"
            :course="state.courseName"
            :document-type="state.documentType || 'Meril Distributor Compliance Policy Adoption Form'"
            @certification-complete="handleCertificationComplete"
          />

          <!-- Step 2: Download -->
          <DownloadStep
            v-else-if="state.currentStep === 2"
            :required-documents="state.requiredDocuments"
            :certification-data="state.certification"
            :course-name="state.courseName"
            :completed-downloads="state.downloads.completedDownloads"
            @download-complete="handleDownloadComplete"
          />

          <!-- Step 3: Upload -->
          <UploadStep
            v-else-if="state.currentStep === 3"
            :required-documents="state.requiredDocuments"
            :uploaded-documents="state.uploadedDocuments"
            :current-document="currentDocumentToUpload"
            :course-name="state.courseName"
            :upload-progress="state.uploads.uploadProgress"
            @upload-complete="handleUploadComplete"
            @upload-progress="handleUploadProgress"
          />

          <!-- Step 4: Completion -->
          <CompletionStep
            v-else-if="state.currentStep === 4"
            :uploaded-documents="state.uploadedDocumentsList"
            :documents-list="state.documentsList"
            :course-name="state.courseName"
            :course-documents-record-id="state.courseDocumentsRecordId"
            :doctype="state.doctype"
          />
        </div>

        <!-- Navigation Buttons -->
        <div class="flex justify-between items-center mt-8 pt-6 border-t border-gray-200">
          <button
            v-if="state.currentStep > 1"
            @click="previousStep"
            class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
          >
            Previous
          </button>
          <div v-else></div>

          <div class="flex space-x-3">
            <button
              v-if="state.currentStep < state.totalSteps"
              @click="nextStep"
              :disabled="!canProceedToNextStep"
              class="px-4 py-2 text-sm font-medium text-white bg-gray-900 rounded-lg hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ getNextButtonText() }}
            </button>
            <button
              v-else
              @click="closeModal"
              class="px-4 py-2 text-sm font-medium text-white bg-gray-900 rounded-lg hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
            >
              Done
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { Spinner } from 'frappe-ui'
import StepIndicator from './StepIndicator.vue'
import CertificationStep from './steps/CertificationStep.vue'
import DownloadStep from './steps/DownloadStep.vue'
import UploadStep from './steps/UploadStep.vue'
import CompletionStep from './steps/CompletionStep.vue'
import {
  state,
  currentDocumentToUpload,
  canProceedToNextStep,
  closeModal,
  nextStep,
  previousStep,
  goToStep,
  completeCertification,
  markDownloadCompleted,
  markDocumentUploaded,
  setUploadProgress
} from '../stores/document-workflow.js'

const stepDefinitions = computed(() => [
  {
    id: 1,
    title: 'Certify',
    description: 'Review and certify documents',
    statusMessage: state.userRole === 'Employee'
      ? 'Please review the Employee Declaration and provide your information.'
      : 'Please review the compliance documents and provide your certification.'
  },
  {
    id: 2,
    title: 'Download',
    description: 'Download required documents',
    statusMessage: 'Download the generated documents for signing and completion.'
  },
  {
    id: 3,
    title: 'Upload',
    description: 'Upload completed documents',
    statusMessage: 'Upload your signed and completed documents.'
  },
  {
    id: 4,
    title: 'Complete',
    description: 'Process completed',
    statusMessage: 'All documents have been successfully processed.'
  }
])

const getStepTitle = () => {
  const titles = {
    1: 'Document Certification',
    2: 'Download Documents',
    3: 'Upload Documents',
    4: 'Process Complete'
  }
  return titles[state.currentStep] || 'Document Workflow'
}

const getNextButtonText = () => {
  const texts = {
    1: 'Proceed to Download',
    2: 'Proceed to Upload',
    3: 'Complete Process'
  }
  return texts[state.currentStep] || 'Next'
}

const handleCertificationComplete = (certificationData) => {
  completeCertification(certificationData.name, certificationData.date)
}

const handleDownloadComplete = (documentName) => {
  markDownloadCompleted(documentName)
}

const handleUploadComplete = (documentName) => {
  markDocumentUploaded(documentName)
}

const handleUploadProgress = (documentName, progress) => {
  setUploadProgress(documentName, progress)
}
</script>