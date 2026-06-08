import { Component } from '@angular/core';

/**
 * Compatibility shim for legacy tests.
 *
 * The project uses `ChatComponent` as the standalone component.
 * Some spec files import `Chat` from `./chat`.
 */
@Component({
  selector: 'app-chat',
  standalone: true,
  template: '',
})
export class Chat {}

