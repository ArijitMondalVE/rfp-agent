import { Component } from '@angular/core';

/**
 * Compatibility shim for legacy tests.
 *
 * The project uses `UploadComponent` as the standalone component.
 * Some spec files import `Upload` from `./upload`.
 */
@Component({
  selector: 'app-upload',
  standalone: true,
  template: '',
})
export class Upload {}

