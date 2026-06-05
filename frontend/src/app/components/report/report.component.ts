import { Component } from '@angular/core';
import { CommonModule, NgIf, NgFor } from '@angular/common';

import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-report',
  standalone: true,
  imports: [CommonModule, NgIf, NgFor],
  templateUrl: './report.component.html',
  styleUrls: ['./report.css', './report.resizable.css'],
})
export class ReportComponent {
  latestReport: any | null = null;

  copyStatus: 'idle' | 'copied' | 'failed' = 'idle';


  // UI state
  exporting = false;
  exportError: string | null = null;
  previewCollapsed = false;

  // Resizing state
  private previewResizableBodyEl: HTMLElement | null = null;
  private resizeStartY = 0;
  private resizeStartH = 0;

  constructor(
    private api: ApiService
  ) {}

  ngAfterViewInit() {
    // Used by drag-to-resize handle
    this.previewResizableBodyEl = document.querySelector('.preview-resizable-body');
  }

  onResizeStart(ev: MouseEvent | TouchEvent) {
    if (!this.previewResizableBodyEl) return;

    const el = this.previewResizableBodyEl;

    this.resizeStartH = el.getBoundingClientRect().height;

    const clientY = (ev instanceof TouchEvent)
      ? ev.touches?.[0]?.clientY
      : (ev as MouseEvent).clientY;

    if (clientY == null) return;

    this.resizeStartY = clientY;

    // Stop selection + keep drag responsive
    ev.preventDefault();

    const onMove = (e: MouseEvent | TouchEvent) => {
      const clientY2 = (e instanceof TouchEvent)
        ? e.touches?.[0]?.clientY
        : (e as MouseEvent).clientY;

      if (clientY2 == null) return;

      const delta = clientY2 - this.resizeStartY;

      // Clamp height so it remains usable.
      const next = Math.max(220, this.resizeStartH + delta);
      el.style.maxHeight = `${next}px`;
    };

    const onUp = () => {
      window.removeEventListener('mousemove', onMove as any);
      window.removeEventListener('mouseup', onUp as any);
      window.removeEventListener('touchmove', onMove as any);
      window.removeEventListener('touchend', onUp as any);
      document.body.style.userSelect = '';
    };

    // Prevent text selection during drag
    document.body.style.userSelect = 'none';

    window.addEventListener('mousemove', onMove as any);
    window.addEventListener('mouseup', onUp as any);
    window.addEventListener('touchmove', onMove as any, { passive: false } as any);
    window.addEventListener('touchend', onUp as any);
  }

  /**
   * The backend currently only keeps `latest_report` in memory.
   * There is no endpoint in the backend to fetch the JSON report.
   * We still render a formatted view once the report JSON is set here
   * (optional in future), and we enable exports directly.
   */
  setReportFromUploadResponse(payload: any) {
    this.latestReport = payload?.report ?? payload ?? null;
  }

  private downloadBlob(blob: Blob, filename: string) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  }

  private getSessionId(): string {
    return localStorage.getItem('rfp_session_id') || '';
  }

  private exportFile(format: 'docx' | 'pdf') {
    this.exporting = true;
    this.exportError = null;

    const sessionId = this.getSessionId();
    if (!sessionId) {
      this.exportError = 'No active session. Upload an RFP first.';
      this.exporting = false;
      return;
    }

    const apiCall = format === 'docx'
      ? this.api.exportDocx(sessionId)
      : this.api.exportPdf(sessionId);

    apiCall.subscribe({
      next: (blob) => {
        this.downloadBlob(blob, `rfp_report.${format}`);
        this.exporting = false;
      },
      error: (err) => {
        console.error(err);
        this.exportError = 'Export failed. Upload an RFP first.';
        this.exporting = false;
      }
    });
  }

  downloadDocx() {
    this.exportFile('docx');
  }

  downloadPdf() {
    this.exportFile('pdf');
  }

  togglePreview(): void {
    this.previewCollapsed = !this.previewCollapsed;
  }

  private buildReportText(): string {
    if (!this.latestReport) return '';

    const parts: string[] = [];

    const execSummary = this.getSummaryText();
    if (execSummary) {
      parts.push('Executive Summary');
      parts.push(execSummary);
      parts.push('');
    }

    const appendList = (title: string, items: any[] | undefined) => {
      if (!items?.length) return;
      parts.push(title);
      for (const it of items) {
        const line = this.formatItem(it);
        if (line) parts.push(`- ${line}`);
      }
      parts.push('');
    };

    appendList('Scope of Work', this.latestReport?.scope_of_work);
    appendList('Deliverables', this.latestReport?.deliverables);
    appendList('Objectives', this.latestReport?.objectives);
    appendList('Deadlines', this.latestReport?.deadlines);
    appendList('Staffing Requirements', this.latestReport?.staffing_requirements);
    appendList('Compliance Items', this.latestReport?.compliance_items);

    return this.cleanText(parts.join('\n'));
  }

  async copyReportText() {
    if (!this.latestReport) return;

    const text = this.buildReportText();
    if (!text) return;

    this.copyStatus = 'idle';

    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        // Fallback for older browsers
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.left = '-9999px';
        ta.style.top = '0';
        document.body.appendChild(ta);
        ta.focus();
        ta.select();
        const ok = document.execCommand('copy');
        document.body.removeChild(ta);
        if (!ok) throw new Error('Copy failed');
      }

      this.copyStatus = 'copied';
      window.setTimeout(() => {
        if (this.copyStatus === 'copied') this.copyStatus = 'idle';
      }, 1200);
    } catch (e) {
      console.error(e);
      this.copyStatus = 'failed';
      window.setTimeout(() => {
        if (this.copyStatus === 'failed') this.copyStatus = 'idle';
      }, 1500);
    }
  }


  formatItem(item: any): string {
    if (item == null) return '';
    if (typeof item === 'string') return this.cleanText(item);
    if (typeof item === 'number') return String(item);
    if (typeof item === 'object') return this.cleanText(item.value ?? item.text ?? item.content ?? String(item));
    return this.cleanText(String(item));
  }

  getSummaryText(): string {
    const summary = this.latestReport?.summary;
    if (!summary) return '';
    const text = Array.isArray(summary)
      ? summary.map((s: any) => typeof s === 'string' ? s : s.value ?? '').join(' ')
      : String(summary);
    return this.cleanText(text);
  }

  private cleanText(text: string): string {
    if (!text) return '';
    // Remove markdown code blocks
    text = text.replace(/```(?:json)?\s*/gi, '');
    text = text.replace(/```\s*$/gi, '');

    // Remove bold/italic markers
    text = text.replace(/\*\*/g, '');
    text = text.replace(/\*/g, '');

    // Remove backticks
    text = text.replace(/`/g, '');

    // Collapse excessive whitespace
    text = text.replace(/\n{3,}/g, '\n\n');

    return text.trim();
  }
}

