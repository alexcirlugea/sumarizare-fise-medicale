import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { AuthService } from '../services/auth.service';
import { ActivatedRoute } from '@angular/router';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';

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
  expandedRomanian: { [key: string]: boolean } = {};
  isTranslating: { [key: string]: boolean } = {};

  // Variabile pentru a ști al cui este documentul
  currentUserUid: string = '';
  targetPatientId: number | null = null;
  targetPatientName: string | null = null;

  userRole: string | null = null;
  patients: any[] = [];

  // Am injectat AuthService și ActivatedRoute în constructor
  constructor(
    private http: HttpClient,
    private authService: AuthService,
    private route: ActivatedRoute,
    private sanitizer: DomSanitizer
  ) {}

  ngOnInit(): void {
    // 1. Logica ta veche (păstrată intactă)
    const savedBatch = sessionStorage.getItem('currentBatch');
    this.userRole = localStorage.getItem('userRole');

    if (savedBatch) {
      this.currentBatch = JSON.parse(savedBatch);
    }

    // 2. Aflăm cine e logat (UID-ul curent)
    this.authService.currentUserSubject.subscribe(user => {
      if (user) {
        this.currentUserUid = user.uid;
        if (this.userRole === 'medic' && !this.targetPatientId) {
          this.loadMyPatients();
        }
      }
    });

    // 3. Verificăm dacă în URL scrie "?patientId=X" (adică a fost trimis de medic)
    this.route.queryParams.subscribe(params => {
      if (params['patientId']) {
        this.targetPatientId = Number(params['patientId']);
        this.targetPatientName = params['patientName'] || 'Pacient';
      }
    });
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
    if (!this.targetPatientId && !this.currentUserUid) {
      this.uploadError = "Eroare de securitate: Nu s-a putut identifica pentru cine se încarcă fișele.";
      return;
    }

    if (this.selectedFiles.length === 0) return;

    this.isUploading = true;
    this.uploadError = null;

    const formData = new FormData();
    this.selectedFiles.forEach(file => {
      formData.append('files', file);
    });

    // 1. UID-ul este obligatoriu pentru FastAPI, deci îl trimitem mereu
    if (this.currentUserUid) {
      formData.append('uid', this.currentUserUid);
    } else {
      this.uploadError = "Eroare: Utilizatorul nu este autentificat.";
      this.isUploading = false;
      return;
    }

    // 2. Dacă există un pacient țintă (ex: logat ca medic), adăugăm ȘI patient_id
    if (this.targetPatientId) {
      formData.append('patient_id', this.targetPatientId.toString());
    }

    // Am păstrat ruta ta originală: '/upload-summary'
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

  toggleRomanian(filename: string): void {
    this.expandedRomanian[filename] = !this.expandedRomanian[filename];
  }

  translateContent(record: any): void {
    if (record.language === 'ROMANIAN') return;

    this.isTranslating[record.filename] = true;

    this.http.post<any>('http://localhost:8000/api/ehr/translate', { 
      id: record.id, 
      original_text: record.original_text, 
      summary: record.summary 
    }).subscribe({
      next: (response) => {
        record.translated_text = response.translated_text;
        record.translated_summary = response.translated_summary;
        
        this.isTranslating[record.filename] = false;
        this.expandedRomanian[record.filename] = true;
        
        sessionStorage.setItem('currentBatch', JSON.stringify(this.currentBatch));
      },
      error: (err) => {
        console.error('Eroare la traducere', err);
        this.isTranslating[record.filename] = false;
      }
    });
  }

  formatOriginalText(text: string): SafeHtml {
    if (!text) return '';
    
    const formatted = text.replace(/<([^>]+)>/g, '\n<span class="medical-tag">$1</span>\n');
    
    return this.sanitizer.bypassSecurityTrustHtml(formatted);
  }

  loadMyPatients() {
    this.http.get<any[]>(`http://localhost:8000/api/doctors/${this.currentUserUid}/patients`).subscribe({
      next: (data) => {
        this.patients = data;
      },
      error: (err) => {
        console.error("Eroare la încărcarea pacienților:", err);
      }
    });
  }

  onPatientSelect(patientIdStr: string) {
    if (!patientIdStr) {
      this.targetPatientId = null;
      this.targetPatientName = null;
      return;
    }
    const patientId = Number(patientIdStr);
    const p = this.patients.find(x => x.id === patientId);
    if (p) {
      this.targetPatientId = p.id;
      this.targetPatientName = p.full_name;
    }
  }

  resetSelectedPatient() {
    this.targetPatientId = null;
    this.targetPatientName = null;
    this.selectedFiles = [];
    this.loadMyPatients();
  }
}