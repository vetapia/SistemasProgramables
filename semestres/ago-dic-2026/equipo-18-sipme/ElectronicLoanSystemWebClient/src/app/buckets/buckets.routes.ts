import { Routes } from '@angular/router';
import { HomePageBuckets } from './pages/home-page-buckets/home-page-buckets';
import { PaginationService } from '../shared/services/pagination.service';
import { BucketService } from './services/bucket.service';
import { MaterialService } from '../materials/services/material.service';

const routes: Routes = [
  {
    path: '',
    component: HomePageBuckets,
    providers: [PaginationService, BucketService, MaterialService],
  },
];

export default routes;
