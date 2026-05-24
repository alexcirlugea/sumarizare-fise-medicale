import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-chat',
  standalone: false,
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.css']
})
export class ChatComponent implements OnInit {
  userMessage: string = '';
  messages: { sender: 'user' | 'bot', text: string }[] = [
    { sender: 'bot', text: 'Salut! Folosesc ultimele 5 fișe încărcate drept context. Poți schimba acest lucru din butonul "Context". Ce ai dori să afli?' }
  ];
  isLoading: boolean = false;

  // NOU: Variabile pentru sistemul de Context
  allRecords: any[] = [];
  filteredRecords: any[] = [];
  selectedIds: number[] = [];
  showContextDropdown: boolean = false;
  searchQuery: string = '';

  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.fetchAvailableRecords();
  }

  // Aducem toate fișele disponibile pentru a le afișa în meniu
  fetchAvailableRecords() {
    this.http.get<any[]>('http://localhost:8000/api/ehr').subscribe({
      next: (data) => {
        this.allRecords = data;
        this.filteredRecords = data;
        // Selectăm automat primele 5 fișiere (care sunt cele mai recente datorită ORDER BY id DESC)
        this.selectedIds = data.slice(0, 5).map(r => r.id);
      },
      error: (err) => console.error("Eroare la preluarea fișelor pentru context", err)
    });
  }

  // Deschide/închide meniul
  toggleContextDropdown() {
    this.showContextDropdown = !this.showContextDropdown;
  }

  // Logica pentru Search Bar
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

  // Bifarea / debifarea unui fișier
  toggleSelection(id: number) {
    const index = this.selectedIds.indexOf(id);
    if (index > -1) {
      this.selectedIds.splice(index, 1); // Debifăm
    } else {
      if (this.selectedIds.length < 5) {
        this.selectedIds.push(id); // Bifăm doar dacă avem sub 5
      }
    }
  }

  sendMessage() {
    if (!this.userMessage.trim()) return;

    const currentMessage = this.userMessage;
    this.messages.push({ sender: 'user', text: currentMessage });
    this.userMessage = '';
    this.isLoading = true;
    this.showContextDropdown = false; // Închidem meniul când dă trimite

    // Trimitem acum și lista de ID-uri selectate!
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