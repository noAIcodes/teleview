<template>
  <div :class="{ 'dark-mode': props.darkMode }" class="messages-view-wrapper">
    <header class="messages-header">
      <button @click="$emit('back-to-dialogs')" class="back-button" aria-label="Back to dialogs">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="icon">
          <path fill-rule="evenodd" d="M12.79 5.23a.75.75 0 01-.02 1.06L8.832 10l3.938 3.71a.75.75 0 11-1.04 1.08l-4.5-4.25a.75.75 0 010-1.08l4.5-4.25a.75.75 0 011.06.02z" clip-rule="evenodd" />
        </svg>
      </button>
      <div class="channel-info">
        <div v-if="channelInfoData">
          <h2 class="channel-name">{{ channelInfoData.title }}</h2>
          <p class="channel-id-type">
            <span class="channel-type">{{ channelInfoData.type }}</span>
            <span class="channel-id">ID: {{ channelInfoData.id }}</span>
          </p>
        </div>
        <div v-else-if="channelInfoError">
          <p class="channel-name error-text">Error loading channel info</p>
        </div>
        <div v-else>
          <p class="channel-name">Loading info...</p>
        </div>
      </div>
      <button @click="props.toggleDarkMode" class="header-dark-mode-toggle" aria-label="Toggle dark mode">
        {{ props.darkMode ? 'Light' : 'Dark' }}
      </button>
    </header>

    <div v-if="loading" class="status-container">
      <p class="status-text">Loading messages...</p>
      <!-- Modern spinner -->
    </div>
    <div v-else-if="error" class="status-container">
      <p class="status-text error-text">Error: {{ error }}</p>
      <button @click="fetchMessages(props.channelId)" class="retry-button">Try Again</button>
    </div>
    
    <div class="message-list-container" ref="messageListContainerRef">
      <div v-if="hasMoreMessages && !loading && messages.length > 0" class="load-more-container">
        <button @click="loadMoreMessages" :disabled="loadingMore" class="load-more-button">
          {{ loadingMore ? 'Loading...' : 'Load More Messages' }}
        </button>
      </div>
      <div v-if="messages.length" class="message-list">
        <div v-for="message in messages" :key="message.id"
             class="message-item"
             :class="{ 'sent': message.is_outgoing, 'received': !message.is_outgoing }">
          
          <div class="message-bubble">
            <div v-if="!message.is_outgoing && message.sender" class="message-sender-name">{{ message.sender }}</div>
            
            <p v-if="message.text" class="message-text-content">{{ message.text }}</p>
            
            <div v-if="message.media_type" class="message-media-content">
              <!-- Poll Display -->
              <div v-if="message.media_type === 'poll'" class="poll-display">
                <h4 class="poll-question-text">{{ message.poll_data.question }}</h4>
                <ul class="poll-options-list">
                  <li v-for="(option, index) in message.poll_data.options" :key="index" 
                      class="poll-option-item"
                      :class="{ 'correct': message.poll_data.type === 'quiz' && message.poll_data.quiz_correct_option_id === index }">
                    <span class="option-text-value">{{ option.text }}</span>
                    <span v-if="message.poll_data.total_voters" class="option-percentage-value">
                      {{ calculatePollPercentage(option.voters, message.poll_data.total_voters) }}%
                    </span>
                  </li>
                </ul>
                <div class="poll-meta-footer">
                  <span>{{ message.poll_data.type === 'quiz' ? 'Quiz' : 'Poll' }}</span>
                  <span>{{ message.poll_data.total_voters }} vote{{ message.poll_data.total_voters !== 1 ? 's' : '' }}</span>
                  <span v-if="message.poll_data.is_closed" class="closed-status">Closed</span>
                </div>
              </div>
              
              <!-- Image Display -->
              <div v-else-if="message.media_type === 'photo' && message.file_id" class="image-display">
                <img :src="getMediaUrl(message.file_id)" alt="Image" class="media-image-element" @error="imageLoadError" />
                <p v-if="message.file_name" class="media-filename-caption">{{ message.file_name }}</p>
              </div>

              <!-- Generic File/Media Display -->
              <div v-else-if="message.file_id" class="file-display">
                <p class="file-info">
                  <span class="file-type-icon">📄</span> <!-- Basic icon, can be improved -->
                  {{ message.file_name || message.media_type }}
                </p>
                <a :href="getMediaUrl(message.file_id, message.file_name)" target="_blank" download class="download-action-link">Download</a>
                <p v-if="message.mime_type" class="mime-type-caption">Type: {{ message.mime_type }}</p>
              </div>
              
              <!-- Fallback for unknown media -->
              <div v-else class="unknown-media-display">
                <p>Unsupported media type: {{ message.media_type }}</p>
                 <p v-if="message.file_name" class="media-filename-caption">{{ message.file_name }}</p>
              </div>
            </div>
            
            <div class="message-timestamp">{{ new Date(message.date * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }}</div>
          </div>
        </div>
      </div>
      <div v-else-if="!loading && !error" class="status-container">
        <p class="status-text">No messages in this channel yet.</p>
      </div>
    </div>

    <footer class="message-input-footer">
      <textarea v-model="newMessageText" placeholder="Type a message..." class="message-compose-input" @keydown.enter.prevent="sendMessage"></textarea>
      <button @click="sendMessage" class="send-action-button" aria-label="Send message">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="icon">
          <path d="M3.105 3.105a.75.75 0 01.815-.398l13.982 4.66a.75.75 0 010 1.268l-13.982 4.66a.75.75 0 01-1.213-.878l2.598-3.599a.75.75 0 000-1.038L2.707 4.006a.75.75 0 01.4-.899z" />
        </svg>
      </button>
    </footer>
  </div>
</template>

<script setup>
// Added ref for new message text and message list container for scrolling
import { ref, onMounted, watch, defineProps, defineEmits, nextTick } from 'vue';
import axios from 'axios';

const props = defineProps({
  channelId: {
    type: Number,
    required: true
  },
  darkMode: {
    type: Boolean,
    default: false // Default to light mode now
  },
  toggleDarkMode: { // Added toggleDarkMode prop
    type: Function,
    required: true
  }
});

const emit = defineEmits(['back-to-dialogs']);

const messages = ref([]);
const loading = ref(true); // For initial load
const error = ref(null);
const newMessageText = ref('');
const messageListContainerRef = ref(null);
const channelInfoData = ref(null);
const channelInfoError = ref(null);

const messagesPerPage = 10;
const currentOffset = ref(0);
const hasMoreMessages = ref(true);
const loadingMore = ref(false); // For "load more" action

const scrollToBottom = async (force = false) => {
  await nextTick();
  const container = messageListContainerRef.value;
  if (container) {
    // Only scroll to bottom if it's an initial load or a new message sent by user
    // For loading more, user might want to stay at their current scroll position.
    // However, if force is true (e.g. new channel loaded), scroll to bottom.
    if (force || (!loadingMore.value && currentOffset.value <= messagesPerPage)) {
       container.scrollTop = container.scrollHeight;
    }
  }
};

const getMediaUrl = (fileId, fileName = null) => {
  let url = `http://localhost:8000/api/media/${fileId}`;
  return url;
};

const imageLoadError = (event) => {
  console.error("Error loading image:", event.target.src);
  event.target.alt = "Image failed to load";
};

const calculatePollPercentage = (voters, total_voters) => {
  if (!total_voters || total_voters === 0) return 0;
  return Math.round((voters / total_voters) * 100);
};

const fetchChannelInfo = async (id) => {
  if (!id) {
    channelInfoData.value = null;
    channelInfoError.value = null;
    return;
  }
  try {
    channelInfoError.value = null;
    const response = await axios.get(`http://localhost:8000/api/channels/${id}/info`);
    channelInfoData.value = response.data;
  } catch (err) {
    console.error('Error fetching channel info:', err);
    channelInfoData.value = null;
    channelInfoError.value = err.response?.data?.detail || 'Failed to load channel info.';
  }
};

const fetchMessages = async (channel, isLoadingMore = false) => {
  if (!channel) {
    messages.value = [];
    loading.value = false;
    loadingMore.value = false;
    return;
  }

  if (isLoadingMore) {
    loadingMore.value = true;
  } else {
    loading.value = true;
    currentOffset.value = 0; // Reset offset for initial load
    messages.value = []; // Clear messages for initial load of a channel
  }
  error.value = null;

  try {
    const response = await axios.get(`http://localhost:8000/api/channels/${channel}/messages?limit=${messagesPerPage}&offset=${currentOffset.value}`);
    const newMessages = response.data.map((msg, index) => ({
      ...msg,
      is_outgoing: msg.is_outgoing !== undefined ? msg.is_outgoing : ((currentOffset.value + index) % 2 === 0), // Keep demo logic if needed
      poll_data: msg.media_type === 'poll' ? (msg.poll_data || { options: [], question: 'Poll Question Missing' }) : null
    }));

    if (isLoadingMore) {
      messages.value = [...newMessages, ...messages.value]; // Prepend older messages
    } else {
      messages.value = newMessages;
    }

    currentOffset.value += newMessages.length;
    hasMoreMessages.value = newMessages.length === messagesPerPage;

    if (!isLoadingMore) {
      scrollToBottom(true); // Scroll to bottom on initial load
    }

  } catch (err) {
    console.error('Error fetching messages:', err);
    error.value = err.response?.data?.detail || 'Failed to fetch messages.';
  } finally {
    if (isLoadingMore) {
      loadingMore.value = false;
    } else {
      loading.value = false;
    }
  }
};

const loadMoreMessages = () => {
  if (hasMoreMessages.value && !loadingMore.value && !loading.value) {
    fetchMessages(props.channelId, true);
  }
};

const sendMessage = () => {
  if (newMessageText.value.trim() === '') return;
  console.log('Sending message:', newMessageText.value);
  messages.value.push({
    id: Date.now(),
    text: newMessageText.value,
    sender: 'You',
    date: Math.floor(Date.now() / 1000),
    is_outgoing: true,
    media_type: null,
  });
  newMessageText.value = '';
  scrollToBottom(true); // Force scroll to bottom after sending a message
};

onMounted(() => {
  fetchChannelInfo(props.channelId);
  fetchMessages(props.channelId); // Initial fetch
});

watch(() => props.channelId, (newChannelId) => {
  fetchChannelInfo(newChannelId);
  messages.value = []; // Clear previous messages
  channelInfoData.value = null; // Clear previous channel info
  currentOffset.value = 0; // Reset offset
  hasMoreMessages.value = true; // Assume there are messages
  error.value = null; // Clear previous errors
  fetchMessages(newChannelId); // Fetch for new channel
});

// Removed the generic watch on messages for scrollToBottom, handled more explicitly now.

</script>

<style scoped>
.messages-view-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%; /* Fill available height from App.vue */
  background-color: var(--bg-color);
  color: var(--text-color);
  overflow: hidden;
}

