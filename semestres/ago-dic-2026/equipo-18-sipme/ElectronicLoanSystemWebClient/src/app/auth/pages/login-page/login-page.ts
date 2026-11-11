import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { AuthService } from '../../services/auth.service';
import { Router } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { FormUtils } from '../../../shared/utils/form.utils';

@Component({
  selector: 'login-page',
  imports: [ReactiveFormsModule],
  templateUrl: './login-page.html',
})
export class LoginPage {

  private fb = inject(FormBuilder)
  private authService = inject(AuthService)
  private router = inject(Router)
  public formUtils = FormUtils

  authForm = this.fb.group({
    email: ["", [Validators.required, Validators.email]],
    password: ["", [Validators.required]]
  })

  private manageLoginError(error: HttpErrorResponse){
    if ([401, 403, 422].includes(error.status)) {
      console.log(error)
    }
  }

  onLogin(){
    if(this.authForm.valid){

      const {email, password} = this.authForm.value
      this.authService.login(email!, password!)
      .subscribe({
        next: () => this.router.navigateByUrl("/panel"),
        error: (err: HttpErrorResponse) => this.manageLoginError(err)
      })
    }
  }

}
