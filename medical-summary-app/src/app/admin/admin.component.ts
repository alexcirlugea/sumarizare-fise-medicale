import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-admin',
  standalone: false,
  templateUrl: './admin.component.html',
  styleUrls: ['./admin.component.css']
})
export class AdminComponent implements OnInit {
  users: any[] = [];
  isLoading = true;

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.loadUsers();
  }

  loadUsers() {
    this.http.get<any[]>('http://localhost:8000/api/auth/users').subscribe({
      next: (data) => {
        this.users = data;
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Eroare la încărcarea utilizatorilor', err);
        this.isLoading = false;
      }
    });
  }

  changeRole(userId: number, newRole: string) {
    this.http.put(`http://localhost:8000/api/auth/users/${userId}/role`, { role: newRole }).subscribe({
      next: () => {
        // Actualizăm direct în listă ca să nu dăm iar refresh la toată pagina
        const user = this.users.find(u => u.id === userId);
        if (user) {
          user.role = newRole;
        }
      },
      error: (err) => {
        console.error('Eroare la schimbarea rolului', err);
        alert('Nu s-a putut actualiza rolul.');
      }
    });
  }

  deleteUser(userId: number, userName: string) {
    const confirmare = confirm(`Ești absolut sigur că vrei să ștergi contul lui ${userName}? Această acțiune va șterge și toate datele și fișele sale medicale.`);
    
    if (confirmare) {
      this.http.delete(`http://localhost:8000/api/auth/users/${userId}`).subscribe({
        next: () => {
          // Scoatem utilizatorul din listă vizual, ca să nu dăm refresh la pagină
          this.users = this.users.filter(u => u.id !== userId);
        },
        error: (err) => {
          console.error('Eroare la ștergere:', err);
          alert('Nu s-a putut șterge utilizatorul.');
        }
      });
    }
  }
}