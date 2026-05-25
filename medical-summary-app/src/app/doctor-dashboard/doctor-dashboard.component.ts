import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { AuthService } from '../services/auth.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-doctor-dashboard',
  standalone: false,
  templateUrl: './doctor-dashboard.component.html',
  styleUrls: ['./doctor-dashboard.component.css']
})
export class DoctorDashboardComponent implements OnInit {
  patients: any[] = [];
  patientEmail = '';
  doctorUid = '';
  isLoading = true;

  constructor(
    private http: HttpClient,
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.authService.currentUserSubject.subscribe(user => {
      if (user) {
        this.doctorUid = user.uid;
        this.loadPatients();
      }
    });
  }

  loadPatients() {
    this.http.get<any[]>(`http://localhost:8000/api/doctors/${this.doctorUid}/patients`)
      .subscribe({
        next: (data) => {
          this.patients = data;
          this.isLoading = false;
        },
        error: (err) => {
          console.error('Eroare la încărcarea pacienților', err);
          this.isLoading = false;
        }
      });
  }

  onLinkPatient() {
    if (!this.patientEmail) {
      alert('Te rog introdu adresa de email a pacientului!');
      return;
    }

    const body = {
      doctor_uid: this.doctorUid,
      patient_email: this.patientEmail
    };

    this.http.post('http://localhost:8000/api/doctors/link-patient', body)
      .subscribe({
        next: (response: any) => {
          alert(response.message);
          this.patientEmail = ''; 
          this.loadPatients(); 
        },
        error: (err) => {
          console.error(err);
          alert(err.error?.detail || 'A apărut o eroare la asocierea pacientului.');
        }
      });
  }

  viewPatientHistory(patientId: number, patientName: string) {
    this.router.navigate(['/ehr'], { 
      queryParams: { patientId: patientId, patientName: patientName } 
    });
  }
}