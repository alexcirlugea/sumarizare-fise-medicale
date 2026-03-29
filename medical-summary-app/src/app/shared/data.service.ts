import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root' 
})
export class DataService {
  originalText: string = '';
  summary: string = '';

  constructor() { }

  saveSummaryData(original: string, summary: string) {
    this.originalText = original;
    this.summary = summary;
  }

  clearData() {
    this.originalText = '';
    this.summary = '';
  }
}