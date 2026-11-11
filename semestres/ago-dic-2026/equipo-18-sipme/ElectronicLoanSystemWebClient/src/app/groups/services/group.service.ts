import { HttpClient } from '@angular/common/http';
import { inject, Service } from '@angular/core';
import { environment } from '../../../environments/environment.development';
import { PaginatedResponse, PaginationParams } from '../../shared/interfaces/app.intefaces';
import { Group, GroupPaginationParams } from '../interfaces/grups.interfaces';
import { toHttpParams } from '../../shared/utils/http-params.utils';

const baseApi = environment.apiUrl

@Service()
export class GroupService {

    private http = inject(HttpClient)

    public getAll(params: GroupPaginationParams){
        return this.http.get<PaginatedResponse<Group>>(`${baseApi}/group`, {
            params: toHttpParams(params)
        })
    }

    public create(group: Group){
        return this.http.post<Group>(`${baseApi}/group`, group)
    }

    public edit(group: Group, id: number){
        return this.http.put<Group>(`${baseApi}/group/${id}`, group)
    }
}
