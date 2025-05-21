<script setup>
import { ref } from 'vue';
import DialogList from './components/DialogList.vue';
import ChannelMessages from './components/ChannelMessages.vue';

const selectedChannelId = ref(null);
const darkMode = ref(true); // Default to dark mode

const toggleDarkMode = () => {
  darkMode.value = !darkMode.value;
};

const selectChannel = (channelId) => {
  selectedChannelId.value = channelId;
};

const backToDialogs = () => {
  selectedChannelId.value = null;
};
</script>

<template>
  <!-- 
    The main div now directly controls visibility of DialogList or ChannelMessages
    based on selectedChannelId, assuming authentication is handled by the backend.
  -->
  <div :class="{ 'dark-mode-app': darkMode }" class="app-shell">
    <!-- Toolbar removed, toggle button will be in child components -->
    <div class="content-area">
      <div v-if="selectedChannelId === null">
        <DialogList 
          @select-channel="selectChannel" 
          :dark-mode="darkMode" 
          :toggle-dark-mode="toggleDarkMode" 
        />
      </div>
      <div v-else>
        <ChannelMessages
          :channel-id="selectedChannelId"
          @back-to-dialogs="backToDialogs"
          :dark-mode="darkMode"
          :toggle-dark-mode="toggleDarkMode"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.app-shell {
  display: flex;
  flex-direction: column;
  height: 100vh; /* Ensure app shell takes full viewport height */
  background-color: var(--bg-color); /* Apply global background */
}

.content-area {
  flex-grow: 1; /* Allows content area to fill available space */
  display: flex; /* To make sure child components can also flex grow */
  flex-direction: column;
  overflow: hidden; /* Prevent double scrollbars if children manage their own */
}

/* Ensure DialogList and ChannelMessages fill the content-area */
.content-area > div {
  flex-grow: 1;
  display: flex; /* Important for child components to take full height */
  flex-direction: column;
}

/* Styles for .dark-mode-toggle are removed as the button is no longer in this component */
</style>
