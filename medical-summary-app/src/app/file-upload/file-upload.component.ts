import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { forkJoin } from 'rxjs';

@Component({
  selector: 'app-file-upload',
  standalone: false,
  templateUrl: './file-upload.component.html',
  styleUrls: ['./file-upload.component.css']
})
export class FileUploadComponent implements OnInit {
  selectedFiles: File[] = [];
  isUploading = false;
  uploadError: string | null = null;
  
  currentBatch: any[] = [];
  
  // Stări pentru extindere/restrângere
  expandedOriginal: { [key: string]: boolean } = {};
  expandedRomanian: { [key: string]: boolean } = {}; // NOU
  isTranslating: { [key: string]: boolean } = {};

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    const savedBatch = sessionStorage.getItem('currentBatch');
    if (savedBatch) {
      this.currentBatch = JSON.parse(savedBatch);
    }
  }

  onFileSelected(event: any): void {
    const files: FileList = event.target.files;
    this.uploadError = null;

    if (files.length > 10) {
      this.uploadError = "Te rugăm să selectezi maxim 10 fișiere pentru o procesare optimă.";
      this.selectedFiles = [];
      return;
    }
    this.selectedFiles = Array.from(files);
  }

  onUpload(): void {
    if (this.selectedFiles.length === 0) return;

    this.isUploading = true;
    this.uploadError = null;

    const formData = new FormData();
    this.selectedFiles.forEach(file => {
      formData.append('files', file);
    });

    this.http.post<any>('http://localhost:8000/upload-summary', formData).subscribe({
      next: (response) => {
        this.currentBatch = response.processed_files;
        sessionStorage.setItem('currentBatch', JSON.stringify(this.currentBatch));
        this.selectedFiles = [];
        this.isUploading = false;
      },
      error: (err) => {
        console.error('Eroare la încărcare', err);
        this.uploadError = err.error?.detail || "A apărut o eroare la procesarea fișierelor.";
        this.isUploading = false;
      }
    });
  }

  toggleOriginal(filename: string): void {
    this.expandedOriginal[filename] = !this.expandedOriginal[filename];
  }

  // NOU: Logica pentru a deschide/închide varianta în română
  toggleRomanian(filename: string): void {
    this.expandedRomanian[filename] = !this.expandedRomanian[filename];
  }

  translateContent(record: any): void {
    if (record.language === 'ROMANIAN') return;

    this.isTranslating[record.filename] = true;

    // Apelăm endpoint-ul unificat, trimițând ID-ul fișei
    this.http.post<any>('http://localhost:8000/api/ehr/translate', { 
      id: record.id, 
      original_text: record.original_text, 
      summary: record.summary 
    }).subscribe({
      next: (response) => {
        // Alocăm traducerile sosite direct pe obiectul record
        record.translated_text = response.translated_text;
        record.translated_summary = response.translated_summary;
        
        this.isTranslating[record.filename] = false;
        this.expandedRomanian[record.filename] = true; // Deschide automat acordeonul
        
        // Salvăm în sessionStorage starea curentă tradusă
        sessionStorage.setItem('currentBatch', JSON.stringify(this.currentBatch));
      },
      error: (err) => {
        console.error('Eroare la traducere', err);
        this.isTranslating[record.filename] = false;
      }
    });
  }
}