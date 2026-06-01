import { Component } from '@angular/core';

import { UploadComponent } from '../upload/upload.component';
import { ChatComponent } from '../chat/chat.component';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [UploadComponent, ChatComponent],
  templateUrl: './sidebar.html',
  styleUrl: './sidebar.css',
})
export class Sidebar {
  
}

