import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { AuthService } from '../services/auth.service'; // Asigură-te că ruta este corectă

@Component({
  selector: 'app-chat',
  standalone: false,
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.css']
})
export class ChatComponent implements OnInit {
  userMessage: string = '';
  messages: { sender: 'user' | 'bot', text: string }[] = [
    { sender: 'bot', text: 'Salut! Folosesc fișele selectate drept context. Ce ai dori să afli?' }
  ];
  isLoading: boolean = false;

  allRecords: any[] = [];
  filteredRecords: any[] = [];
  selectedIds: number[] = [];
  showContextDropdown: boolean = false;
  searchQuery: string = '';

  constructor(private http: HttpClient, private authService: AuthService) {}

  ngOnInit() {
    // 1. Preluăm ce am selectat din cealaltă pagină
    const savedContext = sessionStorage.getItem('selectedChatIds');
    if (savedContext) {
      this.selectedIds = JSON.parse(savedContext);
    }

    // 2. Aducem UID-ul și facem apelul GET corect
    this.authService.currentUserSubject.subscribe(user => {
      if (user) {
        this.fetchAvailableRecords(user.uid);
      }
    });
  }

  // Am adăugat UID ca parametru!
  fetchAvailableRecords(uid: string) {
    this.http.get<any[]>(`http://localhost:8000/api/ehr?uid=${uid}`).subscribe({
      next: (data) => {
        this.allRecords = data;
        this.filteredRecords = data;
        
        // Dacă NU am selectat nimic din pagina cealaltă, abia atunci luăm primele 5 automat
        if (this.selectedIds.length === 0 && data.length > 0) {
           this.selectedIds = data.slice(0, 5).map(r => r.id);
           sessionStorage.setItem('selectedChatIds', JSON.stringify(this.selectedIds));
        }
      },
      error: (err) => console.error("Eroare la preluarea fișelor pentru context", err)
    });
  }

  toggleContextDropdown() {
    this.showContextDropdown = !this.showContextDropdown;
  }

  filterRecords() {
    if (!this.searchQuery.trim()) {
      this.filteredRecords = this.allRecords;
    } else {
      const lowerQuery = this.searchQuery.toLowerCase();
      this.filteredRecords = this.allRecords.filter(r => 
        r.filename.toLowerCase().includes(lowerQuery)
      );
    }
  }

  toggleSelection(id: number) {
    const index = this.selectedIds.indexOf(id);
    if (index > -1) {
      this.selectedIds.splice(index, 1);
    } else {
      if (this.selectedIds.length < 5) {
        this.selectedIds.push(id);
      } else {
        alert("Maxim 5 fișe permise.");
      }
    }
    // Salvăm din nou ca să rămână sincronizat
    sessionStorage.setItem('selectedChatIds', JSON.stringify(this.selectedIds));
  }

  sendMessage() {
    if (!this.userMessage.trim()) return;

    const currentMessage = this.userMessage;
    this.messages.push({ sender: 'user', text: currentMessage });
    this.userMessage = '';
    this.isLoading = true;
    this.showContextDropdown = false; 

    this.http.post<any>('http://localhost:8000/chat', { 
      message: currentMessage,
      selected_ids: this.selectedIds 
    }).subscribe({
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