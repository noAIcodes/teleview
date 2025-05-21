<template>
  <div id="app" class="p-4 max-w-2xl mx-auto">
    <header class="mb-8">
      <h1 class="text-3xl font-bold text-center text-blue-600">
        Telegram Channel Viewer
      </h1>
    </header>

    <!-- Authentication sections (Step 1 and Step 2) are removed -->

    <section class="p-4 border rounded-lg shadow-md bg-white">
      <h2 class="text-xl font-semibold mb-3 text-gray-700">
        Your Dialogs
      </h2>
      <button
        @click="fetchDialogs"
        class="w-full bg-purple-500 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded-md mb-3 disabled:opacity-50"
        :disabled="dialogs.isLoading"
      >
        {{ dialogs.isLoading ? "Loading Dialogs..." : "Fetch My Dialogs" }}
      </button>
      <p v-if="dialogs.error" class="text-red-500 mt-2 text-sm">
        {{ dialogs.error }}
      </p>

      <ul v-if="dialogs.list.length > 0" class="space-y-2 mt-3">
        <li
          v-for="dialog in dialogs.list"
          :key="dialog.id"
          @click="selectDialog(dialog)"
          class="p-4 rounded-lg hover:bg-gray-100 cursor-pointer border border-gray-200 shadow-sm transition-all"
          :class="{
            'bg-blue-100 border-blue-400 shadow-md':
              dialogs.selected && dialogs.selected.id === dialog.id,
            'bg-white': !dialogs.selected || dialogs.selected.id !== dialog.id
          }"
        >
          <div class="flex justify-between items-center">
            <p class="font-semibold text-gray-800 truncate" :title="dialog.title">{{ dialog.title }}</p>
            <span
              class="text-xs font-medium px-2 py-0.5 rounded-full"
              :class="{
                'bg-green-200 text-green-800': dialog.type === 'user' || dialog.type === 'bot',
                'bg-indigo-200 text-indigo-800': dialog.type === 'group' || dialog.type === 'supergroup',
                'bg-pink-200 text-pink-800': dialog.type === 'channel',
                'bg-gray-200 text-gray-800': !['user', 'bot', 'group', 'supergroup', 'channel'].includes(dialog.type)
              }"
            >
              {{ dialog.type }}
            </span>
          </div>
          <p class="text-xs text-gray-500 mt-1">ID: {{ dialog.id }}</p>
        </li>
      </ul>
      <p
        v-if="
          !dialogs.isLoading &&
          dialogs.list.length === 0 &&
          dialogs.hasAttemptedFetch
        "
        class="text-gray-600 mt-4 text-center"
      >
        No dialogs found. Click "Fetch My Dialogs" to load.
      </p>
    </section>

    <section
      v-if="dialogs.selected"
      class="mt-6 p-4 border rounded-lg shadow-md bg-white"
    >
      <div class="mb-3 pb-2 border-b border-gray-200">
        <h2 class="text-xl font-semibold text-gray-800 inline">
          Viewing: <span class="font-bold text-blue-600">{{ dialogs.selected.title }}</span>
        </h2>
        <p class="text-sm text-gray-500 inline ml-2">
          (Type: {{ dialogs.selected.type }} | ID: {{ dialogs.selected.id }})
        </p>
      </div>
      <!-- Message display will be implemented next. -->
      <!-- Placeholder for messages -->
      <ChannelMessages :channelId="dialogs.selected ? dialogs.selected.id : null" />
    </section>
  </div>
</template>

<script>
import axios from "axios";
import ChannelMessages from "./components/ChannelMessages.vue"; // Import the component

const API_BASE_URL = "http://localhost:8000/api";

export default {
  name: "App",
  components: { // Register the component
    ChannelMessages,
  },
  data() {
    return {
      // Auth object simplified as backend is pre-authenticated
      auth: {
        isAuthenticated: true, // Assume authenticated by default
        // Other auth-related fields removed
      },
      dialogs: {
        list: [],
        selected: null,
        isLoading: false,
        error: "",
        hasAttemptedFetch: false,
      },
      // messages: {
      //   list: [],
      //   isLoading: false,
      //   error: "",
      //   currentChannelId: null,
      // },
    };
  },
  methods: {
    // handleRequestCode and handleSubmitCode methods are removed

    async fetchDialogs() {
      // No longer need to check auth.isAuthenticated or auth.phoneNumber
      this.dialogs.isLoading = true;
      this.dialogs.error = "";
      this.dialogs.list = [];
      this.dialogs.selected = null;
      this.dialogs.hasAttemptedFetch = true;

      try {
        // phone_number parameter is removed from the request
        const response = await axios.get(`${API_BASE_URL}/dialogs`);
        this.dialogs.list = response.data;
        if (this.dialogs.list.length === 0) {
          // Handled by the v-if in the template
        }
      } catch (error) {
        console.error(
          "Error fetching dialogs:",
          error.response || error.message
        );
        let errorMessage = "An unexpected error occurred while fetching dialogs.";
        if (error.response && error.response.data && error.response.data.detail) {
          errorMessage = `Error: ${error.response.data.detail}`;
          if (error.response.status === 401) {
            errorMessage += " Please ensure the backend session is valid (run create_session.py if needed) and the backend is running.";
          }
        }
        this.dialogs.error = errorMessage;
        this.dialogs.list = [];
      } finally {
        this.dialogs.isLoading = false;
      }
    },

    selectDialog(dialog) {
      this.dialogs.selected = dialog;
      console.log("Selected dialog:", dialog);
      // TODO: Implement fetchMessagesForDialog(dialog.id) or similar
    },

    // Placeholder for fetching messages - to be implemented
    // async fetchMessagesForDialog(channelId) {
    //   if (!channelId) return;
    //   this.messages.isLoading = true;
    //   this.messages.error = "";
    //   this.messages.list = [];
    //   this.messages.currentChannelId = channelId;

    //   try {
    //     const response = await axios.get(`${API_BASE_URL}/channels/${channelId}/messages`, {
    //       params: { limit: 50 } // Example limit
    //     });
    //     this.messages.list = response.data;
    //   } catch (error) {
    //     console.error(`Error fetching messages for ${channelId}:`, error.response || error.message);
    //     let errorMessage = "Failed to fetch messages.";
    //     if (error.response && error.response.data && error.response.data.detail) {
    //       errorMessage = `Error: ${error.response.data.detail}`;
    //     }
    //     this.messages.error = errorMessage;
    //   } finally {
    //     this.messages.isLoading = false;
    //   }
    // }
  },
  mounted() {
    // Optionally, automatically fetch dialogs when the component mounts
    // if (this.auth.isAuthenticated) { // This will always be true now
    //   this.fetchDialogs();
    // }
  }
};
</script>

<style>
/* Tailwind is handling styles via classes in the template.
   Ensure your main.js imports src/style.css which should have Tailwind directives. */
</style>
