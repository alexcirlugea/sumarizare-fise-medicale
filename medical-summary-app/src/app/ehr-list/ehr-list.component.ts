import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { AuthService } from '../services/auth.service';
import { ActivatedRoute, Router } from '@angular/router';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';

@Component({
  selector: 'app-ehr-list',
  standalone: false,
  templateUrl: './ehr-list.component.html',
  styleUrls: ['./ehr-list.component.css']
})
export class EhrListComponent implements OnInit {
  records: any[] = [];
  allRecords: any[] = [];
  selectedSpecialty: string = '';
  uniqueSpecialties: string[] = [];
  isLoading = true;
  currentUserUid: string = '';
  viewingPatientId: number | null = null;
  viewingPatientName: string | null = null; 

  isTranslating: { [key: number]: boolean } = {};
  expandedOriginal: { [key: number]: boolean } = {};
  expandedRomanian: { [key: number]: boolean } = {};

  selectedForChatIds: number[] = [];

  constructor(
    private http: HttpClient,
    private authService: AuthService,
    private route: ActivatedRoute,
    private router: Router,
    private sanitizer: DomSanitizer
  ) {}

  ngOnInit(): void {
    // 1. Încărcăm coșul existent din sessionStorage (dacă am mai bifat ceva)
    const savedContext = sessionStorage.getItem('selectedChatIds');
    if (savedContext) {
      this.selectedForChatIds = JSON.parse(savedContext);
    }

    this.route.queryParams.subscribe(params => {
      if (params['patientId']) {
        this.viewingPatientId = Number(params['patientId']);
        this.viewingPatientName = params['patientName'] || 'Nume necunoscut';
        this.loadRecordsForPatient(this.viewingPatientId);
      } else {
        this.authService.currentUserSubject.subscribe(user => {
          if (user) {
            this.currentUserUid = user.uid;
            this.loadMyRecords();
          }
        });
      }
    });
  }

  // LOGICA PENTRU CHAT - Modificată să folosească sessionStorage
  toggleChatSelection(recordId: number) {
    const index = this.selectedForChatIds.indexOf(recordId);
    
    if (index !== -1) {
      this.selectedForChatIds.splice(index, 1); // Debifăm
    } else {
      if (this.selectedForChatIds.length >= 5) {
        alert("Poți selecta maxim 5 fișe pentru context!");
        return;
      }
      this.selectedForChatIds.push(recordId); // Bifăm
    }
    
    // Salvăm în sessionStorage ca să le vadă componenta de Chat
    sessionStorage.setItem('selectedChatIds', JSON.stringify(this.selectedForChatIds));
  }

  isRecordSelected(recordId: number): boolean {
    return this.selectedForChatIds.includes(recordId);
  }

  loadRecordsForPatient(patientId: number) {
    this.http.get<any[]>(`http://localhost:8000/api/ehr/patient/${patientId}`).subscribe({
      next: (data) => {
        this.allRecords = data;
        this.updateUniqueSpecialties();
        this.applyFilter();
        this.isLoading = false;
      },
      error: (err) => { console.error(err); this.isLoading = false; }
    });
  }

  loadMyRecords() {
    this.http.get<any[]>(`http://localhost:8000/api/ehr?uid=${this.currentUserUid}`).subscribe({
      next: (data) => {
        this.allRecords = data;
        this.updateUniqueSpecialties();
        this.applyFilter();
        this.isLoading = false;
      },
      error: (err) => { console.error(err); this.isLoading = false; }
    });
  }

  updateUniqueSpecialties() {
    const specs = this.allRecords
      .map(r => r.specialty)
      .filter(s => s && s !== 'Nespecificat');
    this.uniqueSpecialties = Array.from(new Set(specs)).sort();
  }

  onSpecialtyChange(specialty: string) {
    this.selectedSpecialty = specialty;
    this.applyFilter();
  }

  applyFilter() {
    if (!this.selectedSpecialty) {
      this.records = this.allRecords;
    } else {
      this.records = this.allRecords.filter(r => r.specialty === this.selectedSpecialty);
    }
  }

  toggleOriginal(recordId: number) { this.expandedOriginal[recordId] = !this.expandedOriginal[recordId]; }
  toggleRomanian(recordId: number) { this.expandedRomanian[recordId] = !this.expandedRomanian[recordId]; }

  translateEverything(record: any) {
      this.isTranslating[record.id] = true;
      const requestBody = { id: record.id, original_text: record.original_text, summary: record.summary };
      
      this.http.post('http://localhost:8000/api/ehr/translate', requestBody).subscribe({
        next: (response: any) => {
          record.translated_text = response.translated_text;
          record.translated_summary = response.translated_summary;
          this.isTranslating[record.id] = false;
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
    this.router.navigate(['/summary'], { 
      queryParams: { patientId: this.viewingPatientId, patientName: this.viewingPatientName } 
    });
  }

  formatOriginalText(text: string): SafeHtml {
    if (!text) return '';
    
    // Înlocuim <TAG> cu span, dar adăugăm un newline (\n) înaintea lui
    // ca să ne asigurăm că browserul știe că urmează un bloc nou.
    const formatted = text.replace(/<([^>]+)>/g, '\n<span class="medical-tag">$1</span>\n');
    
    return this.sanitizer.bypassSecurityTrustHtml(formatted);
  }
}