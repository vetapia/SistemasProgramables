import type { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from '../services/auth.service';
import { unAddUrls } from '../utils/constants';

export const AuthInterceptor: HttpInterceptorFn = (req, next) => {

  const authService = inject(AuthService)
  const token = authService.token()

  const unNeedToken = unAddUrls.some(url => url == req.url)

  if(!unNeedToken){
    const newReq = req.clone({
      headers: req.headers.append("Authorization", `Bearer ${token}`)
    })

    return next(newReq)
  }

  return next(req);
};
