import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { DataService } from '../shared/data.service'; 

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
  isLoading: boolean = false;
  errorMessage: string = '';

  constructor(private http: HttpClient, private dataService: DataService) {}

  ngOnInit() {
    this.summary = this.dataService.summary;
    this.originalText = this.dataService.originalText;
  }

  onFileSelected(event: any) {
    this.selectedFile = event.target.files[0];
    this.summary = '';
    this.originalText = '';
    this.errorMessage = '';
  }

  onUpload() {
    if (!this.selectedFile) return;

    this.isLoading = true;
    const formData = new FormData();
    formData.append('file', this.selectedFile);

    this.http.post<any>('http://localhost:8000/upload-summary', formData)
      .subscribe({
        next: (response) => {
          this.summary = response.summary;
          this.originalText = response.original_text;

          this.dataService.saveSummaryData(this.originalText, this.summary);

          this.isLoading = false;
        },
        error: (error) => {
          console.error(error);
          this.errorMessage = "A apărut o eroare la procesarea fișierului.";
          this.isLoading = false;
        }
      });
  }
}