<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="text-center">
      <h3 class="text-lg font-medium text-gray-900 mb-2">
        {{ getHeaderTitle() }}
      </h3>
      <p class="text-sm text-gray-600">
        {{ getHeaderDescription() }}
      </p>
    </div>

    <!-- Declaration Content -->
    <div class="max-w-3xl mx-auto">
      <!-- Distributor Declaration -->
      <div v-if="userRole === 'Distributor'" class="space-y-6">
        <!-- Policy Adoption Form Declaration -->
        <div v-if="showDeclaration('Meril Distributor Compliance Policy Adoption Form')" class="bg-gray-50 border border-gray-200 rounded-lg p-6">
          <h4 class="text-center font-semibold mb-4">
            Meril Distributor - Compliance Policy Adoption Form
          </h4>
          <div class="bg-white border-2 border-dotted border-gray-300 rounded-lg p-4 max-h-60 overflow-y-auto text-sm space-y-3">
            <p class="text-right">
              {{ currentDateTime }}
            </p>
            <p class="text-justify">
              We {{ declarationInfo?.distributor_company_name || 'Company Name' }}, being the Distributor of Meril {{ declarationInfo?.meril_company_table?.[0]?.meril_company_name || 'Company' }} do hereby certify that we have willingly adopted attached Meril Distributor Compliance Policy as our own Compliance Policy with effect from {{ currentDate }} and declare to abide by the same.
            </p>
            <p class="text-justify">
              All employees, partners, directors, proprietor of our organization are expected to observe and adhere to this Policy.
            </p>
            <p class="text-justify font-semibold underline">
              Nomination of Compliance Officer:
            </p>
            <p class="text-justify">
              {{ certificationData.name || 'Name' }} is nominated as Compliance Officer of our organization with effect from {{ currentDate }}
            </p>
            <div class="mt-6 space-y-1">
              <p class="text-justify">Authorized representative of {{ declarationInfo?.distributor_company_name || 'Company Name' }}</p>
              <p class="text-justify">Name: {{ declarationInfo?.attendee_name || 'Name' }}</p>
              <p class="text-justify">Title: {{ declarationInfo?.designation || 'Designation' }}</p>
              <p class="text-justify">Email Id: {{ declarationInfo?.distributor_email_address || 'Email' }}</p>
              <p class="text-justify">Contact number: {{ declarationInfo?.distributor_contact_number || 'Contact' }}</p>
              <p class="text-justify">
                Sign and Seal: <span>&lt;Compliance officer nominee name&gt;</span>
              </p>
            </div>
          </div>
        </div>

        <!-- Self Declaration -->
        <div v-if="showDeclaration('Distributor Self Declaration')" class="bg-gray-50 border border-gray-200 rounded-lg p-6">
          <h4 class="text-center font-semibold mb-4">
            Distributor Self Declaration
          </h4>
          <div class="bg-white border-2 border-dotted border-gray-300 rounded-lg p-4 max-h-60 overflow-y-auto text-sm space-y-3">
            <p class="text-justify">
              This is to declare that we {{ declarationInfo?.distributor_company_name || 'Company Name' }}, have reviewed and understood the Meril Distributor Compliance Policy and will adhere to all its provisions.
            </p>
            <p class="text-justify">
              We confirm that we will:
            </p>
            <ul class="list-disc pl-6 space-y-1">
              <li>Comply with all applicable laws and regulations</li>
              <li>Maintain ethical business practices</li>
              <li>Report any violations or concerns</li>
              <li>Cooperate with compliance reviews and audits</li>
            </ul>
            <div class="mt-6 space-y-1">
              <p class="text-justify">Authorized representative of {{ declarationInfo?.distributor_company_name || 'Company Name' }}</p>
              <p class="text-justify">Name: {{ declarationInfo?.attendee_name || 'Name' }}</p>
              <p class="text-justify">Title: {{ declarationInfo?.designation || 'Designation' }}</p>
              <p class="text-justify">Date: {{ currentDate }}</p>
            </div>
          </div>
        </div>

        <!-- Code of Conduct -->
        <div v-if="showDeclaration('Meril Distributor Compliance Code of Conduct')" class="bg-gray-50 border border-gray-200 rounded-lg p-6">
          <h4 class="text-center font-semibold mb-4">
            Meril Distributor Compliance Code of Conduct
          </h4>
          <div class="bg-white border-2 border-dotted border-gray-300 rounded-lg p-4 max-h-60 overflow-y-auto text-sm space-y-3">
            <p class="text-justify">
              We {{ declarationInfo?.distributor_company_name || 'Company Name' }} acknowledge and agree to abide by the Meril Distributor Compliance Code of Conduct.
            </p>
            <p class="text-justify">
              We understand and will comply with:
            </p>
            <ol class="list-decimal pl-6 space-y-1">
              <li>Anti Bribery and Anti Corruption policies</li>
              <li>Fair business practices</li>
              <li>Confidentiality and data protection</li>
              <li>Conflict of interest policies</li>
              <li>Product quality and safety standards</li>
            </ol>
            <div class="mt-6 space-y-1">
              <p class="text-justify">Authorized representative of {{ declarationInfo?.distributor_company_name || 'Company Name' }}</p>
              <p class="text-justify">Name: {{ declarationInfo?.attendee_name || 'Name' }}</p>
              <p class="text-justify">Title: {{ declarationInfo?.designation || 'Designation' }}</p>
              <p class="text-justify">Date: {{ currentDate }}</p>
            </div>
          </div>
        </div>

        <!-- Ethical Practices Declaration -->
        <div v-if="showDeclaration('Distributor Declaration - Ethical Practices & Compliance')" class="bg-gray-50 border border-gray-200 rounded-lg p-6">
          <h4 class="text-center font-semibold mb-4">
            Distributor Declaration - Ethical Practices & Compliance
          </h4>
          <div class="bg-white border-2 border-dotted border-gray-300 rounded-lg p-4 max-h-60 overflow-y-auto text-sm space-y-3">
            <p class="text-justify">
              I hereby declare that {{ declarationInfo?.distributor_company_name || 'Company Name' }} has undergone and understood training provided on Ethical Practices and Compliance.
            </p>
            <p class="text-justify">
              We acknowledge and accept the duty to comply with:
            </p>
            <ul class="list-disc pl-6 space-y-1">
              <li>All procedural frameworks developed by Meril</li>
              <li>Ethical operation guidelines</li>
              <li>NPPA norms and trade regulations</li>
              <li>International compliance standards</li>
            </ul>
            <p class="text-justify">
              We certify that we are not currently in violation of any compliance policies.
            </p>
            <div class="mt-6 space-y-1">
              <p class="text-justify">Authorized representative of {{ declarationInfo?.distributor_company_name || 'Company Name' }}</p>
              <p class="text-justify">Name: {{ declarationInfo?.attendee_name || 'Name' }}</p>
              <p class="text-justify">Title: {{ declarationInfo?.designation || 'Designation' }}</p>
              <p class="text-justify">Date: {{ currentDate }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Employee Declaration -->
      <div v-else-if="userRole === 'Employee'" class="bg-gray-50 border border-gray-200 rounded-lg p-6">
        <h4 class="text-center font-semibold mb-4">
          Employee Declaration - Ethical Practices & Compliance
        </h4>
        <div class="bg-white border-2 border-dotted border-gray-300 rounded-lg p-4 max-h-60 overflow-y-auto text-sm space-y-3">
          <p class="text-justify">
            I hereby declare that I have undergone and understood training provided on Ethical Practices and compliance. As a responsible employee of Meril, I acknowledge and accept the duty to comply with the procedural frameworks developed and adopted by the Meril's Management from time to time.
          </p>
          <p class="text-justify">
            I have been thoroughly informed on the various Code of Conduct that govern the ethical operation of Meril's business, which I agree to follow diligently. I have read understood and consent to abide by the following Codes of Conduct on a consensus-ad-idem basis:
          </p>
          <ol class="list-decimal pl-6 space-y-1">
            <li>Anti Bribery and Anti Corruption Policy</li>
            <li>Export Controls and Trade Sanctions Policy</li>
            <li>HCP & HCO Compliance framework</li>
            <li>National Pharmaceutical Pricing Authority norms for capping of maximum retail price & maximum trade margin across all trade channels</li>
            <li>FCPA (Foreign Corrupt Practices Act)</li>
          </ol>
          <p class="text-justify">
            I hereby confirm that I shall adhere in all respects to the ethics and standards of conduct outlined in the above Codes of Conduct. I understand that any violation or even potential violation of the these Codes of Conduct / Policies may result in disciplinary action, including termination of my employment.
          </p>
          <p class="text-justify">
            I certify that I am not currently in violation of any of the afore mentioned Codes of Conduct.
          </p>
          <p class="text-justify">
            Furthermore, I declare that I have no direct or indirect familial, financial, or other relationships with any distributor or nominated representative of the distributor. Should I become aware of any such relationship in the future, I commit to disclosing it to Meril within thirty (30) days from the date of awareness.
          </p>
          <p class="text-justify">
            I also declare that I will not engage in any financial transactions with any distributor or nominated representative of the distributor. I acknowledge that Meril Group shall bear no responsibility or liability for any such transactions.
          </p>
          <div class="mt-6 space-y-1">
            <p class="text-justify">Employee Name: {{ declarationInfo?.employee_name || 'Name' }}</p>
            <p class="text-justify">Employee ID: {{ declarationInfo?.custom_employee_id || 'ID' }}</p>
            <p class="text-justify">Company Name: {{ declarationInfo?.company || 'Company' }}</p>
            <p class="text-justify">Date: {{ currentDate }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Certification Form -->
    <div class="max-w-md mx-auto space-y-4">
      <div>
        <label for="certification-name" class="block text-sm font-medium text-gray-700 mb-1">
          Name <span class="text-red-500">*</span>
        </label>
        <TextInput
          id="certification-name"
          v-model="localName"
          type="text"
          placeholder="Enter your name"
          class="w-full"
          required
          :min-length="3"
        />
        <p v-if="nameError" class="text-sm text-red-600 mt-1">{{ nameError }}</p>
      </div>

      <div>
        <label for="certification-date" class="block text-sm font-medium text-gray-700 mb-1">
          Date
        </label>
        <input
          id="certification-date"
          v-model="localDate"
          type="datetime-local"
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-gray-500"
          readonly
        />
      </div>

      <Button
        theme="gray"
        variant="solid"
        class="w-full"
        @click="handleCertify"
        :disabled="!isValid"
      >
        I Certify
      </Button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { TextInput, Button } from 'frappe-ui'

const props = defineProps({
  userRole: {
    type: String,
    default: null
  },
  declarationInfo: {
    type: Object,
    default: () => ({})
  },
  certificationData: {
    type: Object,
    default: () => ({
      name: '',
      date: '',
      isCompleted: false
    })
  }
})

const emit = defineEmits(['certification-complete'])

const localName = ref('')
const localDate = ref('')
const nameError = ref('')

const currentDate = computed(() => {
  const date = new Date()
  const day = date.getDate().toString().padStart(2, '0')
  const month = date.toLocaleString('default', { month: 'long' })
  const year = date.getFullYear()
  return `${day} ${month} ${year}`
})

const currentDateTime = computed(() => {
  return new Date().toLocaleString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
    year: 'numeric',
    month: 'short',
    day: '2-digit'
  })
})

