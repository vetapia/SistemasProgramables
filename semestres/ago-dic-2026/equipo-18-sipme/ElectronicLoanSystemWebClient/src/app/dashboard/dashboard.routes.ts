import { Routes } from '@angular/router';
import { DashboardLayout } from './layouts/dashboard-layout/dashboard-layout';
import { DashBoardPage } from './pgaes/dash-board-page/dash-board-page';
import { roleManagerGuard } from '../auth/guards/role-manager-guard';
import { Role } from '../shared/interfaces/app.intefaces';
import { Roles } from '../auth/utils/constants';

const routes: Routes = [
  {
    path: '',
    component: DashboardLayout,
    children: [
      {
        path: '',
        component: DashBoardPage,
      },
      {
        path: "grupos",
        loadChildren: () => import("../groups/groups.routes"),
        canMatch: [roleManagerGuard],
        data: {
          roles: [Roles.ADMIN]
        }
      },
      {
        path: "materiales",
        loadChildren: () => import("../materials/materials.routes"),
        canMatch: [roleManagerGuard],
        data: {
          roles: [Roles.ADMIN, Roles.STUDENT]
        }
      },
      {
        path: "estudiantes",
        loadChildren: () => import("../students/students.routes"),
        canMatch: [roleManagerGuard],
        data: {
          roles: [Roles.ADMIN]
        }
      },
      {
        path: "prestamos",
        loadChildren: () => import("../loans/loans.routes"),
        canMatch: [roleManagerGuard],
        data: {
          roles: [Roles.ADMIN, Roles.STUDENT]
        }
      },
      {
        path: "cajones",
        loadChildren: () => import("../buckets/buckets.routes"),
        canMatch: [roleManagerGuard],
        data: {
          roles: [Roles.ADMIN]
        }
      },
      {
        path: '**',
        redirectTo: '/panel',
      },
    ],
  },
];

export default routes;
