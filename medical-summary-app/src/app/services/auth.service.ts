import { Injectable } from '@angular/core';
import { initializeApp } from 'firebase/app';
import { getAuth, signInWithPopup, GoogleAuthProvider, signOut, User, createUserWithEmailAndPassword, signInWithEmailAndPassword, updateProfile } from 'firebase/auth';
import { environment } from '../../environments/environment';
import { BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private auth;
  private provider;
  
  public currentUserSubject = new BehaviorSubject<User | null>(null);

  public userRoleSubject = new BehaviorSubject<string | null>(localStorage.getItem('userRole'));

  constructor() {
    const app = initializeApp(environment.firebaseConfig);
    this.auth = getAuth(app);
    this.provider = new GoogleAuthProvider();

    this.auth.onAuthStateChanged((user) => {
      this.currentUserSubject.next(user);
    });
  }

  // 1. Logare cu Google
  async loginWithGoogle() {
    const result = await signInWithPopup(this.auth, this.provider);
    return result.user;
  }

  // 2. Înregistrare cu Email, Parolă și Nume
  async registerWithEmail(email: string, password: string, fullName: string) {
    const result = await createUserWithEmailAndPassword(this.auth, email, password);
    // Îi setăm numele în Firebase ca să îl putem afișa frumos mai târziu
    await updateProfile(result.user, { displayName: fullName });
    return result.user;
  }

  // 3. Logare cu Email și Parolă
  async loginWithEmail(email: string, password: string) {
    const result = await signInWithEmailAndPassword(this.auth, email, password);
    return result.user;
  }

  // 4. Deconectare
  async logout() {
    await signOut(this.auth);
  }
}