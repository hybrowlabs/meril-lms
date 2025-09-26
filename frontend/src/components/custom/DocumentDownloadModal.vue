<template>
  <div v-if="state?.showDocument">
    <div v-if="showError">
      <div class="fixed inset-0 z-50 bg-black bg-opacity-50">
        <div class="min-[500px]:w-100 w-full max-w-md max-h-[80vh] overflow-y-auto fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 shadow-lg rounded-lg bg-white p-6 relative">
          <button
        class="block ml-auto focus:ring-2 hover:ring-3 hover:ring-gray-400 focus:ring-gray-400 text-gray-400 hover:text-gray-700 text-2xl font-bold focus:outline-none"
         @click="closeDialog"
        aria-label="Close"
      >
        ×
      </button>
          <h3 class="text-lg font-medium mb-4">Error</h3>
          <p>{{ errorMessage }}</p>
          <Button theme="gray" variant="solid" @click="checkDocumentSubmission">Try again</Button>
        </div>
      </div>
    </div>
  <div v-else-if="loadingScreen">
    <div class="fixed inset-0 z-50 bg-black bg-opacity-50">
        <div class="min-[500px]:w-100 w-full max-w-md max-h-[80vh] overflow-y-auto fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 shadow-lg rounded-lg bg-white p-6 relative">
          <button
          class="block ml-auto focus:ring-2 hover:ring-3 hover:ring-gray-400 focus:ring-gray-400 text-gray-400 hover:text-gray-700 text-2xl font-bold focus:outline-none"
         @click="closeDialog"
        aria-label="Close"
      >
        ×
      </button>
          <p>Loading...</p>
        </div>
      </div>
  </div>
  <div  v-else-if="showDownloadForm" class="fixed inset-0 z-50 bg-black bg-opacity-50">
    <div
      title="Compliance Documents"
      class="min-[500px]:w-100 w-full max-w-md max-h-[80vh] overflow-y-auto fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 shadow-lg rounded-lg bg-white p-6 relative"
    >
      <!-- Close Icon -->
      <button
      class="block ml-auto focus:ring-2 hover:ring-3 hover:ring-gray-400 focus:ring-gray-400 text-gray-400 hover:text-gray-700 text-2xl font-bold focus:outline-none"
         @click="closeDialog"
        aria-label="Close"
      >
        ×
      </button>
      <h3 class="text-xl font-medium mb-4">{{ allDocumentsUploaded ? 'Your Uploaded Documents' : 'Compliance Documents' }}</h3>
      <ul class="space-y-4 mb-2">
        <li v-for="document in displayDocumentsList" :key="document.name || document" class="flex  items-center justify-between">
          <span class="text-sm text-gray-900">{{ document.name || document }}</span>
          <Button theme="gray" variant="outline" @click="downloadDocument(document)" >Download</Button>
        </li>
      </ul>
      <!-- Download All Button for uploaded documents -->
      <div v-if="allDocumentsUploaded && uploadedDocumentsList.length > 0" class="mt-6 border-t pt-4">
        <Button theme="gray" variant="solid" @click="downloadAllUploadedDocuments" class="w-full">
          <span class="flex items-center justify-center gap-2">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M7 10l5 5m0 0l5-5m-5 5V4"/>
            </svg>
            Download All Documents
          </span>
        </Button>
      </div>
    </div>
  </div>

  <!-- Second Modal: Form Modal -->
  <div v-else-if="showUploadForm" class="fixed inset-0 z-50 bg-black bg-opacity-50">
    <div
      class="min-[500px]:w-100 w-full max-w-md max-h-[80vh] overflow-y-auto fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 shadow-lg rounded-lg bg-white p-6 relative"
    >
      <!-- Close Icon -->
      <button
        class="block ml-auto focus:ring-2 hover:ring-3 px-2 rounded-sm hover:ring-gray-900 focus:ring-gray-400 text-gray-400 hover:text-gray-700 text-2xl font-bold focus:outline-none transition"
        @click="closeDialog"
        aria-label="Close"
      >
        ×
      </button>
      <h3 class="text-lg font-semibold mb-4 uppercase text-gray-900">{{ currentDocName || 'Instructions:' }}</h3>
      <ol class="list-decimal list-inside text-gray-700 mb-4 space-y-1">
        <li>
          Please <span class="font-semibold text-gray-900">download</span> the <span class="font-semibold"> {{  uploadDocumentName }} </span> 
        </li>
  
          <li v-if="uploadDocumentName=='Meril Distributor Compliance Policy Adoption Form'">
            Insert your company's letterhead at the top of the document.
          </li>
          <li v-else>
            Sign the Docuemnt
          </li>
          <li>
            Then upload the completed document.
          </li>
      </ol>
      <div v-if="showDownloadForm" class="mb-4 p-3 bg-gray-50 border border-gray-400 text-gray-800 rounded flex items-center gap-2">
        <span class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-gray-900 text-white font-bold mr-2">✓</span>
        <span>
          <strong>Document Submitted</strong> - You have already submitted a document for this course.
        </span>
      </div>
      <form @submit.prevent="handleDownload" class="mb-4">
        <button
          type="submit"
          class="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-md bg-gray-100 hover:bg-gray-300
          text-gray-900 font-semibold shadow transition-colors duration-150 focus:outline-none focus:ring-2 
          focus:ring-offset-2 focus:ring-gray-600 active:ring-2 active:ring-black"
        >
          <svg class="w-5 h-5 mr-1" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M7 10l5 5m0 0l5-5m-5 5V4"/>
          </svg>
          Download Document
        </button>
      </form>
      <form @submit.prevent="uploadDocument">
        <div class="mb-4">
          <label
            for="upload-file"
            class="block mb-2 text-sm font-medium text-gray-700"
          >
            Upload Document
          </label>
          <div class="relative flex items-center">
            <input
              id="upload-file"
              type="file"
              @change="onFileChange"
              class="block w-full border border-gray-500 text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-900 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-gray-50 file:text-gray-900 hover:file:bg-gray-100 transition pr-10"
              required
              accept=".docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/pdf"
            />
            <span class="absolute right-3 pointer-events-none flex items-center">
              <!-- Upload Icon beside "Choose file" text -->
              <svg class="w-5 h-5 text-gray-700" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M7 10l5-5m0 0l5 5m-5-5v12"/>
              </svg>
            </span>
          </div>
        </div>
        <button
          type="submit"
          :disabled="loadingUploadForm"
          class="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-md bg-gray-900 hover:bg-gray-700 text-white font-semibold shadow transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-900 disabled:opacity-60 disabled:cursor-not-allowed"
        >
          <Spinner v-if="loadingUploadForm" class="w-4 h-4 mr-2" />
          <span>{{ loadingUploadForm ? "Uploading Document" : "Submit" }}</span>
        </button>
      </form>
    </div>
  </div>

  <div v-if="showDeclarationForm" class="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center">
    <div
      class="min-[500px]:w-100 w-full max-w-md max-h-[90vh] overflow-y-auto shadow-lg rounded-lg bg-white p-6 relative"
    >
      <!-- Close Icon -->
      <button
      class="block ml-auto focus:ring-2 hover:ring-3 px-2 rounded-sm hover:ring-gray-900 focus:ring-gray-400 text-gray-400 hover:text-gray-700 text-2xl font-bold focus:outline-none"
         @click="closeDialog"
        aria-label="Close"
      >
        ×
      </button>
      <div v-if="role_is=='Distributor'">
        <div v-if="uploadDocumentName=='Meril Distributor Compliance Policy Adoption Form'">
          <h3 class="text-center font-semibold mx-auto max-w-80">Meril Distributor- Compliance Policy Adoption Form</h3>
          <div class="overflow-y-auto h-60 pb-4 border-2 mb-2 mt-4 rounded-lg border-black/50 px-2 border-dotted ">
              <p class="text-sm mt-4">
                {{ new Date().toLocaleString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true, year: 'numeric', month: 'short', day: '2-digit' }) }}
              </p>
              <p class="text-sm text-justify mt-2">We {{ declaratinoInfo.distributor_company_name }}, being the Distributor of Meril {{ distributor?.meril_company_table[0]?.meril_company_name }} do hereby certify that we have willingly adopted attached Meril
            Distributor Compliance Policy as our own Compliance Policy with effect from
            {{ current_date }} and declare to abide by the same.</p>
              <p class="text-sm text-justify mt-2">All employees, partners, directors, proprietor of our organization are expected to
              observe and adhere to this Policy.</p>
              <p class="text-sm text-justify mt-2 underline font-semibold">Nomination of Compliance Officer:</p>
              <p class="text-sm text-justify mt-2">{{ name }} is nominated as Compliance Officer of our organization with effect
                from {{ current_date }}</p>
                
                <p class="text-sm text-justify mt-6">Authorized representative of {{ declaratinoInfo.distributor_company_name }}</p>
                <p class="text-sm text-justify mt-6">Name : {{ declaratinoInfo.attendee_name }}</p>
                <p class="text-sm text-justify mt-2">Title : {{ declaratinoInfo.designation }}</p>
                <p class="text-sm text-justify mt-2">Email Id : {{ declaratinoInfo.distributor_email_address }}</p>
                <p class="text-sm text-justify mt-2">Contact number : {{ declaratinoInfo.distributor_contact_number }}</p>
                <p
                  class="text-sm text-justify mt-2"
                >
                  Sign and Seal : <span > {{"<Compliance officer nominee name>"}} </span>
                </p>
             </div>
            </div>
            <div v-else-if="uploadDocumentName=='Distributor Self Declaration'">
              <h3 class="text-center font-semibold mx-auto max-w-80">Distributor Self Declaration</h3>
              <div class="overflow-y-auto h-60 pb-4 border-2 mb-2 mt-4 rounded-lg border-black/50 px-2 border-dotted ">
                <p class="text-sm text-justify mt-2">This is to declare that we {{ declaratinoInfo?.distributor_company_name || 'Company Name' }}, have reviewed and understood the Meril Distributor Compliance Policy and will adhere to all its provisions.</p>
                <p class="text-sm text-justify mt-4">We confirm that we will:</p>
                <ul class="list-disc pl-6 text-sm mt-2">
                  <li>Comply with all applicable laws and regulations</li>
                  <li>Maintain ethical business practices</li>
                  <li>Report any violations or concerns</li>
                  <li>Cooperate with compliance reviews and audits</li>
                </ul>
                <p class="text-sm text-justify mt-6">Authorized representative of {{ declaratinoInfo?.distributor_company_name || 'Company Name' }}</p>
                <p class="text-sm text-justify mt-6">Name : {{ declaratinoInfo?.attendee_name || 'Name' }}</p>
                <p class="text-sm text-justify mt-2">Title : {{ declaratinoInfo?.designation || 'Designation' }}</p>
                <p class="text-sm text-justify mt-2">Date : {{ current_date }}</p>
              </div>
            </div>
            <div v-else-if="uploadDocumentName=='Meril Distributor Compliance Code Of Conduct'">
              <h3 class="text-center font-semibold mx-auto max-w-80">Meril Distributor Compliance Code Of Conduct</h3>
              <div class="overflow-y-auto h-60 pb-4 border-2 mb-2 mt-4 rounded-lg border-black/50 px-2 border-dotted ">
                <p class="text-sm text-justify mt-2">We {{ declaratinoInfo?.distributor_company_name || 'Company Name' }} acknowledge and agree to abide by the Meril Distributor Compliance Code of Conduct.</p>
                <p class="text-sm text-justify mt-4">We understand and will comply with:</p>
                <ol class="list-decimal pl-6 text-sm mt-2">
                  <li>Anti Bribery and Anti Corruption policies</li>
                  <li>Fair business practices</li>
                  <li>Confidentiality and data protection</li>
                  <li>Conflict of interest policies</li>
                  <li>Product quality and safety standards</li>
                </ol>
                <p class="text-sm text-justify mt-6">Authorized representative of {{ declaratinoInfo?.distributor_company_name || 'Company Name' }}</p>
                <p class="text-sm text-justify mt-6">Name : {{ declaratinoInfo?.attendee_name || 'Name' }}</p>
                <p class="text-sm text-justify mt-2">Title : {{ declaratinoInfo?.designation || 'Designation' }}</p>
                <p class="text-sm text-justify mt-2">Date : {{ current_date }}</p>
              </div>
            </div>
            <div v-else-if="uploadDocumentName=='Distributor Declaration - Ethical Practices & Compliance'">
              <h3 class="text-center font-semibold mx-auto max-w-80">Distributor Declaration - Ethical Practices & Compliance</h3>
              <div class="overflow-y-auto h-60 pb-4 border-2 mb-2 mt-4 rounded-lg border-black/50 px-2 border-dotted ">
                <p class="text-sm text-justify mt-2">I hereby declare that {{ declaratinoInfo?.distributor_company_name || 'Company Name' }} has undergone and understood training provided on Ethical Practices and Compliance.</p>
                <p class="text-sm text-justify mt-4">We acknowledge and accept the duty to comply with:</p>
                <ul class="list-disc pl-6 text-sm mt-2">
                  <li>All procedural frameworks developed by Meril</li>
                  <li>Ethical operation guidelines</li>
                  <li>NPPA norms and trade regulations</li>
                  <li>International compliance standards</li>
                </ul>
                <p class="text-sm text-justify mt-4">We certify that we are not currently in violation of any compliance policies.</p>
                <p class="text-sm text-justify mt-6">Authorized representative of {{ declaratinoInfo?.distributor_company_name || 'Company Name' }}</p>
                <p class="text-sm text-justify mt-6">Name : {{ declaratinoInfo?.attendee_name || 'Name' }}</p>
                <p class="text-sm text-justify mt-2">Title : {{ declaratinoInfo?.designation || 'Designation' }}</p>
                <p class="text-sm text-justify mt-2">Date : {{ current_date }}</p>
              </div>
            </div>
        </div>
        <div v-else-if="role_is=='Employee'">
          <h3 class="text-center font-semibold mx-auto max-w-80">Employee Declaration - Ethical Practices &amp; Compliance</h3>
          <div class="overflow-y-auto h-60 pb-4 border-2 mb-2 mt-4 rounded-lg border-black/50 px-2 border-dotted ">
              <p class="text-sm text-justify mt-2">I hereby declare that I have undergone and understood training provided on Ethical
