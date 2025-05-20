<template>
  <div>
    <h2>Your Telegram Dialogs</h2>
    <p v-if="loading">Loading dialogs...</p>
    <p v-if="error">Error loading dialogs: {{ error }}</p>
    <ul v-if="dialogs.length">
      <li v-for="dialog in dialogs" :key="dialog.id" @click="selectDialog(dialog.id)" class="dialog-item">
        {{ dialog.title }} ({{ dialog.type }})
      </li>
    </ul>
    <p v-else-if="!loading && !error">No dialogs found.</p>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, defineEmits } from 'vue';
import axios from 'axios';

const dialogs = ref([]);
const loading = ref(true);
const error = ref(null);

const emit = defineEmits(['select-channel']);

const selectDialog = (channelId) => {
  emit('select-channel', channelId);
};

const fetchDialogs = async () => {
  // phone parameter removed
  try {
    loading.value = true;
    error.value = null;
    // Assuming your backend is running on http://localhost:8000
    // phone_number query parameter removed
    const response = await axios.get(`http://localhost:8000/api/dialogs`);
    dialogs.value = response.data;
  } catch (err) {
    console.error('Error fetching dialogs:', err);
    error.value = err.response?.data?.detail || 'Failed to fetch dialogs.';
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  // Fetch dialogs when the component is mounted
  fetchDialogs(); // No longer passes props.phoneNumber
});

// Watcher for phoneNumber is removed
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

.dialog-item {
  cursor: pointer;
}

.dialog-item:hover {
  background-color: #f0f0f0;
}
</style>