const isValid = computed(() => {
  return localName.value.trim().length >= 3
})

const getHeaderTitle = () => {
  if (props.userRole === 'Employee') {
    return 'Employee Declaration'
  }
  return 'Document Certification'
}

const getHeaderDescription = () => {
  if (props.userRole === 'Employee') {
    return 'Please review the Employee Declaration and provide your certification.'
  }
  return 'Please review the compliance documents and provide your certification.'
}

const showDeclaration = (documentType) => {
  // For now, show all declarations for distributors
  // This can be made configurable based on enabled documents
  return props.userRole === 'Distributor'
}

const validateName = () => {
  nameError.value = ''
  if (localName.value.trim().length < 3) {
    nameError.value = 'Name must be at least 3 characters long'
    return false
  }
  return true
}

const handleCertify = () => {
  if (!validateName()) {
    return
  }

  emit('certification-complete', {
    name: localName.value.trim(),
    date: localDate.value
  })
}

// Watch for changes in certification data from parent
watch(() => props.certificationData, (newData) => {
  if (newData.name && !localName.value) {
    localName.value = newData.name
  }
  if (newData.date && !localDate.value) {
    localDate.value = newData.date
  }
}, { immediate: true })

onMounted(() => {
  // Set current date/time
  localDate.value = new Date().toISOString().slice(0, 16)

  // Pre-fill name if available from declaration info
  if (props.declarationInfo?.attendee_name && !localName.value) {
    localName.value = props.declarationInfo.attendee_name
  } else if (props.declarationInfo?.employee_name && !localName.value) {
    localName.value = props.declarationInfo.employee_name
  }
})
</script>