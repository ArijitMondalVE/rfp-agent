import {
  Component,
  ViewChild,
  ViewEncapsulation,
  ChangeDetectorRef,
  ChangeDetectionStrategy,
  Inject,
  PLATFORM_ID,
  ElementRef,
  OnInit,
} from '@angular/core';
import { UploadComponent } from './components/upload/upload.component';
import { ChatComponent } from './components/chat/chat.component';
import { ChatWindow } from './components/chat-window/chat-window';
import { ReportComponent } from './components/report/report.component';
import { CommonModule } from '@angular/common';
import { ApiService } from './services/api.service';
import { OnDestroy } from '@angular/core';

type RecentDoc = {
  filename: string;
  uploadedAt: number;
};

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [UploadComponent, ReportComponent, ChatComponent, ChatWindow, CommonModule],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css'],
  encapsulation: ViewEncapsulation.None,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AppComponent implements OnDestroy, OnInit {
  @ViewChild('reportComp') reportComp!: ReportComponent;
  @ViewChild('chatComp') chatComp!: ChatComponent;
  @ViewChild('reportPanel')
  reportPanel!: ElementRef<HTMLDivElement>;

  reportHeight = 300;

  isVerticalResizing = false;

  private verticalResizeStartY = 0;

  private verticalResizeStartHeight = 0;

  private verticalDragHeight = 300;

  private readonly MIN_REPORT_HEIGHT = 150;

  private readonly MAX_REPORT_HEIGHT = 700;

  startVerticalResize(event: MouseEvent | TouchEvent): void {
    // Enable resizing for both desktop and mobile.
    // Height remains clamped by MIN/MAX so the layout doesn't break.

    if (event instanceof MouseEvent) {
      event.preventDefault();
    }

    const clientY = event instanceof TouchEvent ? event.touches?.[0]?.clientY : event.clientY;

    if (clientY == null) return;

    this.isVerticalResizing = true;
    this.verticalResizeStartY = clientY;
    this.verticalResizeStartHeight = this.reportHeight;
    this.verticalDragHeight = this.reportHeight;

    document.body.style.cursor = 'row-resize';
    document.body.style.userSelect = 'none';
  }

  //Session

  onActiveChatChanged(sessionId: string) {
    console.log('CHAT WINDOW EMITTED:', sessionId);

    // Ignore "global" or empty session IDs - they corrupt the session state
    if (sessionId?.trim() && sessionId !== 'global') {
      this.activeSessionId = sessionId;
    }

    // Force change detection for OnPush
    this.cdr.detectChanges();
    this.cdr.markForCheck();
  }

  private getOrCreateSessionId(): string {
    const key = 'rfp_session_id';

    let sessionId = localStorage.getItem(key);

    if (!sessionId) {
      sessionId = crypto.randomUUID();
      localStorage.setItem(key, sessionId);
    }

    return sessionId;
  }

  private onVerticalResize = (event: MouseEvent | TouchEvent): void => {
    if (!this.isVerticalResizing) return;

    if (event instanceof TouchEvent) {
      event.preventDefault();
    }

    const clientY = event instanceof TouchEvent ? event.touches?.[0]?.clientY : event.clientY;

    if (clientY == null) return;

    const delta = clientY - this.verticalResizeStartY;

    const newHeight = Math.min(
      this.MAX_REPORT_HEIGHT,
      Math.max(this.MIN_REPORT_HEIGHT, this.verticalResizeStartHeight + delta),
    );

    this.verticalDragHeight = newHeight;

    requestAnimationFrame(() => {
      if (this.reportPanel) {
        this.reportPanel.nativeElement.style.height = `${newHeight}px`;
      }
    });
  };

  stopVerticalResize = (): void => {
    if (!this.isVerticalResizing) return;

    this.isVerticalResizing = false;
    this.reportHeight = this.verticalDragHeight;

    document.body.style.cursor = '';
    document.body.style.userSelect = '';

    this.cdr.markForCheck();
  };

  recentDocuments: RecentDoc[] = [];

  // Selected chat session id from sidebar.
  activeSessionId: string = '';

  // Trigger to reset main chat UI when all chats are cleared
  chatResetTrigger = 0;

  // Sidebar toggle
  sidebarOpen = true;

  private readonly STORAGE_KEY = 'rfp_recent_documents_v1';

  constructor(
    private cdr: ChangeDetectorRef,
    private api: ApiService,
    @Inject(PLATFORM_ID) private platformId: Object,
  ) {
    this.activeSessionId = this.getOrCreateSessionId();

    console.log('APP SESSION:', this.activeSessionId);

    this.loadRecentDocuments();
    if (typeof window !== 'undefined') {
      window.addEventListener('mousemove', this.onVerticalResize);
      window.addEventListener('mouseup', this.stopVerticalResize);

      window.addEventListener('touchmove', this.onVerticalResize, {
        passive: false,
      });

      window.addEventListener('touchend', this.stopVerticalResize);
    }
  }

  ngOnInit(): void {
    this.activeSessionId = this.getOrCreateSessionId();

    console.log('APP SESSION:', this.activeSessionId);
  }

  ngOnDestroy(): void {
    if (typeof window !== 'undefined') {
      window.removeEventListener('mousemove', this.onVerticalResize);
      window.removeEventListener('mouseup', this.stopVerticalResize);

      window.removeEventListener('touchmove', this.onVerticalResize);
      window.removeEventListener('touchend', this.stopVerticalResize);
    }
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
              uploadedAt: d.uploadedAt || d.created_at || Date.now(),
            }))
            .sort((a: RecentDoc, b: RecentDoc) => b.uploadedAt - a.uploadedAt)
            .slice(0, 10);
          this.persistRecentDocuments();
        }
      },
      error: () => {
        // ignore - keep local cache
      },
    });
  }

  private persistRecentDocuments() {
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.recentDocuments));
    } catch {
      // ignore
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

    this.activeSessionId = localStorage.getItem('rfp_session_id') || '';

    if (this.chatComp) {
      this.chatComp.resetToEmptyState();
    }
  }

  toggleSidebar() {
    this.sidebarOpen = !this.sidebarOpen;
  }
}
