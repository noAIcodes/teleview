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
          
          <!-- Poll display -->
          <div v-if="message.media_type === 'poll'" class="poll-container">
            <h3>{{ message.poll_data.question }}</h3>
            <div class="poll-options">
              <div 
                v-for="(option, index) in message.poll_data.options" 
                :key="index"
                class="poll-option"
                :class="{ 'correct-option': message.poll_data.type === 'quiz' && message.poll_data.quiz_correct_option_id === index }"
              >
                <span class="option-text">{{ option.text }}</span>
                <span v-if="message.poll_data.total_voters" class="option-percentage">
                  <!-- If we had vote counts per option, we could calculate percentages here -->
                </span>
              </div>
            </div>
            <div class="poll-footer">
              <span v-if="message.poll_data.is_closed" class="poll-status">Poll closed</span>
              <span v-else class="poll-status">Poll active</span>
              <span v-if="message.poll_data.total_voters" class="poll-voters">
                {{ message.poll_data.total_voters }} voter{{ message.poll_data.total_voters !== 1 ? 's' : '' }}
              </span>
              <span class="poll-type">
                {{ message.poll_data.type === 'quiz' ? 'Quiz' : 'Regular poll' }}
                {{ message.poll_data.allows_multiple_answers ? ' (multiple answers allowed)' : '' }}
                {{ message.poll_data.is_anonymous ? ' (anonymous)' : ' (not anonymous)' }}
              </span>
            </div>
          </div>
          
          <!-- Other media types -->
          <div v-else-if="message.media_type === 'photo' && message.file_id">
            <!-- phoneNumber removed from getMediaUrl call -->
            <img :src="getMediaUrl(message.file_id)" alt="Image" class="message-image" @error="imageLoadError" />
            <p v-if="message.file_name">Filename: {{ message.file_name }}</p>
          </div>
          <div v-else-if="['video', 'document', 'audio', 'voice', 'sticker'].includes(message.media_type) && message.file_id">
            <p>
              File: {{ message.file_name || message.media_type }}
              <!-- phoneNumber removed from getMediaUrl call -->
              <a :href="getMediaUrl(message.file_id, message.file_name)" target="_blank" download>Download</a>
            </p>
            <p v-if="message.mime_type">MIME Type: {{ message.mime_type }}</p>
          </div>
          <div v-else>
             <p v-if="message.file_name">File: {{ message.file_name }}</p>
             <p v-if="message.mime_type">MIME Type: {{ message.mime_type }}</p>
             <!-- Fallback for unhandled media or media without file_id -->
          </div>
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
  // phoneNumber prop removed
  channelId: {
    type: Number,
    required: true
  }
});

const emit = defineEmits(['back-to-dialogs']);

const messages = ref([]);
const loading = ref(true);
const error = ref(null);

// phoneNumber parameter removed from getMediaUrl
const getMediaUrl = (fileId, fileName = null) => {
  // phone_number query parameter removed from URL
  let url = `http://localhost:8000/api/media/${fileId}`;
  if (fileName) {
    // url += `&download=${encodeURIComponent(fileName)}`; // Usually handled by backend Content-Disposition
  }
  return url;
};

const imageLoadError = (event) => {
  console.error("Error loading image:", event.target.src);
  event.target.alt = "Failed to load image";
};

// phone parameter removed from fetchMessages
const fetchMessages = async (channel) => {
  if (!channel) { // Check for phone removed
    messages.value = [];
    loading.value = false;
    return;
  }
  try {
    loading.value = true;
    error.value = null;
    // phone_number query parameter removed from API call
    const response = await axios.get(`http://localhost:8000/api/channels/${channel}/messages`);
    messages.value = response.data;
  } catch (err) {
    console.error('Error fetching messages:', err);
    error.value = err.response?.data?.detail || 'Failed to fetch messages.';
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  // Fetch messages using only props.channelId
  fetchMessages(props.channelId);
});

// Watch for changes in props.channelId only
watch(() => props.channelId, (newChannelId) => {
  fetchMessages(newChannelId);
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

.message-image {
  max-width: 100%;
  max-height: 300px;
  border-radius: 4px;
  margin-top: 5px;
  border: 1px solid #eee;
}

.poll-container {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 15px;
  margin-top: 10px;
  background-color: #f9f9f9;
}

.poll-container h3 {
  margin-top: 0;
  margin-bottom: 10px;
  font-size: 1.1em;
}

.poll-options {
  margin-bottom: 10px;
}

.poll-option {
  background-color: #fff;
  border: 1px solid #ddd;
  padding: 8px 12px;
  margin-bottom: 5px;
  border-radius: 4px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.poll-option.correct-option {
  border-left: 5px solid #4CAF50; /* Green border for correct quiz option */
  background-color: #e8f5e9;
}

.option-text {
  flex-grow: 1;
}

.option-percentage {
  font-size: 0.9em;
  color: #555;
  margin-left: 10px;
}

.poll-footer {
  font-size: 0.85em;
  color: #777;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.poll-status,
.poll-voters,
.poll-type {
  background-color: #efefef;
  padding: 3px 8px;
  border-radius: 3px;
}
</style>
