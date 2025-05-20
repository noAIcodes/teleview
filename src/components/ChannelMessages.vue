<template>
  <div>
    <h2>Messages from Channel {{ channelId }}</h2>
    <button @click="$emit('back-to-dialogs')">Back to Dialogs</button>
    <p v-if="loading">Loading messages...</p>
    <p v-if="error">Error loading messages: {{ error }}</p>
    <ul v-if="messages.length">
      <li v-for="message in messages" :key="message.id">
        <p><strong>{{ message.sender }} ({{ new Date(message.date * 1000).toLocaleString() }})</strong>: {{ message.text }}</p>
        <div v-if="message.media_type">
          <p><em>Media Type: {{ message.media_type }}</em></p>
          <p v-if="message.file_name">File: {{ message.file_name }}</p>
          <p v-if="message.mime_type">MIME Type: {{ message.mime_type }}</p>
          <!-- TODO: Add logic to display media (e.g., image tags, video players, download links) -->
        </div>
      </li>
    </ul>
    <p v-else-if="!loading && !error">No messages found.</p>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, defineProps, defineEmits } from 'vue';
import axios from 'axios';

const props = defineProps({
  phoneNumber: {
    type: String,
    required: true
  },
  channelId: {
    type: Number,
    required: true
  }
});

const emit = defineEmits(['back-to-dialogs']);

const messages = ref([]);
const loading = ref(true);
const error = ref(null);

const fetchMessages = async (phone, channel) => {
  if (!phone || !channel) {
    messages.value = [];
    loading.value = false;
    return;
  }
  try {
    loading.value = true;
    error.value = null;
    // Assuming your backend is running on http://localhost:8000
    const response = await axios.get(`http://localhost:8000/api/channels/${channel}/messages?phone_number=${phone}`);
    messages.value = response.data;
  } catch (err) {
    console.error('Error fetching messages:', err);
    error.value = err.response?.data?.detail || 'Failed to fetch messages.';
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  // Fetch messages when the component is mounted, using the initial prop values
  fetchMessages(props.phoneNumber, props.channelId);
});

// Watch for changes in props and refetch messages
watch(() => [props.phoneNumber, props.channelId], ([newPhoneNumber, newChannelId]) => {
  fetchMessages(newPhoneNumber, newChannelId);
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