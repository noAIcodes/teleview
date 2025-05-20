<script setup>
import { ref } from 'vue';
import HelloWorld from './components/HelloWorld.vue'
import DialogList from './components/DialogList.vue'
import AuthForm from './components/AuthForm.vue';
import ChannelMessages from './components/ChannelMessages.vue';

const isAuthenticated = ref(false);
const authenticatedPhoneNumber = ref(null);
const selectedChannelId = ref(null);

const handleAuthenticated = (phoneNumber) => {
  authenticatedPhoneNumber.value = phoneNumber;
  isAuthenticated.value = true;
};

const selectChannel = (channelId) => {
  selectedChannelId.value = channelId;
};

const backToDialogs = () => {
  selectedChannelId.value = null;
};
</script>

<template>
  <div>
    <a href="https://vite.dev" target="_blank">
      <img src="/vite.svg" class="logo" alt="Vite logo" />
    </a>
    <a href="https://vuejs.org/" target="_blank">
      <img src="./assets/vue.svg" class="logo vue" alt="Vue logo" />
    </a>
  </div>
  <HelloWorld msg="Vite + Vue" />

  <div v-if="isAuthenticated">
    <div v-if="selectedChannelId === null">
      <DialogList :phone-number="authenticatedPhoneNumber" @select-channel="selectChannel" />
    </div>
    <div v-else>
      <ChannelMessages
        :phone-number="authenticatedPhoneNumber"
        :channel-id="selectedChannelId"
        @back-to-dialogs="backToDialogs"
      />
    </div>
  </div>
  <div v-else>
    <AuthForm @authenticated="handleAuthenticated" />
  </div>
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
