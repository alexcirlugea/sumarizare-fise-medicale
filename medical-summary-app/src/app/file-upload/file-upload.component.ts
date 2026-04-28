import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { DataService } from '../shared/data.service'; 
import { forkJoin } from 'rxjs'; 

@Component({
  selector: 'app-file-upload',
  standalone: false,
  templateUrl: './file-upload.component.html',
  styleUrl: './file-upload.component.css'
})
export class FileUploadComponent implements OnInit {
  selectedFile: File | null = null;
  summary: string = '';
  originalText: string = '';
  filename: string = ''; 
  isLoading: boolean = false;
  errorMessage: string = '';

  
  expandedOriginal: boolean = true; 
  expandedRomanian: boolean = false;
  translation: { original: string, summary: string } | null = null;
  isTranslating: boolean = false;

  constructor(private http: HttpClient, private dataService: DataService) {}

  ngOnInit() {
    this.summary = this.dataService.summary;
    this.originalText = this.dataService.originalText;
    // Dacă avem deja date, înseamnă că s-a făcut un upload anterior
    if (this.summary) this.expandedOriginal = true;
  }

  onFileSelected(event: any) {
    this.selectedFile = event.target.files[0];
    this.summary = '';
    this.originalText = '';
    this.translation = null;
    this.errorMessage = '';
  }

  onUpload() {
    if (!this.selectedFile) return;

    this.isLoading = true;
    const formData = new FormData();
    formData.append('file', this.selectedFile);
    this.filename = this.selectedFile.name;

    this.http.post<any>('http://localhost:8000/upload-summary', formData)
      .subscribe({
        next: (response) => {
          this.summary = response.summary;
          this.originalText = response.original_text;
          this.dataService.saveSummaryData(this.originalText, this.summary);
          
          this.isLoading = false;
          this.expandedOriginal = true; 
        },
        error: (error) => {
          console.error(error);
          this.errorMessage = "A apărut o eroare la procesarea fișierului.";
          this.isLoading = false;
        }
      });
  }

  toggleOriginal() { this.expandedOriginal = !this.expandedOriginal; }
  toggleRomanian() { this.expandedRomanian = !this.expandedRomanian; }

  translateEverything() {
    if (this.translation) {
      this.expandedRomanian = true;
      return;
    }

    this.isTranslating = true;
    const transOriginal = this.http.post<any>('http://localhost:8000/api/translate', { text: this.originalText });
    const transSummary = this.http.post<any>('http://localhost:8000/api/translate', { text: this.summary });

    forkJoin([transOriginal, transSummary]).subscribe({
      next: (results) => {
        this.translation = {
          original: results[0].translation,
          summary: results[1].translation
        };
        this.isTranslating = false;
        this.expandedRomanian = true;
      },
      error: (err) => {
        console.error('Eroare la traducere', err);
        this.isTranslating = false;
      }
    });
  }
}