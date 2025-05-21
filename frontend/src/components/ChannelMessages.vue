<template>
  <div class="channel-messages-container flex flex-col h-full">
    <!-- Message Display Area -->
    <div
      class="messages-area flex-grow overflow-y-auto p-4 space-y-2 bg-gray-100"
      ref="messagesArea"
    >
      <div
        v-for="message in messages"
        :key="message.id"
        class="message-item flex"
        :class="{
          'justify-end': message.is_outgoing,
          'justify-start': !message.is_outgoing,
        }"
      >
        <div
          class="message-bubble p-3 rounded-lg max-w-xs lg:max-w-md shadow"
          :class="{
            'bg-blue-500 text-white': message.is_outgoing,
            'bg-white text-gray-800': !message.is_outgoing,
          }"
        >
          <p class="text-sm">{{ message.text || message.caption }}</p>
          <p
            v-if="message.sender && !message.is_outgoing"
            class="text-xs text-gray-500 mt-1"
          >
            {{ message.sender }}
          </p>
          <p
            class="text-xs mt-1"
            :class="message.is_outgoing ? 'text-blue-200' : 'text-gray-400'"
          >
            {{
              new Date(message.date * 1000).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              })
            }}
          </p>
          <!-- Basic media display -->
          <div
            v-if="message.media_type === 'photo' && message.file_id"
            class="mt-2"
          >
            <img
              :src="getMediaUrl(message)"
              alt="Photo"
              class="rounded max-w-full h-auto"
              @error="onMediaError($event, message)"
            />
          </div>
          <div
            v-if="message.media_type === 'video' && message.file_id"
            class="mt-2"
          >
            <video
              :src="getMediaUrl(message)"
              controls
              class="rounded max-w-full h-auto"
              @error="onMediaError($event, message)"
            ></video>
          </div>
          <div
            v-if="
              message.media_type &&
              !['photo', 'video'].includes(message.media_type) &&
              message.file_id
            "
            class="mt-2 text-xs italic"
          >
            Media: {{ message.media_type }} ({{ message.file_name || "file" }})
            - Preview not available
          </div>
          <div
            v-if="
              message.media_type &&
              !message.file_id &&
              message.media_type !== 'poll'
            "
            class="mt-2 text-xs italic"
          >
            {{ message.media_type }} - content not available
          </div>
          <!-- Poll display -->
          <div
            v-if="message.poll_data"
            class="mt-2 p-2 border rounded bg-gray-50 text-gray-700"
          >
            <p class="font-semibold">{{ message.poll_data.question }}</p>
            <ul>
              <li
                v-for="(option, index) in message.poll_data.options"
                :key="index"
              >
                {{ option.text }}
              </li>
            </ul>
            <p class="text-xs mt-1">
              {{ message.poll_data.total_voters }} voters
              <span v-if="message.poll_data.is_closed">(Closed)</span>
            </p>
          </div>
        </div>
      </div>
      <div v-if="isLoadingMessages" class="text-center py-4">
        <p class="text-gray-500">Loading messages...</p>
      </div>
      <div v-if="loadMessagesError" class="text-center py-4 text-red-500">
        <p>{{ loadMessagesError }}</p>
      </div>
      <div
        v-if="
          !isLoadingMessages &&
          !loadMessagesError &&
          messages.length === 0 &&
          channelId
        "
        class="text-center py-4"
      >
        <p class="text-gray-500">No messages in this channel yet.</p>
      </div>
      <div v-if="!channelId" class="text-center py-4">
        <p class="text-gray-500">Select a dialog to view messages.</p>
      </div>
    </div>

    <!-- Message Input Area -->
    <div class="message-input-area p-4 bg-white border-t border-gray-200">
      <form @submit.prevent="sendMessageHandler" class="flex space-x-2">
        <input
          type="text"
          v-model="newMessageText"
          placeholder="Type your message..."
          class="flex-grow p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          :disabled="!channelId || isSending"
        />
        <button
          type="submit"
          class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md disabled:opacity-50"
          :disabled="!channelId || !newMessageText.trim() || isSending"
        >
          {{ isSending ? "Sending..." : "Send" }}
        </button>
      </form>
      <p v-if="sendError" class="text-red-500 text-sm mt-1">{{ sendError }}</p>
    </div>
  </div>
</template>

<script>
import axios from "axios";

const API_BASE_URL = "http://localhost:8000/api";

