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

  async logout() {
    await this.authService.logout();
    localStorage.removeItem('userRole');
    
    this.authService.userRoleSubject.next(null); 
    
    this.router.navigate(['/login']);
  }
}