Practices and compliance . As a responsible employee of Meril, I acknowledge and
accept the duty to comply with the procedural frameworks developed and adopted by
the Meril’s Management from time to time.</p>
            <p class="text-sm text-justify mt-2">I have been thoroughly informed on the various Code of Conduct that govern the
ethical operation of Meril’s business, which I agree to follow diligently. I have read
understood and consent to abide by the following Codes of Conduct on a consensus-
ad-idem basis :</p>
              <ol class="list-decimal pl-6 text-sm mt-2">
                <li>Anti Bribery and Anti Corruption Policy</li>
                <li>Export Controls and Trade Sanctions Policy</li>
                <li>HCP &amp; HCO Compliance framework</li>
                <li>National Pharmaceutical Pricing Authority norms for capping of
maximum retail price &amp; maximum trade margin across all trade
channels</li>
                <li>FCPA (Foreign Corrupt Practices Act)</li>
              </ol>
              <p class="text-sm text-justify mt-2">I hereby confirm that I shall adhere in all respects to the ethics and standards of conduct
outlined in the above Codes of Conduct. I understand that any violation or even potential
violation of the these Codes of Conduct / Policies may result in disciplinary action,
including termination of my employment.</p>
                <p class="text-sm text-justify mt-2">I certify that I am not currently in violation of any of the afore mentioned Codes of
                  Conduct.</p>
                <p class="text-sm text-justify mt-2">Furthermore, I declare that I have no direct or indirect familial, financial, or other
