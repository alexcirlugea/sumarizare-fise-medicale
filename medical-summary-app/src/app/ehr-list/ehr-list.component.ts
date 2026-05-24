import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { forkJoin } from 'rxjs'; // Importă forkJoin pentru a rula traducerile în paralel

@Component({
  selector: 'app-ehr-list',
  standalone: false,
  templateUrl: './ehr-list.component.html',
  styleUrls: ['./ehr-list.component.css']
})
export class EhrListComponent implements OnInit {
  records: any[] = [];
  isLoading: boolean = true;

  // Stări pentru extindere separată
  expandedOriginal: { [key: number]: boolean } = {};
  expandedRomanian: { [key: number]: boolean } = {};
  
  // Stări pentru traduceri multiple
  translations: { [key: number]: { original: string, summary: string } } = {};
  isTranslating: { [key: number]: boolean } = {};

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.fetchEhrData();
  }

  fetchEhrData() {
    this.http.get<any[]>('http://localhost:8000/api/ehr')
      .subscribe({
        next: (data) => {
          this.records = data;
          this.records.forEach(r => {
            this.expandedOriginal[r.id] = false;
            this.expandedRomanian[r.id] = false;
          });
          this.isLoading = false;
        },
        error: (err) => {
          console.error('Eroare la preluarea datelor', err);
          this.isLoading = false;
        }
      });
  }

  toggleOriginal(id: number) {
    this.expandedOriginal[id] = !this.expandedOriginal[id];
  }

  toggleRomanian(id: number) {
    this.expandedRomanian[id] = !this.expandedRomanian[id];
  }

  // Traduce ambele secțiuni deodată
  translateEverything(record: any): void {
    if (record.language === 'ROMANIAN') return;

    this.isTranslating[record.id] = true;

    this.http.post<any>('http://localhost:8000/api/ehr/translate', {
      id: record.id,
      original_text: record.original_text,
      summary: record.summary
    }).subscribe({
      next: (response) => {
        // Salvăm traducerile direct în obiectul record din listă
        record.translated_text = response.translated_text;
        record.translated_summary = response.translated_summary;
        
        this.isTranslating[record.id] = false;
        this.expandedRomanian[record.id] = true; // Deschide automat acordeonul din istoric
      },
      error: (err) => {
        console.error('Eroare la traducerea din istoric:', err);
        this.isTranslating[record.id] = false;
      }
    });
  }
}