.messages-header {
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--border-color);
  background-color: var(--surface-color);
  flex-shrink: 0; /* Prevent header from shrinking */
}
.dark-mode .messages-header {
  background-color: var(--surface-color);
}

.back-button {
  background: none;
  border: none;
  color: var(--primary-color);
  padding: 0.5rem;
  margin-right: 0.75rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}
.back-button:hover {
  background-color: rgba(0,0,0,0.05);
}
.dark-mode .back-button {
  color: var(--primary-color);
}
.dark-mode .back-button:hover {
  background-color: rgba(255,255,255,0.1);
}
.back-button .icon {
  width: 24px; /* Increased size */
  height: 24px;
}

.channel-info {
  flex-grow: 1;
  margin-right: 1rem; /* Add some space between title and button */
}
.channel-name {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-color);
  text-transform: none;
  white-space: nowrap; /* Prevent wrapping if channel name is long */
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.2; /* Adjust if title wraps */
  margin-bottom: 0.1rem; /* Space between title and id/type */
}

.channel-id-type {
  font-size: 0.75rem;
  color: var(--text-secondary-color);
  display: flex;
  gap: 0.5rem; /* Space between type and ID */
  align-items: center;
}

.channel-type {
  text-transform: capitalize; /* Capitalize first letter of type e.g. "channel", "user" */
}

