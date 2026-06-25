import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { FileUploadComponent } from './file-upload/file-upload.component';
import { MarkdownModule } from 'ngx-markdown';
import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { HomeComponent } from './home/home.component';
import { ChatComponent } from './chat/chat.component';
import { EhrListComponent } from './ehr-list/ehr-list.component';
import { LoginComponent } from './login/login.component';
import { AdminComponent } from './admin/admin.component';
import { DoctorDashboardComponent } from './doctor-dashboard/doctor-dashboard.component';

@NgModule({
  declarations: [
    AppComponent,
    FileUploadComponent,
    HomeComponent,
    ChatComponent,
    EhrListComponent,
    LoginComponent,
    AdminComponent,
    DoctorDashboardComponent
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    FormsModule,
    MarkdownModule.forRoot()
  ],
  providers: [
    provideHttpClient(withInterceptorsFromDi())
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
