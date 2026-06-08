import { Component } from '@angular/core';

/**
 * Compatibility shim for legacy tests.
 *
 * The project uses `ReportComponent` as the standalone component.
 * Some spec files import `Report` from `./report`.
 */
@Component({
  selector: 'app-report',
  standalone: true,
  template: '',
})
export class Report {}

