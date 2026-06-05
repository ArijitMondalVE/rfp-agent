import { ChangeDetectorRef, Component, EventEmitter, OnInit, Output } from '@angular/core';

import { CommonModule, NgFor, NgIf } from '@angular/common';

import { FormsModule } from '@angular/forms';

import { ApiService } from '../../services/api.service';

// ===================================
// CHAT SESSION MODEL
// ===================================

interface ChatSession {
  session_id: string;

  title: string;

  preview: string;

  updated_at?: string;
}

// ===================================
// CHAT MESSAGE MODEL
// ===================================

interface ChatMessage {
  role: string;

  content: string;
}

// ===================================
// COMPONENT
// ===================================

@Component({
  selector: 'app-chat-window',

  standalone: true,

  imports: [CommonModule, FormsModule, NgIf, NgFor],

  templateUrl: './chat-window.html',

  styleUrls: ['./chat-window.css'],
})
export class ChatWindow implements OnInit {
  // ===================================
  // STORAGE KEY
  // ===================================


  SESSION_STORAGE_KEY = 'rfp_session_id';

  // ===================================
  // ACTIVE SESSION
  // ===================================

  sessionId = '';

  // ===================================
  // CHAT LIST
  // ===================================

  chats: ChatSession[] = [];

  // ===================================
  // LOADED MESSAGES
  // ===================================

  messages: ChatMessage[] = [];

  // ===================================
  // UI STATES
  // ===================================

  loading = false;

  error: string | null = null;

  editingChatId: string | null = null;

  editingChatTitle: string = '';

  // Delete confirmation modal
  showDeleteConfirm = false;

  chatToDelete: ChatSession | null = null;

  clearAllMode = false;

  // ===================================
  // ACTIVE CHAT EVENT
  // ===================================

  @Output()
  activeChatChanged = new EventEmitter<string>();

  @Output()
  allChatsCleared = new EventEmitter<void>();

  // ===================================
  // CONSTRUCTOR
  // ===================================

  constructor(
    private api: ApiService,

    private cdr: ChangeDetectorRef,
  ) {}

  // ===================================
  // INIT
  // ===================================

  ngOnInit(): void {
    this.sessionId = this.getOrCreateSessionId();
    this.loadChats();
  }

  // ===================================
  // SESSION ID
  // ===================================

  private getOrCreateSessionId(): string {
    try {
      const existing = localStorage.getItem(this.SESSION_STORAGE_KEY);

      if (existing && existing.trim().length > 0) {
        return existing;
      }

      const created = crypto.randomUUID();

      localStorage.setItem(
        this.SESSION_STORAGE_KEY,

        created,
      );

      return created;
    } catch {
      return 'global';
    }
  }

  private safeStorageSet(key: string, value: string): void {
    try {
      localStorage.setItem(key, value);
    } catch {
      // SSR or restricted environment
    }
  }

  private safeStorageRemove(key: string): void {
    try {
      localStorage.removeItem(key);
    } catch {
      // SSR or restricted environment
    }
  }

  // ===================================
  // LOAD ALL CHATS
  // ===================================

  loadChats(): void {
    this.loading = true;

    this.error = null;

    this.cdr.detectChanges();

    this.api.getAllChats().subscribe({

      next: (res: any) => {
        this.chats = res?.sessions || [];

        this.loading = false;

        this.cdr.detectChanges();

        // Auto-load active chat or first chat - deferred to avoid NG0100
        if (this.chats.length > 0) {
          const activeChat =
            this.chats.find((chat) => chat.session_id === this.sessionId) || this.chats[0];

          setTimeout(() => this.selectChat(activeChat));
        }
      },

      error: (err: unknown) => {
        console.error(err);

        this.error = 'Failed to load chats.';

        this.loading = false;

        this.cdr.detectChanges();
      },
    });
  }

  // ===================================
  // CREATE NEW CHAT
  // ===================================

  createNewChat(): void {
    this.api.createNewChat().subscribe({
      next: (res: any) => {
        const newSessionId = res.session_id;
        this.sessionId = newSessionId;
        this.messages = [];

        // Persist new session
        this.safeStorageSet(this.SESSION_STORAGE_KEY, newSessionId);

        // Emit active session
        this.activeChatChanged.emit(newSessionId);

        // Reload chats list
        this.loadChats();
      },
      error: (err: unknown) => {
        console.error(err);
        this.error = 'Failed to create new chat.';
        this.cdr.detectChanges();
      }
    });
  }

  // ===================================
  // DELETE CHAT
  // ===================================

  deleteChat(chat: ChatSession, event: Event): void {
    event.stopPropagation();
    this.chatToDelete = chat;
    this.clearAllMode = false;
    this.showDeleteConfirm = true;
    this.cdr.detectChanges();
  }