.channel-id {
  font-size: 0.7rem; /* Smaller font for ID */
  opacity: 0.8;
}

.header-dark-mode-toggle {
  /* Similar to DialogList, but can be styled independently if needed */
  padding: 0.4rem 0.8rem;
  font-size: 0.8rem;
  background-color: var(--surface-color);
  color: var(--text-secondary-color);
  border: 1px solid var(--border-color);
  border-radius: 0.375rem;
  cursor: pointer;
  flex-shrink: 0; /* Prevent button from shrinking */
  box-shadow: none;
}
.header-dark-mode-toggle:hover {
  background-color: var(--border-color);
  color: var(--text-color);
}
.dark-mode .header-dark-mode-toggle {
  background-color: var(--surface-color);
  color: var(--text-secondary-color);
  border: 1px solid var(--border-color);
}
.dark-mode .header-dark-mode-toggle:hover {
  background-color: var(--border-color);
  color: var(--text-color);
}

.status-container {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 1rem;
  text-align: center;
}
.status-text {
  font-size: 0.95rem;
  color: var(--text-secondary-color);
  margin-bottom: 0.75rem;
}
.error-text {
  color: #ef4444; /* Tailwind red-500 */
}
.dark-mode .error-text {
  color: #f87171; /* Tailwind red-400 */
}
.retry-button {
  /* Uses global button styles */
  padding: 0.4rem 0.8rem;
  font-size: 0.85rem;
}

