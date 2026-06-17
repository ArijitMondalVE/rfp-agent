import {
  Component,
  ViewChild,
  ViewEncapsulation,
  ChangeDetectorRef,
  ChangeDetectionStrategy,
  Inject,
  PLATFORM_ID,
  OnInit,
} from '@angular/core';
import { UploadComponent } from './components/upload/upload.component';
import { ChatComponent } from './components/chat/chat.component';
import { ChatWindow } from './components/chat-window/chat-window';
import { ReportComponent } from './components/report/report.component';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { ApiService } from './services/api.service';
import { OnDestroy } from '@angular/core';
import { PdfDeleteModalComponent } from './components/pdf-delete-modal/pdf-delete-modal.component';
import { ConfirmDeleteModalComponent } from './components/confirm-delete-modal/confirm-delete-modal.component';

type RecentDoc = {
  id?: number;
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
    CommonModule,
    // PDF delete confirmation modal
    PdfDeleteModalComponent,
    // Reusable confirm modal
    ConfirmDeleteModalComponent,
  ],

  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css'],
  encapsulation: ViewEncapsulation.None,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AppComponent implements OnDestroy, OnInit {
  private isMobileCached: boolean | null = null;

  get isMobile(): boolean {
    if (this.isMobileCached !== null) return this.isMobileCached;
    if (!isPlatformBrowser(this.platformId)) {
      this.isMobileCached = false;
      return false;
    }
    this.isMobileCached = window.innerWidth <= 768;
    return this.isMobileCached;
  }
  // PDF delete confirmation modal state (must match chat history modal style)
  showPdfDeleteConfirm = false;
  pdfToDelete: string | null = null;

  // Generic confirm modal state
  showConfirmDeleteConfirm = false;
  confirmDeleteTargetLabel: string | null = null;

  @ViewChild('reportComp') reportComp!: ReportComponent;
  @ViewChild('chatComp') chatComp!: ChatComponent;
  @ViewChild('chatWindow') chatWindow!: ChatWindow;

  reportSidebarWidth = 420;

  reportSidebarCollapsed = false;

  private resizingReport = false;
  isReportResizing = false;

  private startX = 0;

  private startWidth = 420;

  reportSidebarOpen = false;

  toggleReportSidebar() {
    const isMobile = window.innerWidth <= 768;

    if (isMobile) {
      // Mobile: toggle between open (visible with transform) and closed (hidden)
      if (this.reportSidebarOpen) {
        this.reportSidebarOpen = false;
      } else {
        this.reportSidebarOpen = true;
        this.reportSidebarCollapsed = false;
      }
      return;
    }

    // Desktop/tablet: use collapsed state for smooth width animation
    const wasCollapsed = this.reportSidebarCollapsed;
    this.reportSidebarCollapsed = !wasCollapsed;

    if (!wasCollapsed) {
      // Was expanded, now collapsing
      this.reportSidebarOpen = false;
    } else {
      // Was collapsed, now expanding
      this.reportSidebarOpen = true;
    }
  }

  toggleReportCollapsedFromButton() {
    const isMobile = window.innerWidth <= 768;
    if (isMobile) {
      // Mobile: close the sidebar via transform
      this.reportSidebarOpen = false;
      return;
    }

    // Desktop: same as toggleReportSidebar
    this.toggleReportSidebar();
  }

  openReportSidebar() {
    this.reportSidebarOpen = true;
    this.reportSidebarCollapsed = false;
    this.cdr.markForCheck();
  }
  startReportResize(event: MouseEvent) {
    this.isReportResizing = true;
    event.preventDefault();
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
    const startX = event.clientX;

    const startWidth = this.reportSidebarWidth;

    let animationFrame: number | null = null;

    const onMouseMove = (e: MouseEvent) => {
      if (animationFrame) {
        cancelAnimationFrame(animationFrame);
      }

      document.body.style.cursor = '';
      document.body.style.userSelect = '';

      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);

      animationFrame = requestAnimationFrame(() => {
        const delta = startX - e.clientX;

        this.reportSidebarWidth = Math.max(320, Math.min(startWidth + delta, 900));
        this.cdr.markForCheck();
      });
    };

    const onMouseUp = () => {
      this.isReportResizing = false;

      this.cdr.markForCheck();

      if (animationFrame) {
        cancelAnimationFrame(animationFrame);
      }

      document.removeEventListener('mousemove', onMouseMove);

      document.removeEventListener('mouseup', onMouseUp);
    };

    document.addEventListener('mousemove', onMouseMove);

    document.addEventListener('mouseup', onMouseUp);
  }

  closeReportSidebar() {
    this.reportSidebarOpen = false;
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

  getOrCreateSessionId(): string {
    // Use sessionStorage so it resets when the user refreshes the page.
    // This prevents "cross-user"/"cross-refresh" leakage of document/session history.
    const key = 'rfp_session_id';

    let sessionId = sessionStorage.getItem(key);

    if (!sessionId) {
      sessionId = crypto.randomUUID();
      sessionStorage.setItem(key, sessionId);
    }

    return sessionId;
  }


  recentDocuments: RecentDoc[] = [];

  // Selected chat session id from sidebar.
  activeSessionId: string = '';

  // Trigger to reset main chat UI when all chats are cleared
  chatResetTrigger = 0;

  // Sidebar toggle
  sidebarOpen = true;

  // Upload section collapsible (sandwich bar toggle)
  uploadSectionOpen = true;

  private readonly STORAGE_KEY = 'rfp_recent_documents_v1';
  private readonly LAST_OPENED_DOC_ID_KEY = 'rfp_last_opened_document_id_v1';

  constructor(
    private cdr: ChangeDetectorRef,
    private api: ApiService,
    @Inject(PLATFORM_ID) private platformId: Object,
  ) {
    this.activeSessionId = this.getOrCreateSessionId();

    console.log('APP SESSION:', this.activeSessionId);
    this.loadRecentDocuments();
  }

  ngOnInit(): void {
    this.activeSessionId = this.getOrCreateSessionId();

    console.log('APP SESSION:', this.activeSessionId);

    // Mobile: show report sidebar by default (<= 768px)
    if (isPlatformBrowser(this.platformId)) {
      const isMobile = window.innerWidth <= 768;
      if (isMobile) {
        this.reportSidebarOpen = true;
        this.reportSidebarCollapsed = false;
        this.cdr.markForCheck();
      }

      // Restore last opened document/report/chat on refresh
      this.restoreLastOpenedDocument();
    }
  }

  private restoreLastOpenedDocument(): void {
    const raw = localStorage.getItem(this.LAST_OPENED_DOC_ID_KEY);
    const lastDocId = raw ? Number(raw) : NaN;

    if (!lastDocId || Number.isNaN(lastDocId) || lastDocId <= 0) return;

    this.api.getDocument(lastDocId).subscribe({
      next: (response: any) => {
        if (response?.session_id) {
          // Keep session isolated per refresh using sessionStorage.
          sessionStorage.setItem('rfp_session_id', response.session_id);
          this.activeSessionId = response.session_id;
        }


        if (this.reportComp) {
          this.reportComp.setReportFromUploadResponse({
            report: response.report,
            structured_data: response.report?.structured_data,
            compliance_matrix: response.report?.compliance_matrix,
            classification: response.report?.classification,
            proposal_strategy: response.report?.proposal_strategy,
          });
        }

        if (this.chatWindow) {
          this.chatWindow.loadChats();
        }

        this.cdr.detectChanges();
      },
      error: () => {
        // If doc is gone, ignore and keep user at default state
      },
    });
  }


  ngOnDestroy(): void {}

  private loadRecentDocuments(sessionIdOverride?: string) {
    // Try backend first (source of truth)
    const sessionId = sessionIdOverride || this.getOrCreateSessionId();

    this.api.getUploadedDocuments(sessionId).subscribe({

      next: (res: any) => {
        const docs = res?.documents || res || [];

        if (Array.isArray(docs)) {
          this.recentDocuments = docs
            .map((d: any) => ({
              id: d.id,

              filename: d.filename || d.name || String(d),

              uploadedAt: d.created_at ? new Date(d.created_at).getTime() : Date.now(),
            }))
            .sort((a: RecentDoc, b: RecentDoc) => b.uploadedAt - a.uploadedAt)
            .slice(0, 10);

          this.persistRecentDocuments();
        }
      },

      error: () => {
        // Fallback to cache

        try {
          const raw = localStorage.getItem(this.STORAGE_KEY);

          if (!raw) return;

          const parsed = JSON.parse(raw);

          if (!Array.isArray(parsed)) {
            return;
          }

          this.recentDocuments = parsed.filter((d: any) => d.id);
        } catch {}
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
    // If job completed, reload documents and show latest report
    if (result?.job_completed) {
      const backendSessionId = result?.session_id;
      if (backendSessionId && typeof backendSessionId === 'string') {
        sessionStorage.setItem('rfp_session_id', backendSessionId);
        localStorage.setItem('rfp_session_id', backendSessionId);
        this.activeSessionId = backendSessionId;
      }
      // Load recent documents, then get latest report
      this.loadRecentDocuments(backendSessionId);

      // Load the most recent document's report
      this.api.getUploadedDocuments(backendSessionId).subscribe({
        next: (res: any) => {
          const docs = res?.documents || res || [];
          if (docs && docs.length > 0) {
            const latestDoc = docs[0];
            if (latestDoc?.id) {
              this.openDocument({ id: latestDoc.id, filename: latestDoc.filename, uploadedAt: Date.now() });
            }
          }
        }
      });
      return;
    }


    const filename = result?.filename;
    if (!filename || typeof filename !== 'string') return;

    const now = Date.now();
    const existingIndex = this.recentDocuments.findIndex((d) => d.filename === filename);

    if (existingIndex >= 0) {
      this.recentDocuments = [
        ...this.recentDocuments.slice(0, existingIndex),
        { id: result?.document_id, filename, uploadedAt: now },
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

  openDocument(doc: RecentDoc) {
    if (!doc.id) {
      console.error('Document id missing');
      return;
    }

    // Persist last opened document so refresh restores report/chat
    try {
      localStorage.setItem(this.LAST_OPENED_DOC_ID_KEY, String(doc.id));
    } catch {}

    this.api.getDocument(doc.id).subscribe({
      next: (response: any) => {
        console.log('DOCUMENT LOADED:', response);

        localStorage.setItem('rfp_session_id', response.session_id);

        this.activeSessionId = response.session_id;

        if (this.reportComp) {
          this.reportComp.setReportFromUploadResponse({
            report: response.report,

            structured_data: response.report?.structured_data,

            compliance_matrix: response.report?.compliance_matrix,

            classification: response.report?.classification,

            proposal_strategy: response.report?.proposal_strategy,
          });
        }

        if (this.chatWindow) {
          this.chatWindow.loadChats();
        }

        this.cdr.detectChanges();
      },

      error: (err) => {
        console.error(err);
      },
    });
  }

  deleteRecentDocument(doc: RecentDoc, event: Event) {
    event.stopPropagation();

    if (!doc.filename) return;

    // Keep PDF delete confirmation consistent with chat history (custom modal)
    this.pdfToDelete = doc.filename;
    this.showPdfDeleteConfirm = true;
    this.cdr.detectChanges();
    // Actual delete happens in confirmPdfDelete()
    return;
  }

  openConfirmDeleteModal(targetLabel: string): void {
    this.confirmDeleteTargetLabel = targetLabel;
    this.showConfirmDeleteConfirm = true;
    this.cdr.detectChanges();
  }

  confirmPdfDelete() {
    if (!this.pdfToDelete) return;

    const filename = this.pdfToDelete;

    // optimistic UI update
    this.recentDocuments = this.recentDocuments.filter((d) => d.filename !== filename);
    this.persistRecentDocuments();

    this.api.deleteUploadedDocument(filename).subscribe({
      next: () => {
        this.cdr.detectChanges();
      },
      error: (err: unknown) => {
        console.error(err);
        // revert local change by reloading from backend cache
        this.loadRecentDocuments();
        this.cdr.detectChanges();
      },
    });

    this.closePdfDeleteModal();
  }

  closePdfDeleteModal() {
    this.showPdfDeleteConfirm = false;
    this.pdfToDelete = null;
    this.cdr.detectChanges();
  }

  confirmClearPdfHistory(): void {
    this.clearRecentDocumentsInner();
    this.closeConfirmDeleteModal();
  }

  private clearRecentDocumentsInner(): void {
    // optimistic
    this.recentDocuments = [];
    this.persistRecentDocuments();
    this.cdr.detectChanges();

    const sessionId = this.getOrCreateSessionId();
    this.api.clearUploadedDocuments(sessionId).subscribe({
      next: () => {
        this.cdr.detectChanges();
      },
      error: (err: unknown) => {
        console.error(err);
        this.loadRecentDocuments();
        this.cdr.detectChanges();
      },
    });
  }

  closeConfirmDeleteModal(): void {
    this.showConfirmDeleteConfirm = false;
    this.confirmDeleteTargetLabel = null;
    this.cdr.detectChanges();
  }

  clearRecentDocuments(event: Event) {
    event.stopPropagation();
    if (this.recentDocuments.length === 0) return;

    // Use modern confirm modal (instead of window.confirm)
    this.confirmDeleteTargetLabel = null;
    this.showConfirmDeleteConfirm = true;
    this.cdr.detectChanges();
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

  onMessageStreamComplete() {
    if (this.chatWindow) {
      this.chatWindow.loadChats();
    }
  }

  toggleSidebar() {
    this.sidebarOpen = !this.sidebarOpen;
  }
}
