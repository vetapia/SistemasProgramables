import { inject } from '@angular/core';
import { Router, type CanMatchFn } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { Role } from '../../shared/interfaces/app.intefaces';
import { verifyContainRole } from '../utils/utils';

export const roleManagerGuard: CanMatchFn = async (route, segments) => {

  const authService = inject(AuthService)
  const router = inject(Router)

  const expectedRoles: Role[] = route.data ? route.data["roles"] : []
  const containRole = verifyContainRole(expectedRoles, authService.role() ?? "Student")

  if(!containRole){

    if (router.navigated) {
      return false
    }

    return router.createUrlTree(["/"])
  }

  return true;
};
