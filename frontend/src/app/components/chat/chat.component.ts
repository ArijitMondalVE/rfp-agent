import {
  Component,
  ChangeDetectorRef,
  ElementRef,
  Input,
  SimpleChanges,
  ViewChild,
} from '@angular/core';

import { FormsModule } from '@angular/forms';

import { NgFor, NgIf, NgClass } from '@angular/common';

import { marked } from 'marked';

import * as DOMPurifyImport from 'dompurify';

import { ApiService } from '../../services/api.service';

interface ChatMessage {
  role: string;

  content: string;
}

// -----------------------------------
// MARKDOWN CONFIG
// -----------------------------------
marked.setOptions({
  breaks: true,

  gfm: true,
});

@Component({
  selector: 'app-chat',

  standalone: true,

  imports: [FormsModule, NgFor, NgIf, NgClass],

  templateUrl: './chat.component.html',

  styleUrls: ['./chat.component.css'],
})
export class ChatComponent {
  private scheduleUiUpdate(fn: () => void): void {
    if (typeof window !== 'undefined' && typeof window.requestAnimationFrame === 'function') {
      window.requestAnimationFrame(() => fn());
      return;
    }

    // SSR / non-browser fallback
    setTimeout(() => fn(), 0);
  }

  // -----------------------------------
  // Input: active chat session
  // -----------------------------------
  @Input() sessionId: string = '';

  ngOnChanges(changes: SimpleChanges): void {
    console.log('SESSION RECEIVED:', this.sessionId);

    if (changes['sessionId'] && this.sessionId) {
      this.loadHistoryForSession();
    }
  }

  private loadHistoryForSession(): void {
    // Load existing chat history for the active session.
    // Note: streaming new messages will append to `this.messages`.
    this.api.getChatHistory(this.sessionId).subscribe({
      next: (res: any) => {
        const payload = res?.messages ?? res;
        this.messages = Array.isArray(payload) ? payload : [];
        this.cdr.detectChanges();
        this.scheduleUiUpdate(() => {
          const container = this.messagesContainer?.nativeElement;
          if (container) container.scrollTop = container.scrollHeight;
        });
      },
      error: () => {
        this.messages = [];
        this.cdr.detectChanges();
      },
    });
  }

  // -----------------------------------
  // User Input
  // -----------------------------------
  question = '';

  // -----------------------------------
  // Loading State
  // -----------------------------------
  loading = false;

  // Shared with ChatWindow via localStorage.
  // (sessionId is now driven by @Input())

  ngAfterViewInit(): void {
    // Ensure initial render uses selected session.
    this.loadHistoryForSession();
  }

  // -----------------------------------
  // Chat Messages
  // -----------------------------------
  messages: ChatMessage[] = [];

  // -----------------------------------
  // Messages Container
  // -----------------------------------
  @ViewChild('messagesContainer')
  messagesContainer?: ElementRef<HTMLDivElement>;

  constructor(
    private api: ApiService,

    private cdr: ChangeDetectorRef,
  ) {}

  // -----------------------------------
  // ASK QUESTION
  // -----------------------------------
  async askQuestion() {
    console.log('ASK SESSION:', this.sessionId);
    // Prevent empty input
    if (!this.question.trim()) return;

    // Prevent duplicate requests
    if (this.loading) return;

    // -----------------------------------
    // Store question
    // -----------------------------------
    const currentQuestion = this.question;

    // -----------------------------------
    // Add user message
    // -----------------------------------
    const userMessage: ChatMessage = {
      role: 'user',

      content: currentQuestion,
    };

    this.messages.push(userMessage);

    // -----------------------------------
    // Clear input
    // -----------------------------------
    this.question = '';

    // -----------------------------------
    // Enable loading
    // -----------------------------------
    this.loading = true;

    // -----------------------------------
    // Create AI placeholder
    // -----------------------------------
    const aiMessage: ChatMessage = {
      role: 'assistant',

      content: '',
    };

    this.messages.push(aiMessage);

    try {
      // -----------------------------------
      // Call Streaming API
      // -----------------------------------
      console.log('STREAM SESSION:', this.sessionId);
      const currentSessionId = this.sessionId || localStorage.getItem('rfp_session_id') || '';

      if (!currentSessionId) {
        aiMessage.content = 'No active session found.';
        return;
      }

      const response = await this.api.streamChat(currentSessionId, currentQuestion);

      // -----------------------------------
      // Validate Response
      // -----------------------------------
      if (!response.ok || !response.body) {
        aiMessage.content = `Request failed: ${response.status}`;

        this.loading = false;

        this.cdr.detectChanges();

        return;
      }

      // -----------------------------------
      // Stream Reader
      // -----------------------------------
      const reader = response.body.getReader();

      const decoder = new TextDecoder();

      let buffer = '';

      // -----------------------------------
      // STREAM LOOP
      // -----------------------------------
      while (true) {
        const { done, value } = await reader.read();

        // Stream finished
        if (done) break;

        // -----------------------------------
        // Decode chunk
        // -----------------------------------
        buffer += decoder.decode(
          value,

          { stream: true },
        );

        // -----------------------------------
        // SSE events separated by \n\n
        // -----------------------------------
        const parts = buffer.split('\n\n');

        // Keep incomplete tail
        buffer = parts.pop() || '';

        // -----------------------------------
        // Process SSE events
        // -----------------------------------
        for (const part of parts) {
          const lines = part.split('\n');

          for (const line of lines) {
            const trimmed = line.trim();

            // Ignore non-data lines
            if (!trimmed.startsWith('data:')) {
              continue;
            }

            // Extract content
            const data = trimmed.replace(/^data:\s?/, '');

            // Ignore DONE event
            if (data.trim() === '[DONE]') {
              continue;
            }

            // -----------------------------------
            // Append streamed token
            // -----------------------------------
            aiMessage.content += data;

            // -----------------------------------
            // Refresh Angular UI
            // -----------------------------------
            this.cdr.detectChanges();

            // -----------------------------------
            // Auto-scroll
            // -----------------------------------
            requestAnimationFrame(() => {
              const container = this.messagesContainer?.nativeElement;

              if (container) {
                container.scrollTop = container.scrollHeight;
              }
            });
          }
        }
      }
    } catch (error) {
      console.error(error);

      aiMessage.content = 'Unable to generate AI response. Please try again.';
    } finally {
      // -----------------------------------
      // Disable loading
      // -----------------------------------
      this.loading = false;

      // -----------------------------------
      // Refresh UI
      // -----------------------------------
      this.cdr.detectChanges();
    }
  }

  // -----------------------------------
  // FORMAT MARKDOWN SAFELY
  // -----------------------------------
  formatMessage(content: string): string {
    // Parse markdown - marked handles most cases correctly
    const rawHtml = marked.parse(content) as string;

    // Sanitize HTML
    const domPurify = (DOMPurifyImport as any)?.default ?? DOMPurifyImport;

    const sanitizeFn = domPurify?.sanitize?.bind(domPurify);

    return typeof sanitizeFn === 'function' ? sanitizeFn(rawHtml) : rawHtml;
  }

  resetToEmptyState(): void {
    this.messages = [];
    this.question = '';
    this.loading = false;
    this.cdr.detectChanges();
  }
}
