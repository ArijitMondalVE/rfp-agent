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
        console.log(response);
        // Emit to parent so Recent Documents can update
        this.uploadComplete.emit(response);
      },
      error: (err) => {
        console.error(err);
        this.uploadResponse = null;
        // Backend may return { error: '...' }
        this.errorMessage = err?.error?.error || 'Upload failed. Please try again.';
        this.isUploading = false;
      },
      complete: () => {
        // Fallback: some APIs/clients may not emit a `next` value.
        // If we didn't hit `error`, treat completion as success.
        if (!this.errorMessage) {
          this.successMessage = 'Upload successful.';
          // If server response wasn't emitted via `next`, attempt to emit `uploadResponse` if present.
          if (this.uploadResponse) {
            this.uploadComplete.emit(this.uploadResponse);
          }
        }
        this.isUploading = false;
      },
    });
  }
}

