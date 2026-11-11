import { Routes } from '@angular/router';
import { HomePageLoans } from './pages/home-page-loans/home-page-loans';
import { PaginationService } from '../shared/services/pagination.service';

const routes: Routes = [
  {
    path: '',
    component: HomePageLoans,
    providers: [PaginationService],
  },
];

export default routes;
