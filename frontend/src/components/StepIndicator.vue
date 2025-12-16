<template>
  <div class="w-full overflow-hidden">
    <!-- Progress Bar -->
    <div class="mb-6">
      <div class="flex items-center justify-between mb-2">
        <span class="text-sm font-medium text-gray-700">
          Step {{ currentStep }} of {{ totalSteps }}
        </span>
        <span class="text-sm font-medium text-gray-700">
          {{ progressPercentage }}% Complete
        </span>
      </div>
      <div class="w-full bg-gray-200 rounded-full h-2">
        <div
          class="bg-gray-900 h-2 rounded-full transition-all duration-300 ease-in-out"
          :style="{ width: `${progressPercentage}%` }"
        ></div>
      </div>
    </div>

    <!-- Step Indicators -->
    <div class="flex items-start justify-between relative">
      <div
        v-for="(step, index) in steps"
        :key="step.id"
        class="flex flex-col items-center flex-1 relative z-10 min-w-0"
        :class="{ 'cursor-pointer': allowNavigation && index + 1 <= currentStep }"
        @click="handleStepClick(index + 1)"
      >
        <!-- Step Circle -->
        <div
          class="relative flex items-center justify-center w-10 h-10 rounded-full border-2 transition-all duration-200"
          :class="getStepCircleClasses(index + 1)"
        >
          <!-- Step Number or Checkmark -->
          <template v-if="index + 1 < currentStep">
            <!-- Completed step - show checkmark -->
            <svg class="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
            </svg>
          </template>
          <template v-else-if="index + 1 === currentStep">
            <!-- Current step - show step number -->
            <span class="text-sm font-semibold">{{ index + 1 }}</span>
          </template>
          <template v-else>
            <!-- Future step - show step number -->
            <span class="text-sm font-semibold">{{ index + 1 }}</span>
          </template>
        </div>

        <!-- Step Label -->
        <div class="mt-3 text-center px-1">
          <p
            class="text-sm font-medium transition-colors duration-200 break-words"
            :class="getStepLabelClasses(index + 1)"
          >
            {{ step.title }}
          </p>
          <p
            class="text-xs mt-1 transition-colors duration-200 break-words hidden sm:block"
            :class="getStepDescriptionClasses(index + 1)"
          >
            {{ step.description }}
          </p>
        </div>

        <!-- Connector Line -->
        <div
          v-if="index < steps.length - 1"
          class="absolute top-5 left-[calc(50%+20px)] right-[calc(-50%+20px)] h-0.5 transition-colors duration-200 z-0"
          :class="getConnectorClasses(index + 1)"
        ></div>
      </div>
    </div>

    <!-- Step Status Messages -->
    <div v-if="showStatusMessages" class="mt-6">
      <div
        v-for="(step, index) in steps"
        :key="`status-${step.id}`"
        v-show="index + 1 === currentStep"
        class="text-center px-2"
      >
        <p class="text-sm text-gray-600">{{ step.statusMessage || step.description }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  currentStep: {
    type: Number,
    default: 1
  },
  totalSteps: {
    type: Number,
    default: 4
  },
  steps: {
    type: Array,
    default: () => [
      {
        id: 1,
        title: 'Certify',
        description: 'Review and certify documents',
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
    ]
  },
  allowNavigation: {
    type: Boolean,
    default: false
  },
  showStatusMessages: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['step-click'])

const progressPercentage = computed(() => {
  if (props.totalSteps === 0) return 0
  return Math.round((props.currentStep / props.totalSteps) * 100)
})

const getStepCircleClasses = (stepNumber) => {
  if (stepNumber < props.currentStep) {
    // Completed step
    return 'bg-gray-900 border-gray-900 text-white'
  } else if (stepNumber === props.currentStep) {
    // Current step
    return 'bg-white border-gray-900 text-gray-900'
  } else {
    // Future step
    return 'bg-white border-gray-300 text-gray-500'
  }
}

const getStepLabelClasses = (stepNumber) => {
  if (stepNumber < props.currentStep) {
    // Completed step
    return 'text-gray-900'
  } else if (stepNumber === props.currentStep) {
    // Current step
    return 'text-gray-900'
  } else {
    // Future step
    return 'text-gray-500'
  }
}

const getStepDescriptionClasses = (stepNumber) => {
  if (stepNumber < props.currentStep) {
    // Completed step
    return 'text-gray-600'
  } else if (stepNumber === props.currentStep) {
    // Current step
    return 'text-gray-600'
  } else {
    // Future step
    return 'text-gray-400'
  }
}

const getConnectorClasses = (stepNumber) => {
  if (stepNumber < props.currentStep) {
    // Line between completed steps
    return 'bg-gray-900'
  } else {
    // Line to future steps
    return 'bg-gray-300'
  }
}

const handleStepClick = (stepNumber) => {
  if (props.allowNavigation && stepNumber <= props.currentStep) {
    emit('step-click', stepNumber)
  }
}
</script>