import { Component, EventEmitter, Output } from '@angular/core';
import { ApiService } from '../../services/api.service';
import { NgIf } from '@angular/common';

@Component({
  selector: 'app-upload',
  standalone: true,
  imports: [NgIf],
  templateUrl: './upload.component.html',
})
export class UploadComponent {
  @Output() uploadComplete = new EventEmitter<any>();

  selectedFile!: File;

  uploadResponse: any;

  isUploading = false;
  successMessage: string | null = null;
  errorMessage: string | null = null;

  private currentJobId: string | null = null;

  constructor(private api: ApiService) {}

  onFileSelected(event: any) {
    this.selectedFile = event.target.files[0];
  }

  uploadFile() {
    if (!this.selectedFile) {
      this.errorMessage = 'Please select a PDF/DOC/DOCX file.';
      return;
    }

    // Fast UX: clear previous status immediately
    this.isUploading = true;
    this.successMessage = null;
    this.errorMessage = null;
    this.uploadResponse = null;
    this.currentJobId = null;

    // IMPORTANT:
    // Use sessionStorage (per browser tab/device) to avoid cross-user/session leakage.
    // Fallback to localStorage for legacy sessions.
    const sessionId =
      sessionStorage.getItem('rfp_session_id') ||
      localStorage.getItem('rfp_session_id') ||
      '';

    if (!sessionId) {
      this.errorMessage = 'No active session found. Please refresh the page.';
      this.isUploading = false;
      return;
    }

    console.log('UPLOAD SESSION:', sessionId);

    this.api.uploadRfp(this.selectedFile, sessionId).subscribe({
      next: (response) => {
        this.uploadResponse = response;
        this.currentJobId = (response as any)?.job_id ?? null;
        console.log(response);

        // Start polling for job completion
        if (this.currentJobId) {
          this.pollJobStatus(this.currentJobId);
        }

        // Emit to parent so Recent Documents can update (backend may still be processing)
        this.uploadComplete.emit(response);
      },
      error: (err) => {
        console.error(err);
        this.uploadResponse = null;
        this.currentJobId = null;
        // Backend may return { error: '...' }
        this.errorMessage = err?.error?.error || 'Upload failed. Please try again.';
        this.isUploading = false;
      },
      complete: () => {
        // Fallback: some APIs/clients may not emit a `next` value.
        if (!this.errorMessage) {
          this.successMessage = 'Upload started.';
          if (this.uploadResponse) {
            this.uploadComplete.emit(this.uploadResponse);
          }
        }
        // Do not force-isUploading false here, since processing continues in background.
      },
    });
  }

  private pollJobStatus(jobId: string) {
    const pollInterval = 3000; // 3 seconds
    const maxAttempts = 60; // 3 minutes max
    let attempts = 0;
    const sessionId =
      sessionStorage.getItem('rfp_session_id') ||
      localStorage.getItem('rfp_session_id') ||
      '';

    const checkStatus = () => {
      attempts++;
      this.api.getUploadJobStatus(jobId).subscribe({
        next: (status: any) => {
          console.log('JOB STATUS:', status);
          if (status?.status === 'completed') {
            // Job done - reload recent documents from backend
            this.isUploading = false;
            this.successMessage = 'Upload complete!';
            // Emit the session_id so parent knows to reload docs
            this.uploadComplete.emit({ session_id: sessionId, job_completed: true });
          } else if (status?.status === 'cancelled' || attempts >= maxAttempts) {
            this.isUploading = false;
            if (attempts >= maxAttempts) {
              this.errorMessage = 'Processing timed out. Check PDF History.';
            }
          } else {
            // Keep polling
            setTimeout(checkStatus, pollInterval);
          }
        },
        error: () => {
          // On error, stop polling
          this.isUploading = false;
        },
      });
    };

    setTimeout(checkStatus, pollInterval);
  }

  cancelUpload() {
    if (!this.currentJobId) {
      this.isUploading = false;
      this.successMessage = null;
      this.errorMessage = null;
      return;
    }

    // Optimistic UI: stop showing spinner immediately
    this.isUploading = false;
    this.successMessage = 'Upload cancelled.';
    this.errorMessage = null;

    this.api.cancelUpload(this.currentJobId).subscribe({
      next: () => {
        // No further action needed; backend cooperative cancel will prevent persistence.
        this.currentJobId = null;
      },
      error: (err) => {
        console.error(err);
        this.errorMessage =
          err?.error?.error || 'Could not cancel upload. It may have already completed.';
      },
    });
  }
}


