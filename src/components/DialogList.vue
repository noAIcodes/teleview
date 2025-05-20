<template>
  <div>
    <h2>Your Telegram Dialogs</h2>
    <p v-if="loading">Loading dialogs...</p>
    <p v-if="error">Error loading dialogs: {{ error }}</p>
    <ul v-if="dialogs.length">
      <li v-for="dialog in dialogs" :key="dialog.id">
        {{ dialog.title }} ({{ dialog.type }})
      </li>
    </ul>
    <p v-else-if="!loading && !error">No dialogs found.</p>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import axios from 'axios';

const props = defineProps({
  phoneNumber: {
    type: String,
    required: true
  }
});

const dialogs = ref([]);
const loading = ref(true);
const error = ref(null);

const fetchDialogs = async (phone) => {
  if (!phone) {
    dialogs.value = [];
    loading.value = false;
    return;
  }
  try {
    loading.value = true;
    error.value = null;
    // Assuming your backend is running on http://localhost:8000
    const response = await axios.get(`http://localhost:8000/api/dialogs?phone_number=${phone}`);
    dialogs.value = response.data;
  } catch (err) {
    console.error('Error fetching dialogs:', err);
    error.value = err.response?.data?.detail || 'Failed to fetch dialogs.';
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  // Fetch dialogs when the component is mounted, using the initial prop value
  fetchDialogs(props.phoneNumber);
});

// Watch for changes in the phoneNumber prop and refetch dialogs
watch(() => props.phoneNumber, (newPhoneNumber) => {
  fetchDialogs(newPhoneNumber);
});
</script>

<style scoped>
/* Add some basic styling */
ul {
  list-style: none;
  padding: 0;
}

li {
  margin-bottom: 10px;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 5px;
}
</style>