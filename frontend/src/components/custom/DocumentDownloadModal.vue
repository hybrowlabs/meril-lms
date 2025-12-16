<template>
  <!-- New Document Wizard Modal -->
  <DocumentWizardModal />
</template>

<script setup>
import { watch } from "vue";
import DocumentWizardModal from "../DocumentWizardModal.vue";
import { openModal, closeModal, state } from "../../stores/document-workflow.js";
import { state as courseCompletionState } from "../../stores/course_completion.js";

// Watch for changes in course completion state to open the new modal
watch(() => courseCompletionState.showDocument, (newVal) => {
  if (newVal && courseCompletionState.courseName) {
    openModal(courseCompletionState.courseName)
  }
})

</script>