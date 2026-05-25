import { Component } from '@angular/core';
import { AuthService } from '../services/auth.service';
import { Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-login',
  standalone: false,
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent {
  isLoading = false;
  isLoginMode = true; // Dacă e true arată Login, dacă e false arată Register

  // Datele din formular
  email = '';
  password = '';
  fullName = '';

  constructor(
    private authService: AuthService, 
    private router: Router,
    private http: HttpClient
  ) {}

  switchMode() {
    this.isLoginMode = !this.isLoginMode;
  }

  async onGoogleLogin() {
    this.isLoading = true;
    try {
      const user = await this.authService.loginWithGoogle();
      this.syncUserWithBackend(user);
    } catch (error: any) {
      alert('Eroare Google: ' + error.message);
      this.isLoading = false;
    }
  }

  async onSubmit() {
    if (!this.email || !this.password) {
      alert('Te rog completează email-ul și parola!');
      return;
    }

    this.isLoading = true;
    try {
      let user;
      if (this.isLoginMode) {
        user = await this.authService.loginWithEmail(this.email, this.password);
      } else {
        if (!this.fullName) {
          alert('Te rog introdu și numele complet pentru înregistrare!');
          this.isLoading = false;
          return;
        }
        user = await this.authService.registerWithEmail(this.email, this.password, this.fullName);
      }
      this.syncUserWithBackend(user);
    } catch (error: any) {
      alert('Eroare autentificare: ' + error.message);
      this.isLoading = false;
    }
  }

  // Această funcție comunică cu FastAPI
  private syncUserWithBackend(user: any) {
    this.http.post<any>('http://localhost:8000/api/auth/sync', {
      uid: user.uid,
      email: user.email,
      full_name: user.displayName || 'Utilizator'
    }).subscribe({
      next: (response) => {
        localStorage.setItem('userRole', response.role);
        this.authService.userRoleSubject.next(response.role);
        this.router.navigate(['/home']);
      },
      error: (err) => {
        console.error('Eroare conectare backend', err);
        alert('Eroare de server. Verifică dacă FastAPI rulează.');
        this.isLoading = false;
      }
    });
  }
}