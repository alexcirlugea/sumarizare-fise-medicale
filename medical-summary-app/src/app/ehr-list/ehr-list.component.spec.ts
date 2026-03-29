import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';

import { EhrListComponent } from './ehr-list.component';

describe('EhrListComponent', () => {
  let component: EhrListComponent;
  let fixture: ComponentFixture<EhrListComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [EhrListComponent],
      imports: [HttpClientTestingModule] 
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(EhrListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});