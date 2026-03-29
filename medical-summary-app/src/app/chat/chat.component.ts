import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-chat',
  standalone: false,
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.css']
})
export class ChatComponent {
  userMessage: string = '';
  // Mesajul inițial
  messages: { sender: 'user' | 'bot', text: string }[] = [
    { sender: 'bot', text: 'Salut! Asigură-te că ai încărcat o fișă la secțiunea "Sumarizare". Ce ai dori să afli despre pacient?' }
  ];
  isLoading: boolean = false;

  constructor(private http: HttpClient) {}

  sendMessage() {
    if (!this.userMessage.trim()) return;

    // Adăugăm mesajul utilizatorului în UI
    const currentMessage = this.userMessage;
    this.messages.push({ sender: 'user', text: currentMessage });
    this.userMessage = '';
    this.isLoading = true;

    // Trimitem la backend
    this.http.post<any>('http://localhost:8000/chat', { message: currentMessage })
      .subscribe({
        next: (response) => {
          this.messages.push({ sender: 'bot', text: response.reply });
          this.isLoading = false;
        },
        error: (error) => {
          console.error(error);
          this.messages.push({ sender: 'bot', text: 'A apărut o eroare de conexiune cu serverul.' });
          this.isLoading = false;
        }
      });
  }
}