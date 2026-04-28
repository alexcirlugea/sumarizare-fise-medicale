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
  translateEverything(id: number, originalText: string, summaryText: string) {
    if (this.translations[id]) {
      this.expandedRomanian[id] = true; // Dacă e deja tradus, doar deschidem secțiunea
      return;
    }

    this.isTranslating[id] = true;

    // Trimitem ambele cereri de traducere în paralel
    const transOriginal = this.http.post<any>('http://localhost:8000/api/translate', { text: originalText });
    const transSummary = this.http.post<any>('http://localhost:8000/api/translate', { text: summaryText });

    forkJoin([transOriginal, transSummary]).subscribe({
      next: (results) => {
        this.translations[id] = {
          original: results[0].translation,
          summary: results[1].translation
        };
        this.isTranslating[id] = false;
        this.expandedRomanian[id] = true; // Deschidem automat varianta în română după traducere
      },
      error: (err) => {
        console.error('Eroare la traducere', err);
        this.isTranslating[id] = false;
      }
    });
  }
}