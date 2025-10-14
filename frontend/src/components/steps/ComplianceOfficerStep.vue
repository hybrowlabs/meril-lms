<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="text-center">
      <h3 class="text-lg font-medium text-gray-900 mb-2">
        Nominate Compliance Officer
      </h3>
      <p class="text-sm text-gray-600">
        Please nominate the compliance officer for your organization
      </p>
    </div>

    <!-- Compliance Officer Form -->
    <div class="max-w-md mx-auto">
      <div class="bg-white border border-gray-200 rounded-lg p-6">
        <label for="compliance-officer-name" class="block text-sm font-medium text-gray-700 mb-2">
          Compliance Officer Name <span class="text-red-500">*</span>
        </label>
        <TextInput
          id="compliance-officer-name"
          v-model="localComplianceOfficerName"
          type="text"
          placeholder="Nominate Compliance Officer name for your organization"
          class="w-full"
          required
          :min-length="3"
          @input="validateName"
          @blur="validateName"
        />
        <p v-if="nameError" class="text-sm text-red-600 mt-1">{{ nameError }}</p>

        <!-- Helper text -->
        <p class="text-xs text-gray-500 mt-2">
          This person will be designated as the compliance officer for your organization in all related documents.
        </p>
      </div>
    </div>

    <!-- Summary of what happens next -->
    <div class="max-w-md mx-auto">
      <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div class="flex">
          <svg class="w-5 h-5 text-blue-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
          </svg>
          <div class="ml-3">
            <h4 class="text-sm font-medium text-blue-800">Next Steps</h4>
            <p class="text-sm text-blue-700 mt-1">
              After nomination, you'll review compliance documents, download them for signing, and upload the completed forms.
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { TextInput } from 'frappe-ui'

const props = defineProps({
  complianceOfficerName: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['officer-nominated', 'validation-changed'])

const localComplianceOfficerName = ref(props.complianceOfficerName || '')
const nameError = ref('')

const validateName = () => {
  nameError.value = ''

  if (!localComplianceOfficerName.value?.trim()) {
    nameError.value = 'Compliance officer name is required'
    return false
  }

  if (localComplianceOfficerName.value.trim().length < 3) {
    nameError.value = 'Compliance officer name must be at least 3 characters'
    return false
  }

  // Check for valid name format (letters, spaces, common punctuation)
  const namePattern = /^[a-zA-Z\s\-'.,]+$/
  if (!namePattern.test(localComplianceOfficerName.value.trim())) {
    nameError.value = 'Please enter a valid name (letters, spaces, and basic punctuation only)'
    return false
  }

  return true
}

const isValid = () => {
  return validateName()
}

// Watch for changes and emit validation status
watch(localComplianceOfficerName, (newValue) => {
  const valid = validateName()
  emit('officer-nominated', {
    name: newValue?.trim() || '',
    isValid: valid
  })
  emit('validation-changed', valid)
}, { immediate: true })

// Watch for external prop changes
watch(() => props.complianceOfficerName, (newValue) => {
  if (newValue !== localComplianceOfficerName.value) {
    localComplianceOfficerName.value = newValue
  }
})

onMounted(() => {
  // Emit initial validation state
  const valid = validateName()
  emit('officer-nominated', {
    name: localComplianceOfficerName.value?.trim() || '',
    isValid: valid
  })
  emit('validation-changed', valid)
})

// Expose validation method for parent component
defineExpose({
  isValid,
  validateName
})
</script>

<style scoped>
/* Any additional styles can be added here if needed */
</style>