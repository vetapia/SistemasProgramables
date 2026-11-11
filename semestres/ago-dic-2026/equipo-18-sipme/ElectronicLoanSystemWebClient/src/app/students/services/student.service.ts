import { HttpClient } from '@angular/common/http';
import { inject, Service } from '@angular/core';
import { environment } from '../../../environments/environment.development';
import { PaginatedResponse } from '../../shared/interfaces/app.intefaces';
import { Student, StudentPaginationParams, StudentRequest } from '../interfaces/students.intefaces';
import { toHttpParams } from '../../shared/utils/http-params.utils';

const baseApi = environment.apiUrl;

@Service()
export class StudentService {
  private http = inject(HttpClient);

  public getAll(params: StudentPaginationParams) {
    return this.http.get<PaginatedResponse<Student>>(`${baseApi}/students`, {
      params: toHttpParams(params),
    });
  }

  public create(studentRequest: StudentRequest) {
    return this.http.post<Student>(`${baseApi}/students`, studentRequest);
  }

  public edit(studentRequest: StudentRequest, id: number) {
    return this.http.put<Student>(`${baseApi}/students/${id}`, studentRequest);
  }
}
