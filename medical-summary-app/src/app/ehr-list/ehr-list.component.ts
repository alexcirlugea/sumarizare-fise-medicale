import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { AuthService } from '../services/auth.service';
import { ActivatedRoute, Router } from '@angular/router';

@Component({
  selector: 'app-ehr-list',
  standalone: false,
  templateUrl: './ehr-list.component.html',
  styleUrls: ['./ehr-list.component.css']
})
export class EhrListComponent implements OnInit {
  records: any[] = [];
  isLoading = true;
  currentUserUid: string = '';
  viewingPatientId: number | null = null;
  viewingPatientName: string | null = null; 

  isTranslating: { [key: number]: boolean } = {};
  expandedOriginal: { [key: number]: boolean } = {};
  expandedRomanian: { [key: number]: boolean } = {};

  constructor(
    private http: HttpClient,
    private authService: AuthService,
    private route: ActivatedRoute,
    private router: Router
  ) {}

  ngOnInit(): void {
    // Verificăm dacă avem un ID de pacient în URL
    this.route.queryParams.subscribe(params => {
      if (params['patientId']) {
        this.viewingPatientId = Number(params['patientId']);
        this.viewingPatientName = params['patientName'] || 'Nume necunoscut';
        this.loadRecordsForPatient(this.viewingPatientId);
      } else {
        // Dacă nu e niciun ID, încărcăm fișele utilizatorului logat
        this.authService.currentUserSubject.subscribe(user => {
          if (user) {
            this.currentUserUid = user.uid;
            this.loadMyRecords();
          }
        });
      }
    });
  }

  loadRecordsForPatient(patientId: number) {
    this.http.get<any[]>(`http://localhost:8000/api/ehr/patient/${patientId}`).subscribe({
      next: (data) => {
        this.records = data;
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Eroare la încărcarea fișelor pacientului', err);
        this.isLoading = false;
      }
    });
  }

  loadMyRecords() {
    this.http.get<any[]>(`http://localhost:8000/api/ehr?uid=${this.currentUserUid}`).subscribe({
      next: (data) => {
        this.records = data;
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Eroare la încărcarea propriilor fișe', err);
        this.isLoading = false;
      }
    });
  }

  // --- FUNCȚIILE DE INTERFAȚĂ (care lipseau) ---

  toggleOriginal(recordId: number) {
    this.expandedOriginal[recordId] = !this.expandedOriginal[recordId];
  }

  toggleRomanian(recordId: number) {
    this.expandedRomanian[recordId] = !this.expandedRomanian[recordId];
  }

  translateEverything(record: any) {
    this.isTranslating[record.id] = true;
    
    // Apelul către ruta ta de traducere din FastAPI
    this.http.post('http://localhost:8000/api/ehr/translate', { record_id: record.id }).subscribe({
      next: (response: any) => {
        // Actualizăm direct în listă ca să apară pe ecran
        record.specialty_ro = response.specialty_ro;
        record.diagnosis_ro = response.diagnosis_ro;
        record.summary_ro = response.summary_ro;
        
        this.isTranslating[record.id] = false;
        
        // Deschidem automat tab-ul de română după ce se termină traducerea
        this.expandedRomanian[record.id] = true; 
      },
      error: (err) => {
        console.error('Eroare la traducere', err);
        this.isTranslating[record.id] = false;
        alert('A apărut o eroare la traducerea fișei.');
      }
    });
  }

  goToUploadForPatient() {
    // Când mergem la upload, îi dăm mai departe și numele!
    this.router.navigate(['/summary'], { 
      queryParams: { 
        patientId: this.viewingPatientId,
        patientName: this.viewingPatientName 
      } 
    });
  }

  // FUNCȚIA PENTRU COȘUL AI
  addToChatContext(record: any) {
    // Citim "coșul" actual din sessionStorage (dacă există)
    let chatIds = JSON.parse(sessionStorage.getItem('selectedChatIds') || '[]');
    
    if (!chatIds.includes(record.id)) {
      chatIds.push(record.id);
      sessionStorage.setItem('selectedChatIds', JSON.stringify(chatIds));
      alert(`✅ Fișa "${record.filename}" a fost adăugată în contextul pentru Chat AI!`);
    } else {
      alert(`⚠️ Fișa "${record.filename}" este deja selectată pentru Chat.`);
    }
  }
}