  confirmDelete(): void {
    if (!this.chatToDelete) return;

    this.api.deleteChat(this.chatToDelete.session_id).subscribe({
      next: () => {
        if (this.sessionId === this.chatToDelete!.session_id) {
          this.sessionId = this.chats.length > 1
            ? this.chats.find(c => c.session_id !== this.chatToDelete!.session_id)?.session_id || 'global'
            : 'global';
          this.safeStorageSet(this.SESSION_STORAGE_KEY, this.sessionId);
          this.activeChatChanged.emit(this.sessionId);
        }
        this.loadChats();
        this.closeDeleteModal();
      },
      error: (err: unknown) => {
        console.error(err);
        this.error = 'Failed to delete chat.';
        this.closeDeleteModal();
        this.cdr.detectChanges();
      }
    });
  }

  closeDeleteModal(): void {
    this.showDeleteConfirm = false;
    this.chatToDelete = null;
    this.clearAllMode = false;
    this.cdr.detectChanges();
  }

  clearAllChats(): void {
    this.clearAllMode = true;
    this.chatToDelete = null;
    this.showDeleteConfirm = true;
    this.cdr.detectChanges();
  }

  confirmClearAll(): void {
    this.api.clearAllChats().subscribe({
      next: () => {
        this.chats = [];
        this.sessionId = '';
        this.messages = [];
        this.safeStorageRemove('rfp_chat_session_id_v1');
        this.activeChatChanged.emit(this.sessionId);
        this.allChatsCleared.emit();
        this.closeDeleteModal();
      },
      error: (err: unknown) => {
        console.error(err);
        this.error = 'Failed to clear all chats.';
        this.closeDeleteModal();
        this.cdr.detectChanges();
      }
    });
  }

  // ===================================
  // RENAME CHAT
  // ===================================

  startRenameChat(chat: ChatSession, event: Event): void {
    event.stopPropagation();
    this.editingChatId = chat.session_id;
    this.editingChatTitle = chat.title;
    this.cdr.detectChanges();

    // Focus input after view updates
    setTimeout(() => {
      const input = window.document.querySelector('.rename-input') as HTMLInputElement;
      if (input) {
        input.focus();
        input.select();
      }
    });
  }

  saveRenameChat(chat: ChatSession): void {
    const newTitle = this.editingChatTitle.trim();
    if (!newTitle || newTitle === chat.title) {
      this.editingChatId = null;
      return;
    }

    this.api.renameChat(chat.session_id, newTitle).subscribe({
      next: () => {
        chat.title = newTitle;
        this.editingChatId = null;
        this.cdr.detectChanges();
      },
      error: (err: unknown) => {
        console.error(err);
        this.error = 'Failed to rename chat.';
        this.cdr.detectChanges();
      }
    });
  }

  cancelRenameChat(): void {
    this.editingChatId = null;
    this.editingChatTitle = '';
    this.cdr.detectChanges();
  }

  onRenameBlur(chat: ChatSession, event: Event): void {
    this.saveRenameChat(chat);
  }

  onRenameKeydown(chat: ChatSession, event: KeyboardEvent): void {
    if (event.key === 'Escape') {
      this.cancelRenameChat();
    } else if (event.key === 'Enter') {
      event.preventDefault();
      this.saveRenameChat(chat);
    }
  }

  onRenameInput(chat: ChatSession, event: Event): void {
    const input = event.target as HTMLInputElement;
    this.editingChatTitle = input.value;
  }

  // ===================================
  // SELECT CHAT
  // ===================================

  selectChat(chat: ChatSession): void {
    if (!chat) return;

    this.sessionId = chat.session_id;

    // Persist active session
    this.safeStorageSet(this.SESSION_STORAGE_KEY, chat.session_id);

    // Emit active session
    this.activeChatChanged.emit(chat.session_id);

    // Load full history
    this.loadHistory();
  }

  // ===================================
  // LOAD CHAT HISTORY
  // ===================================

  loadHistory(): void {
    this.loading = true;

    this.error = null;

    this.cdr.detectChanges();

    this.api.getChatHistory(this.sessionId).subscribe({
      next: (res: any) => {
        const payload = res?.messages ?? res;

        this.messages = payload || [];

        this.loading = false;

        this.cdr.detectChanges();

        // Chat history rendering/auto-scroll is handled in `ChatComponent`.
        // Keeping this here would require querying DOM nodes that don't exist in
        // this template.

      },

      error: (err: unknown) => {
        console.error(err);

        this.error = 'Failed to load chat history.';

        this.loading = false;

        this.cdr.detectChanges();
      },
    });
  }

  // ===================================
  // CLEAR CHAT
  // ===================================

  clearChat(): void {
    this.api.clearChat(this.sessionId).subscribe({
      next: () => {
        this.messages = [];

        this.loadChats();
      },

      error: (err: unknown) => {
        console.error(err);

        this.error = 'Failed to clear chat.';
      },
    });
  }

  // ===================================
  // AUTO SCROLL
  // ===================================

  private scrollToBottom(): void {
    // NOTE:
    // This component renders the chat history sidebar.
    // The actual message list/scroll container lives in `ChatComponent`
    // (see chat.component.html where `#messagesContainer` is defined).
    //
    // Keep this as a no-op to avoid querying a DOM element that isn't
    // present in this template.
  }

}
