import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class ApiService {
  baseUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  uploadRfp(file: File, sessionId: string) {
    console.log('UPLOAD SESSION:', sessionId);
    const formData = new FormData();

    formData.append('file', file);

    return this.http.post(
      `${this.baseUrl}/upload?session_id=${encodeURIComponent(sessionId)}`,
      formData,
    );
  }

  chatWithRfp(sessionId: string, question: string) {
    console.log('CHAT SESSION:', sessionId);
    return this.http.get(`${this.baseUrl}/chat`, {
      params: {
        session_id: sessionId,
        question: question,
      },
    });
  }

  searchRfp(sessionId: string, query: string) {
    return this.http.get(`${this.baseUrl}/search`, {
      params: {
        session_id: sessionId,
        query: query,
      },
    });
  }

  streamChat(sessionId: string, question: string) {
    const url = `${this.baseUrl}/stream-chat?session_id=${sessionId}&question=${encodeURIComponent(question)}`;

    return fetch(url, {
      method: 'GET',
      headers: {
        Accept: 'text/event-stream',
        // Hint: don't let browsers/proxies buffer
        'Cache-Control': 'no-cache',
      },
    });
  }

  // Fetch saved conversation history.
  // Expected backend to return either:
  //  - { messages: [{ role, content }] } OR
  //  - [{ role, content }]
  getChatHistory(sessionId: string) {
    return this.http.get(`${this.baseUrl}/chat-history`, {
      params: {
        session_id: sessionId,
      },
    });
  }

  getAllChats(sessionIds: string[]) {
    return this.http.get(`${this.baseUrl}/sessions`, {
      params: {
        session_ids: sessionIds.join(','),
      },
    });
  }

  clearChat(sessionId: string) {
    return this.http.delete(`${this.baseUrl}/clear-chat`, {
      params: {
        session_id: sessionId,
      },
    });
  }

  createNewChat(sourceSessionId?: string) {
    const url = sourceSessionId
      ? `${this.baseUrl}/sessions?source_session_id=${encodeURIComponent(sourceSessionId)}`
      : `${this.baseUrl}/sessions`;
    return this.http.post(url, {});
  }

  deleteChat(sessionId: string) {
    return this.http.delete(`${this.baseUrl}/sessions/${sessionId}`);
  }

  renameChat(sessionId: string, title: string) {
    return this.http.put(`${this.baseUrl}/sessions/${sessionId}`, { title });
  }

  clearAllChats() {
    return this.http.delete(`${this.baseUrl}/clear-all-chats`);
  }

  getUploadedDocuments() {
    return this.http.get(`${this.baseUrl}/documents`);
  }
}
