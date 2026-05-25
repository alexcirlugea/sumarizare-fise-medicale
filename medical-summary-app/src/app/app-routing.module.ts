import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { HomeComponent } from './home/home.component';
import { FileUploadComponent } from './file-upload/file-upload.component';
import { ChatComponent } from './chat/chat.component';
import { EhrListComponent } from './ehr-list/ehr-list.component';
import { LoginComponent } from './login/login.component';
import { AdminComponent } from './admin/admin.component';
import { DoctorDashboardComponent } from './doctor-dashboard/doctor-dashboard.component';

const routes: Routes = [
  { path: '', redirectTo: '/login', pathMatch: 'full' },
  { path: 'login', component: LoginComponent },
  { path: 'home', component: HomeComponent },
  { path: 'doctor-dashboard', component: DoctorDashboardComponent },
  { path: 'summary', component: FileUploadComponent },
  { path: 'chat', component: ChatComponent },
  { path: 'ehr', component: EhrListComponent },
  { path: 'admin', component: AdminComponent },
  { path: '**', redirectTo: '/login' }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }