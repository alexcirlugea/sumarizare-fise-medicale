import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-ehr-list',
  standalone: false,
  templateUrl: './ehr-list.component.html',
  styleUrls: ['./ehr-list.component.css'] /* Atenție, aici e styleUrls cu 's' la final, spre deosebire de styleUrl */
})
export class EhrListComponent implements OnInit {
  // Aici sunt definite variabilele pe care nu le găsea HTML-ul:
  records: any[] = [];
  isLoading: boolean = true;

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.fetchEhrData();
  }

  fetchEhrData() {
    this.http.get<any[]>('http://localhost:8000/api/ehr')
      .subscribe({
        next: (data) => {
          this.records = data;
          this.isLoading = false;
        },
        error: (err) => {
          console.error('Eroare la preluarea datelor', err);
          this.isLoading = false;
        }
      });
  }
}