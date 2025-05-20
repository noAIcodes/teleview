<template>
  <div>
    <h2>Telegram Login</h2>
    <form @submit.prevent="requestLoginCode" v-if="!codeSent">
      <div>
        <label for="phone">Phone Number:</label>
        <input type="text" id="phone" v-model="phoneNumber" required>
      </div>
      <button type="submit" :disabled="loading">Request Code</button>
    </form>

    <form @submit.prevent="submitLoginCode" v-if="codeSent && !passwordNeeded">
      <div>
        <label for="code">Verification Code:</label>
        <input type="text" id="code" v-model="code" required>
      </div>
      <button type="submit" :disabled="loading">Submit Code</button>
    </form>

    <form @submit.prevent="submitLoginPassword" v-if="codeSent && passwordNeeded">
      <div>
        <label for="password">2FA Password:</label>
        <input type="password" id="password" v-model="password" required>
      </div>
      <button type="submit" :disabled="loading">Submit Password</button>
    </form>

    <p v-if="loading">Loading...</p>
    <p v-if="error" style="color: red;">{{ error }}</p>
    <p v-if="successMessage" style="color: green;">{{ successMessage }}</p>
  </div>
</template>

<script setup>
import { ref, defineEmits } from 'vue';
import axios from 'axios';

const phoneNumber = ref('');
const code = ref('');
const password = ref('');
const codeSent = ref(false);
const passwordNeeded = ref(false);
const loading = ref(false);
const error = ref(null);
const successMessage = ref(null);

const emit = defineEmits(['authenticated']);

const requestLoginCode = async () => {
  loading.value = true;
  error.value = null;
  successMessage.value = null;
  try {
    // Assuming your backend is running on http://localhost:8000
    await axios.post('http://localhost:8000/api/auth/request_code', {
      phone_number: phoneNumber.value
    });
    codeSent.value = true;
    successMessage.value = 'Code sent. Please check your Telegram messages.';
  } catch (err) {
    console.error('Error requesting code:', err);
    error.value = err.response?.data?.detail || 'Failed to request code.';
  } finally {
    loading.value = false;
  }
};

const submitLoginCode = async () => {
  loading.value = true;
  error.value = null;
  successMessage.value = null;
  try {
    const response = await axios.post('http://localhost:8000/api/auth/submit_code', {
      phone_number: phoneNumber.value,
      code: code.value
    });
    successMessage.value = response.data.message;
    // Emit event to parent component with authenticated phone number
    emit('authenticated', phoneNumber.value);
  } catch (err) {
    console.error('Error submitting code:', err);
    error.value = err.response?.data?.detail || 'Failed to submit code.';
    if (err.response?.data?.detail && err.response.data.detail.includes('Two-Factor Authentication password is required')) {
        passwordNeeded.value = true;
        successMessage.value = '2FA password required.';
    }
  } finally {
    loading.value = false;
  }
};

const submitLoginPassword = async () => {
  loading.value = true;
  error.value = null;
  successMessage.value = null;
  try {
    const response = await axios.post('http://localhost:8000/api/auth/submit_code', {
      phone_number: phoneNumber.value,
      code: code.value, // Still need to send the code along with the password
      password: password.value
    });
    successMessage.value = response.data.message;
     // Emit event to parent component with authenticated phone number
    emit('authenticated', phoneNumber.value);
  } catch (err) {
    console.error('Error submitting password:', err);
    error.value = err.response?.data?.detail || 'Failed to submit password.';
  } finally {
    loading.value = false;
  }
};

</script>

<style scoped>
form div {
  margin-bottom: 10px;
}
</style>