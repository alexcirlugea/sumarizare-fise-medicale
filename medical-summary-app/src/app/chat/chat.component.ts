import { Component, OnInit, OnDestroy } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { AuthService } from '../services/auth.service';
import { ActivatedRoute } from '@angular/router';

@Component({
  selector: 'app-chat',
  standalone: false,
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.css']
})
export class ChatComponent implements OnInit, OnDestroy {
  userMessage: string = '';
  messages: { sender: 'user' | 'bot', text: string }[] = [
    { sender: 'bot', text: 'Salut! Îmi poți pune întrebări clinice specifice despre pacienți sau statistici generale despre fișe. Cu ce te pot ajuta?' }
  ];
  isLoading: boolean = false;

  scope: 'global' | 'patient' = 'global';
  selectedPatientId: number | null = null;
  myPatients: any[] = [];
  userRole: string = '';
  userUid: string = '';
  selectedIds: number[] = [];

  private storageListener = (event: StorageEvent) => {
    if (event.key === 'chatSelectedIds') {
      this.selectedIds = event.newValue ? JSON.parse(event.newValue) : [];
    }
  };

  constructor(
    private http: HttpClient, 
    private authService: AuthService,
    private route: ActivatedRoute
  ) {}

  ngOnInit() {
    this.authService.currentUserSubject.subscribe(user => {
      if (user) {
        this.userUid = user.uid;
        if (this.userRole === 'medic') {
          this.fetchPatients(user.uid);
        }
      }
    });

    this.authService.userRoleSubject.subscribe(role => {
      if (role) {
        this.userRole = role;
        if (role === 'medic' && this.userUid) {
          this.fetchPatients(this.userUid);
        }
      }
    });

    // Preluăm parametrii din URL dacă doctorul vine direct de la dosarul unui pacient
    this.route.queryParams.subscribe(params => {
      if (params['patientId']) {
        this.scope = 'patient';
        this.selectedPatientId = Number(params['patientId']);
      }
    });

    // Citim selecția contextului din sessionStorage
    const stored = sessionStorage.getItem('chatSelectedIds');
    if (stored) {
      this.selectedIds = JSON.parse(stored);
    }

    // Ascultăm schimbări din alte tab-uri/componente
    window.addEventListener('storage', this.storageListener);
  }

  ngOnDestroy() {
    window.removeEventListener('storage', this.storageListener);
  }

  clearContext() {
    this.selectedIds = [];
    sessionStorage.removeItem('chatSelectedIds');
  }

  fetchPatients(doctorUid: string) {
    this.http.get<any[]>(`http://localhost:8000/api/doctors/${doctorUid}/patients`).subscribe({
      next: (data) => {
        this.myPatients = data;
      },
      error: (err) => console.error("Eroare la preluarea pacienților medicului", err)
    });
  }

  onScopeChange() {
    if (this.scope === 'global') {
      this.selectedPatientId = null;
    } else if (this.myPatients.length > 0 && !this.selectedPatientId) {
      // Selectăm primul pacient implicit
      this.selectedPatientId = this.myPatients[0].id;
    }
  }

  sendMessage() {
    if (!this.userMessage.trim()) return;

    const currentMessage = this.userMessage;
    this.messages.push({ sender: 'user', text: currentMessage });
    this.userMessage = '';
    this.isLoading = true;

    const payload: any = {
      message: currentMessage,
      uid: this.userUid,
      scope: this.scope,
      patient_id: this.scope === 'patient' ? this.selectedPatientId : null,
      selected_ids: this.selectedIds.length > 0 ? this.selectedIds : null
    };

    this.http.post<any>('http://localhost:8000/chat', payload).subscribe({
      next: (response) => {
        this.messages.push({ sender: 'bot', text: response.reply });
        this.isLoading = false;
      },
      error: (error) => {
        console.error(error);
        this.messages.push({ sender: 'bot', text: 'A apărut o eroare de conexiune cu serverul. Te rog reîncearcă.' });
        this.isLoading = false;
      }
    });
  }
}