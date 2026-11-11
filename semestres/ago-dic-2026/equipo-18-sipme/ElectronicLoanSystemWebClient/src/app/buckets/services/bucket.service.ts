import { HttpClient } from '@angular/common/http';
import { inject, Service } from '@angular/core';
import { environment } from '../../../environments/environment.development';
import { PaginatedResponse, PaginationParams } from '../../shared/interfaces/app.intefaces';
import { toHttpParams } from '../../shared/utils/http-params.utils';
import { Material } from '../../materials/interfaces/material.interfaces';
import {
  Bucket,
  BucketMaterialsRequest,
  BucketPaginationParams,
  BucketRequest,
} from '../interfaces/bucket.interfaces';

const baseApi = environment.apiUrl;

@Service()
export class BucketService {
  private http = inject(HttpClient);

  public getAll(params: BucketPaginationParams) {
    return this.http.get<PaginatedResponse<Bucket>>(`${baseApi}/bucket`, {
      params: toHttpParams(params),
    });
  }

  public get(id: number) {
    return this.http.get<Bucket>(`${baseApi}/bucket/${id}`);
  }

  public create(bucket: BucketRequest) {
    return this.http.post<Bucket>(`${baseApi}/bucket`, bucket);
  }

  public edit(bucket: BucketRequest, id: number) {
    return this.http.put<Bucket>(`${baseApi}/bucket/${id}`, bucket);
  }

  public delete(id: number) {
    return this.http.delete<void>(`${baseApi}/bucket/${id}`);
  }

  public getMaterials(bucketId: number, params: PaginationParams) {
    return this.http.get<PaginatedResponse<Material>>(
      `${baseApi}/bucket/${bucketId}/materials`,
      {
        params: toHttpParams(params),
      }
    );
  }

  public addMaterials(bucketId: number, materialIds: number[]) {
    const payload: BucketMaterialsRequest = { materialIds };
    return this.http.post<void>(
      `${baseApi}/bucket/${bucketId}/materials/add`,
      payload
    );
  }

  public removeMaterials(bucketId: number, materialIds: number[]) {
    const payload: BucketMaterialsRequest = { materialIds };
    return this.http.post<void>(
      `${baseApi}/bucket/${bucketId}/materials/remove`,
      payload
    );
  }
}