.message-list-container {
  flex-grow: 1;
  overflow-y: auto;
  padding: 1rem 0.75rem;
  display: flex;
  flex-direction: column;
}

.message-list {
  width: 100%;
}

.message-item {
  display: flex;
  margin-bottom: 0.75rem;
}
.message-item.sent {
  justify-content: flex-end;
}
.message-item.received {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 70%; /* Max width of bubble */
  padding: 0.5rem 0.75rem;
  border-radius: 1rem; /* Rounded corners */
  word-wrap: break-word;
  position: relative; /* For timestamp */
}

.message-item.sent .message-bubble {
  background-color: var(--primary-color);
  color: var(--button-text-color); /* Usually white or light text on primary bg */
  border-bottom-right-radius: 0.25rem; /* "Tail" for sent messages */
}
.dark-mode .message-item.sent .message-bubble {
  background-color: var(--primary-color); /* Dark mode primary */
}

.message-item.received .message-bubble {
  background-color: var(--surface-color);
  color: var(--text-color);
  border: 1px solid var(--border-color);
  border-bottom-left-radius: 0.25rem; /* "Tail" for received messages */
}
.dark-mode .message-item.received .message-bubble {
  background-color: var(--surface-color); /* Dark mode surface */
  border: 1px solid var(--border-color);
}

.message-sender-name {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--primary-color); /* Or a distinct color */
  margin-bottom: 0.2rem;
}
.dark-mode .message-sender-name {
  color: var(--primary-color);
}


.message-text-content {
  font-size: 0.95rem;
  line-height: 1.5;
  margin:0; /* Reset p margin */
  white-space: pre-wrap; /* Preserve line breaks */
}

.message-media-content {
  margin-top: 0.5rem;
}

.media-image-element {
  max-width: 100%;
  border-radius: 0.5rem;
  display: block;
  margin-bottom: 0.25rem;
}
.media-filename-caption, .mime-type-caption {
  font-size: 0.75rem;
  color: var(--text-secondary-color);
  opacity: 0.8;
}
.dark-mode .media-filename-caption, .dark-mode .mime-type-caption {
   color: var(--text-secondary-color);
}


