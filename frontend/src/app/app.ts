import { Component } from '@angular/core';

/**
 * Compatibility shim for legacy tests.
 *
 * The project uses `AppComponent` as the standalone bootstrap component.
 * Some generated spec files import `App` from `./app`.
 */
@Component({
  selector: 'app',
  standalone: true,
  template: '<h1>Hello, rfp-ui</h1>',
})
export class App {}