relationships with any distributor or nominated representative of the distributor. Should I
become aware of any such relationship in the future, I commit to disclosing it to Meril
within thirty (30) days from the date of awareness.</p>
                  <p class="text-sm text-justify mt-2">I also declare that I will not engage in any financial transactions with any distributor or
nominated representative of the distributor. I acknowledge that Meril Group shall bear no
responsibility or liability for any such transactions.</p>
                
                <p class="text-sm text-justify mt-2">Employee Name : {{ declaratinoInfo.employee_name }}</p>
                <p class="text-sm text-justify mt-2">Employee ID : {{ declaratinoInfo.custom_employee_id }}</p>
                <p class="text-sm text-justify mt-2">Company Name : {{ declaratinoInfo.company }}</p>
                <p class="text-sm text-justify mt-2">Date : {{ date }}</p>
             </div>
        </div>
        
        <form @submit="handleCertify" class="flex flex-col gap-y-2">
          <div class="flex flex-col gap-y-2">
            <label for="name" class="text-sm font-medium">Name</label>
            <TextInput
              id="name"
              type="text"
              placeholder="Enter name"
              v-model="name"
              class="w-full rounded-lg border focus:outline-none focus:ring-2 border-gray-300"
              required
              minlength="3"
            />
          </div>
        
          <div class="flex flex-col gap-y-2">
            <label for="date" class="text-sm font-medium">Date</label>
            <input
              id="date"
              type="datetime-local"
              :value="new Date().toISOString().slice(0,16)"
              class="border rounded px-2 py-1 text-sm"
              readonly
            />
          </div>
          <Button theme="gray" variant="solid" class="w-full mt-4" type="submit" :disabled="loadingUploadForm">
        <div class="flex items-center justify-center w-full">
        <Spinner v-if="loadingUploadForm" class="w-4 mr-2" />  
        <span>{{ loadingUploadForm ? "" : "I Certify"}}</span>
        </div>
      </Button>
    </form>
    </div>
  </div>
