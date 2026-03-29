import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { HomeComponent } from './home/home.component';
import { FileUploadComponent } from './file-upload/file-upload.component';
import { ChatComponent } from './chat/chat.component';
import { EhrListComponent } from './ehr-list/ehr-list.component';

const routes: Routes = [
  { path: '', component: HomeComponent }, // Pagina principală
  { path: 'summary', component: FileUploadComponent },
  { path: 'chat', component: ChatComponent },
  { path: 'ehr', component: EhrListComponent },
  { path: '**', redirectTo: '' } // Dacă introduce un URL greșit, îl trimite la home
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }