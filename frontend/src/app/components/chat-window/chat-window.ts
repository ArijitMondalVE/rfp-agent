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

  ALL_SESSIONS_STORAGE_KEY = 'rfp_all_session_ids';

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
    const allIds = this.getAllSessionIds();
    this.loadChats(allIds.length > 0 ? allIds : [this.sessionId]);
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

      this.addSessionToList(created);

      return created;
    } catch {
      return 'global';
    }
  }

  private getAllSessionIds(): string[] {
    try {
      const raw = localStorage.getItem(this.ALL_SESSIONS_STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed)) {
          return parsed.filter((s: string) => s && s.trim().length > 0);
        }
      }
      return [];
    } catch {
      return [];
    }
  }

  private addSessionToList(sessionId: string): void {
    try {
      const ids = this.getAllSessionIds();
      if (!ids.includes(sessionId)) {
        ids.push(sessionId);
        localStorage.setItem(this.ALL_SESSIONS_STORAGE_KEY, JSON.stringify(ids));
      }
    } catch {
      // ignore
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

  loadChats(sessionIds?: string[]): void {
    const allIds = sessionIds ?? this.getAllSessionIds();

    if (allIds.length === 0) {
      this.chats = [];
      return;
    }

    this.loading = true;

    this.error = null;

    this.cdr.detectChanges();

    this.api.getAllChats(allIds).subscribe({
      next: (res: any) => {
        this.chats = res?.sessions || [];

        this.loading = false;

        this.cdr.detectChanges();

        // Auto-load active chat or first chat - deferred to avoid NG0100
        if (this.chats.length > 0) {
          const currentSession = localStorage.getItem(this.SESSION_STORAGE_KEY);

          const activeChat = this.chats.find((chat) => chat.session_id === currentSession);

          if (activeChat) {
            setTimeout(() => this.selectChat(activeChat));
          }
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
        const previousSessionId = this.sessionId;
        this.sessionId = newSessionId;
        this.messages = [];

        // Persist new session
        this.safeStorageSet(this.SESSION_STORAGE_KEY, newSessionId);

        // Track all session IDs
        this.addSessionToList(newSessionId);

        // Emit active session
        this.activeChatChanged.emit(newSessionId);

        // Add new chat to the list immediately so it appears in sidebar
        this.chats = [
          {
            session_id: newSessionId,
            title: 'New Chat',
            preview: 'No messages',
          },
          ...this.chats,
        ];

        this.cdr.detectChanges();
      },
      error: (err: unknown) => {
        console.error(err);
        this.error = 'Failed to create new chat.';
        this.cdr.detectChanges();
      },
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
          this.sessionId =
            this.chats.length > 1
              ? this.chats.find((c) => c.session_id !== this.chatToDelete!.session_id)
                  ?.session_id || this.getOrCreateSessionId()
              : this.getOrCreateSessionId();
          this.safeStorageSet(this.SESSION_STORAGE_KEY, this.sessionId);
          this.activeChatChanged.emit(this.sessionId);
        }
        this.loadChats(this.getAllSessionIds());
        this.closeDeleteModal();
      },
      error: (err: unknown) => {
        console.error(err);
        this.error = 'Failed to delete chat.';
        this.closeDeleteModal();
        this.cdr.detectChanges();
      },
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
        const newSession = crypto.randomUUID();

        localStorage.setItem('rfp_session_id', newSession);
        localStorage.setItem('rfp_all_session_ids', JSON.stringify([newSession]));

        this.chats = [];
        this.messages = [];
        this.sessionId = newSession;

        this.activeChatChanged.emit(newSession);
        this.allChatsCleared.emit();

        this.closeDeleteModal();
      },
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
      },
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