.poll-display {
  padding: 0.5rem;
  border: 1px solid var(--border-color);
  border-radius: 0.5rem;
  background-color: var(--bg-color); /* Slightly different from bubble */
}
.dark-mode .poll-display {
  background-color: var(--input-bg-color); /* Darker for contrast */
}
.poll-question-text {
  font-weight: 500;
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
  color: var(--text-color);
}
.poll-options-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.poll-option-item {
  padding: 0.3rem 0;
  font-size: 0.85rem;
  display: flex;
  justify-content: space-between;
  border-bottom: 1px solid var(--border-color);
}
.poll-option-item:last-child {
  border-bottom: none;
}
.poll-option-item.correct {
  font-weight: bold;
  color: #16a34a; /* Green for correct quiz option */
}
.dark-mode .poll-option-item.correct {
  color: #4ade80;
}
.option-text-value { color: var(--text-color); }
.option-percentage-value { color: var(--text-secondary-color); font-size: 0.8rem; }

.poll-meta-footer {
  font-size: 0.75rem;
  color: var(--text-secondary-color);
  margin-top: 0.5rem;
  display: flex;
  justify-content: space-between;
}
.closed-status { font-weight: bold; }

.file-display {
  padding: 0.5rem;
  border: 1px solid var(--border-color);
  border-radius: 0.5rem;
  background-color: var(--bg-color);
}
.dark-mode .file-display {
  background-color: var(--input-bg-color);
}
.file-info {
  font-size: 0.9rem;
  margin-bottom: 0.3rem;
  display: flex;
  align-items: center;
}
.file-type-icon { margin-right: 0.3rem; }
.download-action-link {
  font-size: 0.85rem;
  font-weight: 500;
}

.message-timestamp {
  font-size: 0.7rem;
  color: var(--text-secondary-color);
  text-align: right;
  margin-top: 0.25rem;
  opacity: 0.8;
}
.message-item.sent .message-timestamp {
  color: var(--button-text-color); /* Light timestamp on dark bubble */
  opacity: 0.7;
}
.dark-mode .message-item.sent .message-timestamp {
  color: var(--button-text-color);
}


.message-input-footer {
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  border-top: 1px solid var(--border-color);
  background-color: var(--surface-color); /* Consistent with header */
  flex-shrink: 0; /* Prevent footer from shrinking */
}
.dark-mode .message-input-footer {
  background-color: var(--surface-color);
}

.message-compose-input {
  flex-grow: 1;
  /* Uses global textarea styles */
  padding: 0.6rem 0.8rem;
  border-radius: 1.5rem; /* Pill shape */
  resize: none;
  min-height: 40px; /* Adjust as needed */
  max-height: 120px; /* Limit expansion */
  overflow-y: auto;
  margin-right: 0.75rem;
}

.send-action-button {
  background: var(--primary-color);
  border: none;
  color: white;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  padding: 0; /* Reset padding for icon button */
}
.send-action-button:hover {
  background: var(--primary-hover-color);
}
.send-action-button .icon {
  width: 20px;
  height: 20px;
}

.load-more-container {
  display: flex;
  justify-content: center;
  padding: 0.75rem 0;
}

.load-more-button {
  padding: 0.5rem 1rem;
  font-size: 0.85rem;
  background-color: var(--surface-color);
  color: var(--primary-color);
  border: 1px solid var(--primary-color);
  border-radius: 0.375rem;
  cursor: pointer;
  transition: background-color 0.2s, color 0.2s;
}

.load-more-button:hover:not(:disabled) {
  background-color: var(--primary-color);
  color: var(--button-text-color);
}

.load-more-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}
.dark-mode .load-more-button {
  background-color: var(--surface-color);
  color: var(--primary-color);
  border: 1px solid var(--primary-color);
}
.dark-mode .load-more-button:hover:not(:disabled) {
  background-color: var(--primary-color);
  color: var(--button-text-color);
}

</style>