export default {
  name: "ChannelMessages",
  props: {
    channelId: {
      type: [String, Number],
      default: null,
    },
  },
  data() {
    return {
      messages: [],
      isLoadingMessages: false,
      loadMessagesError: "",
      newMessageText: "",
      isSending: false,
      sendError: "",
      pollingInterval: null,
      isScrolledToBottom: true,
    };
  },
  watch: {
    channelId: {
      immediate: true,
      async handler(newChannelId, oldChannelId) {
        this.messages = [];
        this.loadMessagesError = "";
        this.newMessageText = ""; // Clear input when channel changes
        this.sendError = "";
        if (newChannelId) {
          await this.fetchMessages();
          this.scrollToBottom();
          this.startPolling();
        } else {
          this.stopPolling();
        }
      },
    },
    messages: {
      handler() {
        // If scrolled to bottom, keep it scrolled to bottom after new messages
        if (this.isScrolledToBottom) {
          this.$nextTick(() => {
            this.scrollToBottom();
          });
        }
      },
      deep: true,
    },
  },
  methods: {
    handleScroll() {
      const messagesArea = this.$refs.messagesArea;
      if (messagesArea) {
        const threshold = 5; // Small threshold to account for fractional pixels
        this.isScrolledToBottom =
          messagesArea.scrollHeight -
            messagesArea.scrollTop -
            messagesArea.clientHeight <=
          threshold;
      }
    },
    scrollToBottom() {
      this.$nextTick(() => {
        const messagesArea = this.$refs.messagesArea;
        if (messagesArea) {
          messagesArea.scrollTop = messagesArea.scrollHeight;
        }
      });
    },
    async fetchMessages() {
      if (!this.channelId) return;
      this.isLoadingMessages = true;
      // Don't clear loadMessagesError here if we want to keep previous error visible during auto-refresh
      try {
        const response = await axios.get(
          `${API_BASE_URL}/channels/${this.channelId}/messages`,
          {
            params: { limit: 100 }, // Fetch more messages
          }
        );
        this.messages = response.data.sort((a, b) => a.date - b.date);
        this.loadMessagesError = ""; // Clear error on successful fetch
      } catch (error) {
        console.error(
          `Error fetching messages for ${this.channelId}:`,
          error.response || error.message
        );
        this.loadMessagesError =
          error.response?.data?.detail || "Failed to fetch messages.";
        // Potentially stop polling on certain errors or implement backoff
      } finally {
        this.isLoadingMessages = false;
      }
    },
    async sendMessageHandler() {
      if (!this.channelId || !this.newMessageText.trim()) return;
      this.isSending = true;
      this.sendError = "";
      try {
        await axios.post(`${API_BASE_URL}/send_message`, {
          chat_id: this.channelId,
          text: this.newMessageText,
        });
        this.newMessageText = "";
        await this.fetchMessages(); // Refresh messages immediately after sending
        this.scrollToBottom(); // Scroll to new message
      } catch (error) {
        console.error(
          "Error sending message:",
          error.response || error.message
        );
        this.sendError =
          error.response?.data?.detail || "Failed to send message.";
      } finally {
        this.isSending = false;
      }
    },
    getMediaUrl(message) {
      const fileIdentifier = message.file_id || message.media_type; // Fallback to media_type if file_id isn't specific
      return `${API_BASE_URL}/media/${this.channelId}/${message.id}/${fileIdentifier}`;
    },
    onMediaError(event, message) {
      console.warn(`Failed to load media: ${this.getMediaUrl(message)}`, event);
      event.target.alt = `Failed to load ${message.media_type}`;
      // Optionally, replace src with a placeholder image or hide the element
      // event.target.src = '/path/to/placeholder-image.png';
    },
    startPolling() {
      this.stopPolling();
      if (this.channelId) {
        this.pollingInterval = setInterval(async () => {
          await this.fetchMessages();
        }, 5000);
      }
    },
    stopPolling() {
      if (this.pollingInterval) {
        clearInterval(this.pollingInterval);
        this.pollingInterval = null;
      }
    },
  },
  mounted() {
    if (this.$refs.messagesArea) {
      this.$refs.messagesArea.addEventListener("scroll", this.handleScroll);
    }
    if (this.channelId) {
      this.scrollToBottom(); // Scroll on initial load if channel is already selected
    }
  },
  beforeUnmount() {
    this.stopPolling();
    if (this.$refs.messagesArea) {
      this.$refs.messagesArea.removeEventListener("scroll", this.handleScroll);
    }
  },
};
</script>

<style scoped>
.channel-messages-container {
  height: 75vh; /* Adjust height as needed */
}
.messages-area {
  scroll-behavior: smooth;
}
.message-bubble {
  word-break: break-word;
}
</style>
