<script setup>
import { ref } from 'vue';
import DialogList from './components/DialogList.vue';
import ChannelMessages from './components/ChannelMessages.vue';
// AuthForm import is removed

// isAuthenticated and authenticatedPhoneNumber are removed
const selectedChannelId = ref(null);

// handleAuthenticated is removed

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
  <div>
    <div v-if="selectedChannelId === null">
      <!-- DialogList no longer needs phone-number prop -->
      <DialogList @select-channel="selectChannel" />
    </div>
    <div v-else>
      <!-- ChannelMessages no longer needs phone-number prop -->
      <ChannelMessages
        :channel-id="selectedChannelId"
        @back-to-dialogs="backToDialogs"
      />
    </div>
  </div>
  <!-- AuthForm usage is removed -->
</template>

<style scoped>
.logo {
  height: 6em;
  padding: 1.5em;
  will-change: filter;
  transition: filter 300ms;
}
.logo:hover {
  filter: drop-shadow(0 0 2em #646cffaa);
}
.logo.vue:hover {
  filter: drop-shadow(0 0 2em #42b883aa);
}
</style>
