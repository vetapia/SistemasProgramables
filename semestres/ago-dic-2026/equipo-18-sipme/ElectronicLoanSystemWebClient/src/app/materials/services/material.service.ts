import { HttpClient } from '@angular/common/http';
import { inject, Service } from '@angular/core';
import { environment } from '../../../environments/environment.development';
import { Material, MaterialPaginationParams } from '../interfaces/material.interfaces';
import { PaginatedResponse } from '../../shared/interfaces/app.intefaces';
import { toHttpParams } from '../../shared/utils/http-params.utils';

const baseApi = environment.apiUrl

@Service()
export class MaterialService {

    private http = inject(HttpClient)

    public getAll(params: MaterialPaginationParams){
        return this.http.get<PaginatedResponse<Material>>(`${baseApi}/material`, {
            params: toHttpParams(params)
        })
    }

    public create(material: Material){
        return this.http.post<Material>(`${baseApi}/material`, material)
    }

    public edit(material: Material, id: number){
        return this.http.put<Material>(`${baseApi}/material/${id}`, material)
    }
}