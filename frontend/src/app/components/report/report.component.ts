import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { CommonModule, NgIf, NgFor } from '@angular/common';

import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-report',
  standalone: true,
  imports: [CommonModule, NgIf, NgFor],
  templateUrl: './report.component.html',
  styleUrls: ['./report.css'],
})
export class ReportComponent {
  latestReport: any | null = null;

  // UI state
  exporting = false;
  exportError: string | null = null;
  previewCollapsed = false;

  baseUrl = 'http://127.0.0.1:8000/rfp';

  constructor(
    private api: ApiService,
    private http: HttpClient
  ) {}

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

  private exportFile(endpoint: string, filename: string) {
    this.exporting = true;
    this.exportError = null;

    return this.http.get(`${this.baseUrl}${endpoint}`, {
      responseType: 'blob',
    }).subscribe({
      next: (blob) => {
        this.downloadBlob(blob, filename);
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
    this.exportFile('/export-docx', 'rfp_report.docx');
  }

  downloadPdf() {
    this.exportFile('/export-pdf', 'rfp_report.pdf');
  }

  togglePreview(): void {
    this.previewCollapsed = !this.previewCollapsed;
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
    const text = Array.isArray(summary) ? summary.map((s: any) => typeof s === 'string' ? s : s.value ?? '').join(' ') : String(summary);
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
    // Remove hash headers
    text = text.replace(/^#+\s*/gm, '');
    // Remove backticks
    text = text.replace(/`/g, '');
    // Collapse excessive whitespace
    text = text.replace(/\n{3,}/g, '\n\n');
    return text.trim();
  }
}

