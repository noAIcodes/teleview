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
          class="p-3 rounded-md hover:bg-gray-100 cursor-pointer border border-gray-200"
          :class="{
            'bg-blue-100 border-blue-300':
              dialogs.selected && dialogs.selected.id === dialog.id,
          }"
        >
          <p class="font-medium text-gray-800">{{ dialog.title }}</p>
          <p class="text-sm text-gray-500">
            Type: {{ dialog.type }} | ID: {{ dialog.id }}
          </p>
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
      <h2 class="text-xl font-semibold mb-3 text-gray-700">
        Messages for: {{ dialogs.selected.title }}
      </h2>
      <p class="text-gray-500">Message display will be implemented next.</p>
      <!-- Placeholder for messages -->
    </section>
  </div>
</template>

<script>
import axios from "axios";

const API_BASE_URL = "http://localhost:8000/api";

export default {
  name: "App",
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
