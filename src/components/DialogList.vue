<template>
  <div :class="{ 'dark-mode': props.darkMode }" class="dialog-list-wrapper">
    <header class="dialog-list-header">
      <h1 class="main-title">Chats</h1>
      <button @click="props.toggleDarkMode" class="header-dark-mode-toggle" aria-label="Toggle dark mode">
        {{ props.darkMode ? 'Light Mode' : 'Dark Mode' }}
      </button>
    </header>
    <div class="search-controls-container">
      <input type="search" v-model="searchTerm" placeholder="Search chats..." class="search-input" />
    </div>

    <div v-if="loading" class="status-container">
      <p class="status-message">Loading chats...</p>
      <!-- Add a modern spinner/loader component here if desired -->
    </div>
    <div v-else-if="error" class="status-container">
      <p class="status-message error-message">Error: {{ error }}</p>
      <button @click="fetchDialogs" class="retry-button">Try Again</button>
    </div>
    <div v-else-if="filteredDialogs.length" class="dialogs-scroll-container">
      <ul class="dialog-list">
        <li v-for="dialog in filteredDialogs" :key="dialog.id" @click="selectDialog(dialog.id)" class="dialog-item">
          <div class="dialog-avatar-placeholder">
            <!-- Placeholder for an avatar - could be initials or an icon -->
            <span>{{ dialog.title ? dialog.title.charAt(0).toUpperCase() : '?' }}</span>
          </div>
          <div class="dialog-info">
            <h3 class="dialog-title">{{ dialog.title }}</h3>
            <p class="dialog-meta">Type: {{ dialog.type }} | ID: {{ dialog.id }}</p>
          </div>
          <!-- Could add unread count or last message preview here -->
        </li>
      </ul>
    </div>
    <div v-else class="status-container">
      <p class="status-message">No chats found{{ searchTerm ? ' matching your search' : '' }}.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, defineEmits, computed, defineProps } from 'vue'; // Added defineProps
import axios from 'axios';

const props = defineProps({
  darkMode: {
    type: Boolean,
    required: true
  },
  toggleDarkMode: { // Added toggleDarkMode prop
    type: Function,
    required: true
  }
});

const dialogs = ref([]);
const loading = ref(true);
const error = ref(null);
const searchTerm = ref('');
// Removed local darkMode ref: const darkMode = ref(false);

const emit = defineEmits(['select-channel']);

const selectDialog = (channelId) => {
  emit('select-channel', channelId);
};

const fetchDialogs = async () => {
  try {
    loading.value = true;
    error.value = null;
    const response = await axios.get(`http://localhost:8000/api/dialogs`);
    dialogs.value = response.data;
  } catch (err) {
    console.error('Error fetching dialogs:', err);
    error.value = err.response?.data?.detail || 'Failed to fetch dialogs.';
  } finally {
    loading.value = false;
  }
};

const filteredDialogs = computed(() => {
  if (!searchTerm.value) {
    return dialogs.value;
  }
  return dialogs.value.filter(dialog =>
    dialog.title.toLowerCase().includes(searchTerm.value.toLowerCase()) ||
    String(dialog.id).toLowerCase().includes(searchTerm.value.toLowerCase())
  );
});

// Removed toggleDarkMode method

onMounted(() => {
  fetchDialogs();
  // Removed localStorage logic for dark mode as it's now a prop
});
</script>

<style scoped>
.dialog-list-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%; /* Fill available height */
  background-color: var(--bg-color);
  color: var(--text-color);
  /* overflow: hidden; */ /* Prevent overall page scroll, manage scrolling internally */
}

.dialog-list-header {
  display: flex; /* Added for layout */
  justify-content: space-between; /* Added for layout */
  align-items: center; /* Added for layout */
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--border-color);
  background-color: var(--surface-color);
  flex-shrink: 0; /* Prevent header shrinking */
}
.dark-mode .dialog-list-header {
  background-color: var(--surface-color);
}

.main-title {
  font-size: 1.5rem; /* Adjusted size */
  font-weight: 600;
  color: var(--text-color);
  text-transform: none;
  margin: 0; /* Removed bottom margin */
}

.header-dark-mode-toggle {
  /* Using global button styles as a base, but can be more specific */
  padding: 0.4rem 0.8rem;
  font-size: 0.8rem;
  background-color: var(--surface-color);
  color: var(--text-secondary-color);
  border: 1px solid var(--border-color);
  box-shadow: none; /* Remove default button shadow if desired for header */
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

.search-controls-container { /* New container for search input */
  padding: 0.75rem 1.25rem;
  border-bottom: 1px solid var(--border-color);
  background-color: var(--bg-color); /* Match main background */
  flex-shrink: 0;
}

.search-input {
  /* Using global input styles from style.css */
  padding: 0.6rem 1rem;
  font-size: 0.95rem; /* Adjusted size */
}
.search-input::placeholder {
  color: var(--text-secondary-color);
}



.status-container {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 2rem;
  text-align: center;
}

.status-message {
  font-size: 1rem;
  color: var(--text-secondary-color);
  margin-bottom: 1rem;
}

.error-message {
  color: #ef4444; /* Tailwind red-500 */
}
.dark-mode .error-message {
  color: #f87171; /* Tailwind red-400 */
}

.retry-button {
  /* Uses global button styles */
  background-color: var(--primary-color);
  color: var(--button-text-color);
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
}
.retry-button:hover {
   background-color: var(--primary-hover-color);
}


.dialogs-scroll-container {
  flex-grow: 1;
  overflow-y: auto; /* Enable scrolling for the list only */
  min-height: 0; /* Added to help with flex scrolling */
}

.dialog-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.dialog-item {
  display: flex;
  align-items: center;
  padding: 0.75rem 1.25rem;
  border-bottom: 1px solid var(--border-color);
  cursor: pointer;
  transition: background-color 0.15s ease-in-out;
}

.dialog-item:hover {
  background-color: var(--surface-color);
}
.dark-mode .dialog-item:hover {
  background-color: rgba(255, 255, 255, 0.05); /* Subtle hover for dark mode */
}

.dialog-item:last-child {
  border-bottom: none;
}

.dialog-avatar-placeholder {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: var(--primary-color);
  color: var(--button-text-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 500;
  font-size: 1.1rem;
  margin-right: 0.75rem;
  flex-shrink: 0; /* Prevent shrinking */
}
.dark-mode .dialog-avatar-placeholder {
  background-color: var(--primary-color); /* Use dark mode primary color */
}


.dialog-info {
  flex-grow: 1;
  overflow: hidden; /* For text ellipsis if needed */
}

.dialog-title {
  font-size: 1rem;
  font-weight: 500; /* Medium weight for titles */
  color: var(--text-color);
  margin-bottom: 0.15rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-transform: none;
}

.dialog-meta {
  font-size: 0.8rem;
  color: var(--text-secondary-color);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 0; /* Override default p margin */
}

/* Ensure dark-mode class from prop correctly applies variables */
.dialog-list-wrapper.dark-mode {
  background-color: var(--bg-color); /* This will be dark bg */
  color: var(--text-color); /* This will be dark text */
}
/* Other elements within .dialog-list-wrapper.dark-mode will inherit or use their specific dark mode variable styles */

</style>