</div>
</template>

<script setup>
import { Button, Spinner } from "frappe-ui";
import { defineEmits, ref, watch, computed, onMounted } from "vue";
import { call , TextInput, Select, toast } from 'frappe-ui'
import { useRoute } from 'vue-router'
import { resetCourseCompletion, state } from "../../stores/course_completion.js";

const emit = defineEmits(['close']);
const current_date = (() => {
  const date = new Date();
  const day = date.getDate().toString().padStart(2, '0');
  const month = date.toLocaleString('default', { month: 'long' });
  const year = date.getFullYear();
  return `${day} ${month} ${year}`;
})();
// Second modal state and logic
const showUploadForm = ref(false)
const uploadDocumentName = ref("Meril Distributor Compliance Policy Adoption Form");
const loadingScreen = ref(false);
const showDownloadForm = ref(false)
const name = ref('')
const currentDocName = ref('')
const signatureText = computed(() => name.value?.trim() || 'Signature')
const showError = ref(false)
const declaratinoInfo = ref(null);
const showDeclarationForm = ref(true);
const uploadDolaodEnabled = ref({
  distributor_self_declaration: false,
  meril_distributor_compliance_code_of_conduct: false,
  meril_distributor_compliance_policy_adoption_form: false,
  distributor_declaration_ethical_practices: false,
})

