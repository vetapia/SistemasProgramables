import { Component, inject } from '@angular/core';
import { MaterialInputFind } from '../../../materials/components/material-input-find/material-input-find';
import { Student } from '../../../students/interfaces/students.intefaces';
import { AuthService } from '../../../auth/services/auth.service';

@Component({
  selector: 'app-dash-board-page',
  imports: [],
  templateUrl: './dash-board-page.html',
})
export class DashBoardPage {

  protected authService = inject(AuthService)


}
