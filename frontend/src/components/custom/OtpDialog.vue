<template>
  <div v-if="showOtpDialog" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
    <div
      v-if="showOtpDialog"
      title="Verify Your Identity"
      class="min-[500px]:w-100 w-full max-w-md max-h-[80vh] overflow-y-auto fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 shadow-lg rounded-lg bg-white"
      :close-on-esc="false"
      :close-on-overlay-click="false"
      :show-close-button="false"
      :show-footer="false"
    >
      <form class="p-6" @submit.prevent="submitOtp">
        <p class="text-center mb-4 text-gray-700 font-medium">
          Please Enter OTPs to continue your Training.
        </p>
        <div class="mb-4">
          <label class="block mb-1 text-gray-800 " for="email-otp">Email OTP</label>
          <TextInput
            id="email-otp"
            v-model="emailOtp"
            type="text"
            placeholder="Enter Email OTP"
            class="w-full mb-2 rounded-lg border p-2 focus:outline-none focus:ring-2"
            :error="!!errors.emailOtp"
          />
        </div>
        <div class="mb-6">
          <label class="block mb-1 text-gray-800 " for="mobile-otp">Mobile OTP</label>
          <TextInput
            id="mobile-otp"
            v-model="mobileOtp"
            type="text"
            placeholder="Enter Mobile OTP"
            class="w-full rounded-lg border p-2 focus:outline-none focus:ring-2"
            :error="!!errors.mobileOtp"
          />
        </div>
        <Button
          type="button"
          class="block w-fit p-2 ml-auto mb-4 rounded-lg border border-gray-500 cursor-pointer select-none active:ring-2 ring-gray-800"
          @click="sendOtp"
          v-bind:disabled="loading"
        >
          Resend me OTPs
        </Button>
        <Button
          type="submit"
          variant="solid"
          class="w-full flex"
          v-bind:disabled="loading"
        >
        <div class="flex items-center justify-center w-full">
         <Spinner v-if="loading" class="w-4 mr-2" />
          <span v-if="loading" class="block">Loading...</span>
          <span v-else class="block">Submit</span>
          
          </div>
        </Button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { call, TextInput, Button , Spinner } from "frappe-ui";

const showOtpDialog = ref(false)
const emailOtp = ref('')
const mobileOtp = ref('')
const errors = ref({
  emailOtp: "",
  mobileOtp: ""
})
const loading = ref(false);

window.addEventListener("load", () => {
  getUnlockedStatus();
})

async function getUnlockedStatus() {
  try {
    const res = await call("lms.overrides.otp_aut.get_user_status", {});
    if (res.status === "unlocked") {
      showOtpDialog.value = false;
      return;
    }
    showOtpDialog.value = true;
    if (res.status === "locked") {
      submitOtp();
      console.log("User is locked, showing OTP dialog.");
      return;
    }
    if (res.status === "error") {
      console.error("Error fetching user status:", res.message);
      alert(`Error: ${res.message || "Failed to fetch user status. Please refresh again."}`);
    }
  } catch (error) {
    console.error("Error fetching user status:", error);
    alert("Failed to fetch user status. Please try again later.");
  }
}

async function sendOtp() {
  try {
    loading.value = true;
    const res = await call("lms.overrides.otp_aut.send_email_otp");
    if (res.status === "success") {
      alert("OTP sent successfully!");
    } else if (res.status === "error") {
      alert(res.message || "Failed to send OTP. Please try again.");
    }
  } catch (error) {
    console.error("Error sending OTP:", error);
    alert("Failed to send OTP. Please try again later.");
  }finally{
    loading.value = false;
  }
}

async function submitOtp() {
  errors.value.emailOtp = ""
  errors.value.mobileOtp = ""
  if (!emailOtp.value) {
    errors.value.emailOtp = "Email OTP is required"
  }
  if (!mobileOtp.value) {
    errors.value.mobileOtp = "Mobile OTP is required"
  }
  if (errors.value.emailOtp || errors.value.mobileOtp) return;

  try {
    loading.value = true;
    const res = await call("lms.overrides.otp_aut.verify_email_otp", {
      otp: emailOtp.value,
      otp1: mobileOtp.value
    });
    if (res.status === "success") {
      alert("OTP verified successfully!");
      showOtpDialog.value = false;
    } else if (res.status === "error") {
      alert(res.message || "Failed to verify OTP. Please try again.");
    }
  } catch (error) {
    console.error("Error verifying OTP:", error);
    alert("Failed to verify OTP. Please try again later.");
  }finally{
    loading.value = false;
  }
}
</script>

<style scoped>
input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
input[type="number"] {
  -moz-appearance: textfield;
}
</style>