// Track which documents have been uploaded in current session
const uploadedDocuments = ref(new Set())

// Computed property to decide which documents to display
const displayDocumentsList = computed(() => {
  // If all 3 documents are uploaded, show the uploaded documents + completion certificate
  if (allDocumentsUploaded.value && uploadedDocumentsList.value.length >= 3) {
    // Combine uploaded documents with completion certificate
    const combinedList = [...uploadedDocumentsList.value]
    // Add completion certificate as a print format document (not uploaded by user)
    combinedList.push({
      name: "Distributor Completion Certificate",
      isPrintFormat: true
    })
    return combinedList
  }
  // Otherwise show the standard documents list
  return documentsList.value
})

// signature removed

const date = ref( new Date().toISOString().split('T')[0])
const file = ref(null)
const documentsList = ref([])
const uploadedDocumentsList = ref([]) // List of user's uploaded documents
const allDocumentsUploaded = ref(false) // Flag to check if all 4 documents are uploaded
const loadingUploadForm = ref(false);
const errorMessage = ref('')
const course_documents_record_id = ref('');
const doctype = ref('');

const role_is = ref(null);
// signature fonts removed


const handleCertify = async (event) => {
  if (event && typeof event.preventDefault === "function") {
    event.preventDefault();
  }

  // If Employee, take signature via API then show download form
  if (role_is.value === 'Employee') {
    if (!name.value || name.value.trim().length < 3) {
      toast.error('Please enter name (minimum 3 characters)')
      return
    }
    showDeclarationForm.value = false;
    showUploadForm.value = false;
    showDownloadForm.value = true;
    return;
  }

  // Default (Distributor): move to upload form
  showDeclarationForm.value = false;
  showUploadForm.value = true;
}
// Fetch list of signature types where font files are not private
// signature fonts removed

async function get_declaration_info(){
  try{
  const res = await call("lms.overrides.documents.get_declaration_info");

  console.log("declaraion info", res);
  declaratinoInfo.value = res;

  // If we don't have declaratinoInfo, set defaults to prevent empty modal
  if (!declaratinoInfo.value) {
    declaratinoInfo.value = {
      distributor_company_name: 'Company Name',
      attendee_name: 'Name',
      designation: 'Designation',
      distributor_email_address: 'Email',
      distributor_contact_number: 'Contact'
    }
  }
  }catch(err){
    console.error("Error getting declaration", err)
    toast.error("Error in getting declaration")
    // Set defaults even on error
    declaratinoInfo.value = {
      distributor_company_name: 'Company Name',
      attendee_name: 'Name',
      designation: 'Designation',
      distributor_email_address: 'Email',
      distributor_contact_number: 'Contact'
    }
  }
}
uploadDolaodEnabled
function decideInitialView() {
  // Reset all views
  showError.value = false
  loadingScreen.value = false
  showDownloadForm.value = false
  showUploadForm.value = false
  showDeclarationForm.value = false

  // Check what needs to be uploaded next based on priority
  const documentsToUpload = getNextDocumentToUpload()

  if (documentsToUpload) {
    // Show the appropriate form for the next document
    currentDocName.value = documentsToUpload
    uploadDocumentName.value = documentsToUpload

    // For Policy Adoption Form, show declaration first
    if (documentsToUpload === 'Meril Distributor Compliance Policy Adoption Form') {
      showDeclarationForm.value = true
    } else {
      showUploadForm.value = true
    }
    return
  }

  // All documents uploaded, show download modal
  showDownloadForm.value = true
}

