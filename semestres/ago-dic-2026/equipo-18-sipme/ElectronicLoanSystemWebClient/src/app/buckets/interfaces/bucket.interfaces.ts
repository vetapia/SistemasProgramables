import { PaginationParams } from '../../shared/interfaces/app.intefaces';

export interface Bucket {
  id: number;
  bucketNumber: number;
  name: string;
}

export interface BucketRequest {
  id?: number;
  bucketNumber: number;
  name: string;
  materialIds?: number[];
}

export interface BucketPaginationParams extends PaginationParams {}

export interface BucketMaterialsRequest {
  materialIds: number[];
}
