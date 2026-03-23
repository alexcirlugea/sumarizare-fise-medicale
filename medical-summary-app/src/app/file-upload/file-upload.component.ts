import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-file-upload',
  standalone: false,
  templateUrl: './file-upload.component.html',
  styleUrl: './file-upload.component.css'
})
export class FileUploadComponent {
  selectedFile: File | null = null;
  summary: string = '';
  isLoading: boolean = false;
  errorMessage: string = '';

  constructor(private http: HttpClient) {}

  onFileSelected(event: any) {
    this.selectedFile = event.target.files[0];
    this.summary = '';
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