// Get the next document that needs to be uploaded
function getNextDocumentToUpload() {
  // Only 3 documents need to be uploaded (completion certificate is generated, not uploaded)
  const documentPriority = [
    { key: 'meril_distributor_compliance_policy_adoption_form', name: 'Meril Distributor Compliance Policy Adoption Form' },
    { key: 'distributor_self_declaration', name: 'Distributor Self Declaration' },
    { key: 'meril_distributor_compliance_code_of_conduct', name: 'Meril Distributor Compliance Code of Conduct' }
  ]

  for (const doc of documentPriority) {
    // Check if document is enabled and not uploaded yet
    if (uploadDolaodEnabled.value[doc.key] && !uploadedDocuments.value.has(doc.name)) {
      return doc.name
    }
  }

  return null // All required documents uploaded
}

onMounted(async () => {
  console.log("mounted");
  try {
    const res = await call("lms.overrides.documents.get_upload_download_docuemtn_enabled");
    if (res?.success) {
      uploadDolaodEnabled.value = {
        distributor_self_declaration: !!res.distributor_self_declaration,
        meril_distributor_compliance_code_of_conduct: !!res.meril_distributor_compliance_code_of_conduct,
        meril_distributor_compliance_policy_adoption_form: !!res.meril_distributor_compliance_policy_adoption_form
      }
    }
  } catch (e) {
    console.error("Error fetching upload/download enabled flags", e);
  }
  decideInitialView()
});


const closeDialog = ()=>{
  resetCourseCompletion();
  name.value = "";
  showError.value = false;
  showDownloadForm.value = false;
  showDeclarationForm.value = false;
}

const onFileChange = (e) => {
  const selectedFile = e.target.files[0];
  const maxSize = 4 * 1024 * 1024; // 4MB
  if (selectedFile && selectedFile.size > maxSize) {
    file.value = null;
    e.target.value = ""; // reset file input
    toast.warning("File size must be less than 4MB");
    return;
  }
  file.value = selectedFile;
}

const route = useRoute()
const courseName = computed(() => route.params.courseName || state.courseName)

watch( () => state.showDocument , (newVal) => {
  if (newVal) {
    checkDocumentSubmission()
  }
})

const checkDocumentSubmission = async () => {
try {
    loadingScreen.value = true
    showDeclarationForm.value = false

    // First ensure we have the enabled flags loaded
    if (!uploadDolaodEnabled.value.distributor_self_declaration
      && !uploadDolaodEnabled.value.meril_distributor_compliance_code_of_conduct
      && !uploadDolaodEnabled.value.meril_distributor_compliance_policy_adoption_form) {
      // Try to load the flags if not already loaded
      try {
        const flagsRes = await call("lms.overrides.documents.get_upload_download_docuemtn_enabled");
        if (flagsRes?.success) {
          uploadDolaodEnabled.value = {
            distributor_self_declaration: !!flagsRes.distributor_self_declaration,
            meril_distributor_compliance_code_of_conduct: !!flagsRes.meril_distributor_compliance_code_of_conduct,
            meril_distributor_compliance_policy_adoption_form: !!flagsRes.meril_distributor_compliance_policy_adoption_form
          }
        }
      } catch (e) {
        console.error("Error fetching upload/download enabled flags", e);
      }

      // If still no flags enabled, show download modal
      if (!uploadDolaodEnabled.value.distributor_self_declaration
        && !uploadDolaodEnabled.value.meril_distributor_compliance_code_of_conduct
        && !uploadDolaodEnabled.value.meril_distributor_compliance_policy_adoption_form) {
        loadingScreen.value = false
        decideInitialView()
        return
      }
    }
    const res = await call('lms.overrides.documents.has_user_submited_document', { course: courseName.value })
    console.log("res",res)
    if(res.error){
      showError.value = true
      showUploadForm.value = false
      errorMessage.value = res.error
      showDeclarationForm.value = false
      toast.error(res.error)
      return
    }
    if (res.submited === true) {
      showDownloadForm.value = true
      showUploadForm.value = false
      showDeclarationForm.value = false
      documentsList.value = res.documents_list
      course_documents_record_id.value = res.course_documents_record_id
      doctype.value = res.doctype
      role_is.value = res.role_is

      // Pull existing uploaded documents from the response
      if (res.uploaded_documents && res.uploaded_documents.length > 0) {
        uploadedDocumentsList.value = res.uploaded_documents
        // Mark documents as uploaded in our tracking
        res.uploaded_documents.forEach(doc => {
          uploadedDocuments.value.add(doc.name)
        })
        // If we have 3 or more uploaded documents (not including completion certificate), mark as all uploaded
        if (res.uploaded_documents.length >= 3) {
          allDocumentsUploaded.value = true
        }
      }

      console.log('Document already submitted for this course')
    } else {
      get_declaration_info();
      role_is.value = res.role_is
      // Store the course_documents_record_id even if document doesn't exist yet
      course_documents_record_id.value = res.course_documents_record_id || null
      doctype.value = res.doctype || 'Distributor Course Documents'

      // If backend provides documents_list for not-submitted state, use it to avoid empty modal
      if (Array.isArray(res.documents_list) && res.documents_list.length) {
        documentsList.value = res.documents_list
      }

      // Check if there are partially uploaded documents
      if (res.uploaded_documents && res.uploaded_documents.length > 0) {
        uploadedDocumentsList.value = res.uploaded_documents
        // Mark documents as uploaded in our tracking
        res.uploaded_documents.forEach(doc => {
          uploadedDocuments.value.add(doc.name)
        })
      }
      // decide initial view based on flags
      decideInitialView()
    }

    if(showError.value){
      showError.value = false;
    }
  } catch (e) {
    // handle error
    showDownloadForm.value = false
    showUploadForm.value = false
    showDeclarationForm.value = false
    showError.value = true
    toast.error(e?.exception || 'Error checking document submission')
  } finally {
    loadingScreen.value = false
  }
}

