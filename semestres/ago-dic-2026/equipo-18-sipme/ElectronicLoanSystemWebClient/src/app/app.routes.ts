import { Routes } from '@angular/router';
import { AuthenticatedGuard } from './auth/guards/authenticated.guard';

export const routes: Routes = [
    {
        path: "login",
        loadChildren: () => import("./auth/auth.routes")
    },
    {
        path: "panel",
        loadChildren: () => import("./dashboard/dashboard.routes"),
        canActivate: [AuthenticatedGuard]
    }
];
