import { inject } from '@angular/core';
import { Router, type CanMatchFn, type Route, type UrlSegment } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { firstValueFrom } from 'rxjs';

export const AuthenticatedGuard: CanMatchFn = async (
  route: Route, 
  state: UrlSegment[]
) => {

  const authService = inject(AuthService)
  const router = inject(Router)
  const isAuthenticated = await firstValueFrom(authService.checkStatus())

  if(!isAuthenticated){
    return router.createUrlTree(["/login"])
  }

  return true;

};
