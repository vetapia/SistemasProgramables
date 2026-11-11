import { HttpClient } from '@angular/common/http';
import { inject, Service } from '@angular/core';
import { environment } from '../../../environments/environment.development';
import { PaginatedResponse } from '../../shared/interfaces/app.intefaces';
import { Loan, LoanPaginationParams, LoanRequest } from '../interfaces/loan.interfaces';
import { toHttpParams } from '../../shared/utils/http-params.utils';

const baseApi = environment.apiUrl;

@Service()
export class LoanService {
  private http = inject(HttpClient);

  public getAll(params: LoanPaginationParams) {
    return this.http.get<PaginatedResponse<Loan>>(`${baseApi}/loans`, {
      params: toHttpParams(params),
    });
  }

  public get(id: number) {
    return this.http.get<Loan>(`${baseApi}/loans/${id}`);
  }

  public create(loanRequest: LoanRequest) {
    return this.http.post<Loan>(`${baseApi}/loans`, loanRequest);
  }

  public endLoan(id: number) {
    return this.http.patch<Loan>(`${baseApi}/loans/${id}`, {});
  }
}
