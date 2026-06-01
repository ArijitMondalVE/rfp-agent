import { Component, ViewChild, ViewEncapsulation, ChangeDetectorRef } from '@angular/core';
import { UploadComponent } from './components/upload/upload.component';
import { ChatComponent } from './components/chat/chat.component';
import { ChatWindow } from './components/chat-window/chat-window';
import { ReportComponent } from './components/report/report.component';
import { CommonModule } from '@angular/common';
import { ApiService } from './services/api.service';

type RecentDoc = {
  filename: string;
  uploadedAt: number;
};

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    UploadComponent,
    ReportComponent,
    ChatComponent,
    ChatWindow,
    CommonModule
  ],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css'],
  encapsulation: ViewEncapsulation.None
})
export class AppComponent {
  @ViewChild('reportComp') reportComp!: ReportComponent;
  @ViewChild('chatComp') chatComp!: ChatComponent;

  recentDocuments: RecentDoc[] = [];

  // Selected chat session id from sidebar.
  activeSessionId: string = 'global';

  // Trigger to reset main chat UI when all chats are cleared
  chatResetTrigger = 0;

  // Sidebar resize
  sidebarWidth = 320;
  isResizing = false;
  private readonly MIN_SIDEBAR_WIDTH = 200;
  private readonly MAX_SIDEBAR_WIDTH = 500;
  private readonly STORAGE_KEY_SIDEBAR = 'rfp_sidebar_width_v1';

  private readonly STORAGE_KEY = 'rfp_recent_documents_v1';


  constructor(
    private cdr: ChangeDetectorRef,
    private api: ApiService
  ) {
    this.loadRecentDocuments();
    this.loadSidebarWidth();
    this.setupResizeListeners();
  }

  private loadRecentDocuments() {
    // First load from localStorage cache
    try {
      const raw = localStorage.getItem(this.STORAGE_KEY);
      if (!raw) return;

      const parsed = JSON.parse(raw) as RecentDoc[];
      if (!Array.isArray(parsed)) return;

      this.recentDocuments = parsed
        .filter((d) => d && typeof d.filename === 'string' && typeof d.uploadedAt === 'number')
        .sort((a, b) => b.uploadedAt - a.uploadedAt)
        .slice(0, 10);
    } catch {
      // ignore
    }

    // Then fetch from backend to get actual persisted documents
    this.api.getUploadedDocuments().subscribe({
      next: (res: any) => {
        const docs = res?.documents || res || [];
        if (Array.isArray(docs) && docs.length > 0) {
          this.recentDocuments = docs
            .map((d: any) => ({
              filename: d.filename || d.name || String(d),
              uploadedAt: d.uploadedAt || d.created_at || Date.now()
            }))
            .sort((a: RecentDoc, b: RecentDoc) => b.uploadedAt - a.uploadedAt)
            .slice(0, 10);
          this.persistRecentDocuments();
        }
      },
      error: () => {
        // ignore - keep local cache
      }
    });
  }

  private persistRecentDocuments() {
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.recentDocuments));
    } catch {
      // ignore
    }
  }

  private loadSidebarWidth() {
    try {
      const saved = localStorage.getItem(this.STORAGE_KEY_SIDEBAR);
      if (saved) {
        const width = parseInt(saved, 10);
        if (width >= this.MIN_SIDEBAR_WIDTH && width <= this.MAX_SIDEBAR_WIDTH) {
          this.sidebarWidth = width;
        }
      }
    } catch {
      // ignore
    }
  }

  private saveSidebarWidth() {
    try {
      localStorage.setItem(this.STORAGE_KEY_SIDEBAR, String(this.sidebarWidth));
    } catch {
      // ignore
    }
  }

  private resizeStartX = 0;
  private resizeStartWidth = 0;
  private dragWidth = 0;

  startResize(event: MouseEvent) {
    event.preventDefault();
    this.isResizing = true;
    this.resizeStartX = event.clientX;
    this.resizeStartWidth = this.sidebarWidth;
    this.dragWidth = this.sidebarWidth;
  }

  private setupResizeListeners() {
    if (typeof window !== 'undefined') {
      window.addEventListener('mousemove', this.onResize.bind(this));
      window.addEventListener('mouseup', this.stopResize.bind(this));
    }
  }

  private onResize(event: MouseEvent) {
    if (!this.isResizing) return;

    const delta = event.clientX - this.resizeStartX;
    const newWidth = this.resizeStartWidth + delta;

    if (newWidth >= this.MIN_SIDEBAR_WIDTH && newWidth <= this.MAX_SIDEBAR_WIDTH) {
      this.dragWidth = newWidth;
      // Only update CSS variable - no Angular change detection during drag
      window.document.documentElement.style.setProperty('--sidebar-width', `${newWidth}px`);
    }
  }

  stopResize() {
    if (this.isResizing) {
      this.isResizing = false;
      // Sync to Angular state only at the end
      this.sidebarWidth = this.dragWidth;
      this.saveSidebarWidth();
    }
  }

  onDocumentUploaded(result: any) {
    const filename = result?.filename;
    if (!filename || typeof filename !== 'string') return;

    const now = Date.now();
    const existingIndex = this.recentDocuments.findIndex((d) => d.filename === filename);

    if (existingIndex >= 0) {
      this.recentDocuments = [
        ...this.recentDocuments.slice(0, existingIndex),
        { filename, uploadedAt: now },
        ...this.recentDocuments.slice(existingIndex + 1),
      ].sort((a, b) => b.uploadedAt - a.uploadedAt);
    } else {
      this.recentDocuments = [{ filename, uploadedAt: now }, ...this.recentDocuments]
        .sort((a, b) => b.uploadedAt - a.uploadedAt)
        .slice(0, 10);
    }

    this.persistRecentDocuments();

    // Forward report data to the report component
    if (this.reportComp && result?.report) {
      this.reportComp.setReportFromUploadResponse(result);
    }
  }

  formatUploadedAt(ts: number): string {
    if (!ts) return 'Uploaded recently';
    const date = new Date(ts);
    return `Uploaded ${date.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: '2-digit' })}`;
  }

  onAllChatsCleared() {
    this.chatResetTrigger++;
    this.activeSessionId = 'global';
    if (this.chatComp) {
      this.chatComp.resetToEmptyState();
    }
  }
}