const uploadDocument = async () => {
  loadingUploadForm.value = true

  if(!file.value) {
    toast.error("Please select a file")
    loadingUploadForm.value = false
    return;
  }
  
  try {
    // Convert file to base64
    const base64Data = await fileToBase64(file.value)
    
    // Call the save_user_course_document_with_file method
    const response = await call('lms.overrides.documents.upload_distributor_document_with_datetime', {
      course: courseName.value,
      document_name: currentDocName.value || file.value.name,
      filename: file.value.name,
      base64_file_data: base64Data,
      is_private: 0,
      document_upload_datetime: new Date().toISOString(),
      uploadDocumentName: uploadDocumentName.value
    })
    console.log("response", response)
    if (response.message && response.success) {
      toast.success('Document uploaded successfully')

      // Mark this document as uploaded
      uploadedDocuments.value.add(uploadDocumentName.value)

      // Reset form
      date.value = ''
      file.value = null
      // Reset file input
      const fileInput = document.querySelector('input[type="file"]')
      if (fileInput) fileInput.value = ''

      // Check what document should be shown next
      const nextDoc = getNextDocumentToUpload()

      if (nextDoc) {
        // Show form for next document
        currentDocName.value = nextDoc
        uploadDocumentName.value = nextDoc
        showUploadForm.value = false
        showDownloadForm.value = false

        // For certain documents, show declaration form first
        if (nextDoc === 'Distributor Self Declaration' ||
            nextDoc === 'Meril Distributor Compliance Code Of Conduct' ||
            nextDoc === 'Distributor Declaration - Ethical Practices & Compliance') {
          showDeclarationForm.value = true
          get_declaration_info()
        } else {
          showUploadForm.value = true
        }
      } else {
        // All documents uploaded, refresh to show download modal
        await checkDocumentSubmission()
      }
    } else {
      toast.error(response?.message || 'Upload failed')
    }
  } catch (error) {
    console.error('Upload error:', error)
    toast.error(error.messages?.[0] || 'Upload failed')
  }finally {
    loadingUploadForm.value = false
  }
}

// Helper function to convert file to base64
const fileToBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      try {
        const base64 = reader.result.split(',')[1]
        const cleanBase64 = base64.replace(/[^A-Za-z0-9+/=]/g, '')
        resolve(cleanBase64)
      } catch (error) {
        reject(error)
      }
    }
    reader.onerror = error => reject(error)
    reader.readAsDataURL(file)
  })
}

// Helper function to send file to React Native WebView
const sendToWebView = (base64Content, fileName, mimeType) => {
  if (window.ReactNativeWebView) {
    window.ReactNativeWebView.postMessage(
      JSON.stringify({
        type: "DOWNLOAD_FILE",
        base64: base64Content,
        fileName: fileName,
        mimeType: mimeType || "application/pdf"
      })
    );
    return true;
  }
  return false;
};

