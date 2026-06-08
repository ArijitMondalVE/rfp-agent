import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';

@Component({
  selector: 'app-pdf-delete-modal',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="modal-backdrop" (click)="onBackdropClick()">
      <div class="modal-card" (click)="$event.stopPropagation()">
        <div class="modal-icon">
          <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"></path>
          </svg>
        </div>

        <h2 class="modal-title">Delete PDF?</h2>
        <p class="modal-desc">
          This will permanently delete "{{ filename }}" from PDF history. This action cannot be undone.
        </p>

        <div class="modal-actions">
          <button class="modal-btn modal-btn-cancel" (click)="close.emit()">Cancel</button>
          <button
            class="modal-btn modal-btn-delete"
            (click)="confirm.emit()"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [
    `
    .modal-backdrop {
      position: fixed;
      inset: 0;
      z-index: 9999;
      background: rgba(0, 0, 0, 0.6);
      backdrop-filter: blur(6px);
      -webkit-backdrop-filter: blur(6px);
      display: flex;
      align-items: center;
      justify-content: center;
      animation: backdropFadeIn 0.2s ease;
    }

    @keyframes backdropFadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }

    .modal-card {
      background: linear-gradient(
        160deg,
        rgba(30, 41, 59, 0.98) 0%,
        rgba(15, 23, 42, 0.98) 100%
      );
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 20px;
      padding: 2rem 2.25rem;
      width: 340px;
      max-width: 90vw;
      box-shadow:
        0 24px 48px rgba(0, 0, 0, 0.4),
        0 0 0 1px rgba(255, 255, 255, 0.05) inset;
      animation: modalSlideIn 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
      text-align: center;
    }

    @keyframes modalSlideIn {
      from { opacity: 0; transform: scale(0.88) translateY(12px); }
      to { opacity: 1; transform: scale(1) translateY(0); }
    }

    .modal-icon {
      width: 56px;
      height: 56px;
      border-radius: 50%;
      background: rgba(239, 68, 68, 0.15);
      border: 1px solid rgba(239, 68, 68, 0.3);
      color: #ef4444;
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0 auto 1.25rem;
      transition: 0.2s ease;
    }

    .modal-title {
      color: #fff;
      font-size: 1.1rem;
      font-weight: 700;
      margin: 0 0 0.6rem;
      font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
        sans-serif;
    }

    .modal-desc {
      color: rgba(203, 213, 225, 0.8);
      font-size: 0.875rem;
      line-height: 1.6;
      margin: 0 0 1.75rem;
      font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
        sans-serif;
    }

    .modal-actions {
      display: flex;
      gap: 0.75rem;
    }

    .modal-btn {
      flex: 1;
      padding: 0.6rem 1rem;
      border-radius: 12px;
      font-size: 0.875rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.18s ease;
      font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
        sans-serif;
      border: none;
    }

    .modal-btn-cancel {
      background: rgba(255, 255, 255, 0.07);
      border: 1px solid rgba(255, 255, 255, 0.12);
      color: rgba(226, 232, 240, 0.85);
    }

    .modal-btn-cancel:hover {
      background: rgba(255, 255, 255, 0.12);
      color: #fff;
    }

    .modal-btn-delete {
      background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
      color: #fff;
      box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
    }

    .modal-btn-delete:hover {
      filter: brightness(1.1);
      box-shadow: 0 6px 18px rgba(239, 68, 68, 0.4);
      transform: translateY(-1px);
    }

    .modal-btn-delete:active {
      transform: translateY(0px) scale(0.98);
    }
    `,
  ],
})
export class PdfDeleteModalComponent {
  @Input({ required: true }) filename!: string;

  @Output() confirm = new EventEmitter<void>();
  @Output() close = new EventEmitter<void>();

  onBackdropClick() {
    this.close.emit();
  }
}

