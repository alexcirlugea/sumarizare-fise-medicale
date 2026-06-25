import { Component, OnInit } from '@angular/core';
import { AuthService } from './services/auth.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: false,
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit {
  title = 'medical-summary-app';
  user: any = null;
  userRole: string | null = null; // Adăugăm o variabilă pentru rol

  constructor(private authService: AuthService, private router: Router) {}

  ngOnInit() {
    this.authService.currentUserSubject.subscribe(currentUser => {
      this.user = currentUser;
    });

    this.authService.userRoleSubject.subscribe(role => {
      this.userRole = role;
    });
  }

  // În app.component.ts
  async logout() {
    await this.authService.logout();
    
    // 1. Ștergem absolut tot din memoria browserului (localStorage și sessionStorage)
    localStorage.clear();
    sessionStorage.clear();
    
    this.authService.userRoleSubject.next(null); 
    
    // 2. În loc de this.router.navigate(['/login']), facem un redirect de sistem.
    // Asta va "omorî" memoria RAM a aplicației Angular și va încărca totul de la zero!
    window.location.href = '/login';
  }
}