// Helper function to fetch document as base64
const fetchDocumentAsBase64 = async (url) => {
  try {
    const response = await fetch(url);
    const blob = await response.blob();

    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const base64 = reader.result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  } catch (error) {
    console.error("Error fetching document as base64:", error);
    throw error;
  }
};

const directDownload = async(url, file_name)=>{
   // Check if running in WebView
   if (window.ReactNativeWebView) {
      try {
        toast.success("Downloading Started...");
        const base64Content = await fetchDocumentAsBase64(url);
        const mimeType = file_name?.endsWith('.pdf') ? 'application/pdf' :
                        file_name?.endsWith('.docx') ? 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' :
                        'application/octet-stream';
        sendToWebView(base64Content, file_name, mimeType);
      } catch (error) {
        console.error("Error downloading in WebView:", error);
        toast.error("Download failed in WebView");
      }
   } else {
      // Regular browser download
      const link = document.createElement('a');
      link.href = url;
      link.download = file_name;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
   }
}


const handleDownload = async() => {
  try{
    // Always use the generate_dynamic_docx API which handles document creation if needed
    const res = await call("lms.overrides.documents.generate_dynamic_docx", {
      name: name?.value || '',
      course: courseName.value,
      font_path: null,
      document_type: uploadDocumentName.value,  // Pass document type
      use_print_format: true  // Force print format generation to ensure document is created
    });
    console.log("res", res)
    if (res?.success && res.file_content) {
      toast.success("Downloading Started...");

      // Use the helper function for WebView downloads
      const isPDF = res.file_name?.endsWith('.pdf');
      const mimeType = isPDF ? "application/pdf" : "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
      const fileName = res.file_name || `${name.value}_${uploadDocumentName.value}.${isPDF ? 'pdf' : 'docx'}`;

      if (!sendToWebView(res.file_content, fileName, mimeType)) {
        // Not in WebView, use regular browser download
        const url = `data:${mimeType};base64,${res.file_content}`;
        const a = document.createElement('a');
        a.href = url;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      }
    } else {
      toast.error(res?.error || "Error generating document")
    }
  }catch(e) {
    console.error("Error in handleDownload", e)
    toast.error("Error in downloading document")
  }
}

const downloadDocument = async (document) => {
  try {
      const baseUrl = window.location.origin;
      let url = null;

      // Check if this is an uploaded document object with file_url
      if (document.file_url) {
        // Direct download of uploaded file
        url = `${baseUrl}${document.file_url}`;
        await directDownload(url, document.name || 'document');
        return;
      }

      // Get document name
      const document_name = document.name || document;

      if(!course_documents_record_id?.value){
        toast.error("Course document record id not found")
        console.error("Course document record id not found")
        return;
      }

      const params = new URLSearchParams({
          doctype: doctype.value,
          name: course_documents_record_id.value,
          format: document_name,
          no_letterhead: '1',
          letterhead: 'No Letterhead',
          settings: '{}',
          _lang: 'en',
          custom_filename: document_name, // set custom filename
          custom_type: 'download'         // set custom type
      });

      url = `${baseUrl}/api/method/lms.overrides.download_pdf.custom_download_pdf?${params.toString()}`;

      if (document_name === "Meril Distributor Compliance Policy")
          url = `${baseUrl}/api/method/lms.overrides.documents.downlaod_nonendo_file`;

      if (document_name === "Meril Distributor Compliance Policy for Endo")
          url =  `${baseUrl}/api/method/lms.overrides.documents.downlaod_endo_file`;

      // Use the appropriate filename with .pdf extension if not present
      const fileName = document_name.endsWith('.pdf') ? document_name : `${document_name}.pdf`;
      await directDownload(url, fileName);
  } catch (e) {
      toast.error('Failed to download document');
      console.error("Error in downloadDocument", e);
  }
}

// Download all uploaded documents
const downloadAllUploadedDocuments = async () => {
  if (!displayDocumentsList.value || displayDocumentsList.value.length === 0) {
    toast.error('No documents to download')
    return
  }

  toast.success('Starting download of all documents...')

  // Add delay between downloads to prevent browser blocking
  for (let i = 0; i < displayDocumentsList.value.length; i++) {
    const doc = displayDocumentsList.value[i]
    await downloadDocument(doc)

    // Add small delay between downloads (except for last one)
    if (i < displayDocumentsList.value.length - 1) {
      await new Promise(resolve => setTimeout(resolve, 500))
    }
  }
}

</script>

<style>
</style>