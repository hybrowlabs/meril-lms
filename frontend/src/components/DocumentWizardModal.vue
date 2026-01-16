<template>
  <div v-if="state.isOpen" class="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center p-2 sm:p-4">
    <div :class="['w-full max-w-4xl max-h-[90vh] bg-white rounded-lg shadow-xl flex flex-col', { 'shake-animation': isShaking }]">
      <!-- Modal Header -->
      <div class="flex-shrink-0 bg-white border-b border-gray-200 px-4 sm:px-6 py-4 rounded-t-lg">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-xl font-semibold text-gray-900">
              {{ stepTitle }}
            </h2>
            <p class="text-sm text-gray-600 mt-1">
              {{ state.courseName ? `Course: ${state.courseName}` : 'Document Compliance Workflow' }}
            </p>
          </div>
          <!-- Hide close button if in force certification mode and not certified -->
          <button
            v-if="!isCloseBlocked"
            @click="handleCloseAttempt"
            class="text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 rounded-lg p-2"
            aria-label="Close modal"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Certification Warning Message -->
      <div v-if="showCertifyWarning" class="mx-4 sm:mx-6 mt-4">
        <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div class="flex">
            <svg class="w-5 h-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
            </svg>
            <div class="ml-3">
              <h3 class="text-sm font-medium text-yellow-800">Certification Required</h3>
              <p class="text-sm text-yellow-700 mt-1">Please click the "Certify" button below to complete your certification before closing this dialog.</p>
            </div>
            <button @click="showCertifyWarning = false" class="ml-auto text-yellow-400 hover:text-yellow-600">
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
              </svg>
            </button>
          </div>
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
            :total-steps="totalSteps"
            :steps="stepDefinitions"
            :allow-navigation="true"
            @step-click="goToStep"
          />
        </div>

        <!-- Step Content -->
        <div class="mt-8">
          <!-- Step 1: Certification (includes compliance officer nomination) -->
          <CertificationStep
            v-if="certificationStepId && state.currentStep === certificationStepId"
            :user-role="state.userRole"
            :declaration-info="state.declarationInfo"
            :certification-data="state.certification"
            :course="state.courseName"
            :compliance-officer-name="state.complianceOfficerName"
            :document-type="state.documentType || 'Meril Distributor Compliance Policy Adoption Form'"
            @certification-complete="handleCertificationComplete"
            @officer-nominated="handleOfficerNominated"
            @validation-changed="handleOfficerValidationChanged"
          />

          <!-- Step 2: Download -->
          <DownloadStep
            v-if="downloadStepId && state.currentStep === downloadStepId"
            :required-documents="state.requiredDocuments"
            :certification-data="state.certification"
            :course-name="state.courseName"
            :compliance-officer-name="state.complianceOfficerName"
            :completed-downloads="state.downloads.completedDownloads"
            :user-role="state.userRole"
            @download-complete="handleDownloadComplete"
          />

          <!-- Step 3: Upload -->
          <UploadStep
            v-if="uploadStepId && state.currentStep === uploadStepId"
            :required-documents="state.requiredDocuments"
            :uploaded-documents="state.uploadedDocuments"
            :current-document="currentDocumentToUpload"
            :course-name="state.courseName"
            :upload-progress="state.uploads.uploadProgress"
            :user-role="state.userRole"
            @upload-complete="handleUploadComplete"
            @upload-progress="handleUploadProgress"
          />

          <!-- Step 4: Completion -->
          <CompletionStep
            v-if="completionStepId && state.currentStep === completionStepId"
            :uploaded-documents="state.uploadedDocumentsList"
            :documents-list="state.documentsList"
            :required-documents="state.requiredDocuments"
            :course-name="state.courseName"
            :course-documents-record-id="state.courseDocumentsRecordId"
            :doctype="state.doctype"
            :user-role="state.userRole"
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
              v-if="state.currentStep < totalSteps"
              @click="nextStep"
              :disabled="!canProceedToNextStep"
              class="px-4 py-2 text-sm font-medium text-white bg-gray-900 rounded-lg hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ nextButtonLabel }}
            </button>
            <button
              v-else
              @click="handleCloseAttempt"
              :disabled="isCloseBlocked"
              class="px-4 py-2 text-sm font-medium text-white bg-gray-900 rounded-lg hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
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
import { computed, ref } from 'vue'
import { Spinner } from 'frappe-ui'
import StepIndicator from './StepIndicator.vue'
import CertificationStep from './steps/CertificationStep.vue'
import DownloadStep from './steps/DownloadStep.vue'
import UploadStep from './steps/UploadStep.vue'
import CompletionStep from './steps/CompletionStep.vue'
import {
  state,
  totalSteps,
  stepDefinitions,
  certificationStepId,
  downloadStepId,
  uploadStepId,
  completionStepId,
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

// Shake animation and warning state
const isShaking = ref(false)
const showCertifyWarning = ref(false)

// Check if user is employee and hasn't certified yet
const isEmployeeNotCertified = computed(() => {
  return state.userRole === 'Employee' && !state.certification.isCompleted
})

// Check if close is completely blocked (force certification mode)
const isCloseBlocked = computed(() => {
  return state.forceCertificationMode && !state.certification.isCompleted
})

// Handle close attempt - show warning for employees who haven't certified
const handleCloseAttempt = () => {
  // If in force certification mode and not certified, block completely
  if (isCloseBlocked.value) {
    isShaking.value = true
    showCertifyWarning.value = true
    setTimeout(() => {
      isShaking.value = false
    }, 500)
    return
  }

  // If employee and not certified, show warning and shake
  if (isEmployeeNotCertified.value) {
    isShaking.value = true
    showCertifyWarning.value = true
    setTimeout(() => {
      isShaking.value = false
    }, 500)
    return
  }

  // Otherwise, allow closing
  closeModal()
}

const currentStepMeta = computed(() => stepDefinitions.value.find(step => step.id === state.currentStep) || null)
const stepTitle = computed(() => currentStepMeta.value?.title || 'Document Workflow')
const nextButtonLabel = computed(() => currentStepMeta.value?.nextButtonText || 'Next')

const handleOfficerNominated = (officerData) => {
  // This will be handled by the store
  state.complianceOfficerName = officerData.name
  state.complianceOfficerValid = officerData.isValid
}

const handleOfficerValidationChanged = (isValid) => {
  state.complianceOfficerValid = isValid
}

const handleCertificationComplete = async (certificationData) => {
  await completeCertification(certificationData.name, certificationData.date)
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

<style scoped>
/* Shake animation for modal when employee tries to close without certifying */
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-8px); }
  20%, 40%, 60%, 80% { transform: translateX(8px); }
}

.shake-animation {
  animation: shake 0.5s ease-in-out;
}
</style>
