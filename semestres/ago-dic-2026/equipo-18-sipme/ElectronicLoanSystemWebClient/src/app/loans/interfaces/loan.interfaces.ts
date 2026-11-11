import { PaginationParams, User } from '../../shared/interfaces/app.intefaces';
import { Material } from '../../materials/interfaces/material.interfaces';

export interface Loan {
  id: number;
  startDate: string;
  endDate: string | null;
  material: Material;
  user: User;
}

export interface LoanRequest {
  materialId: number;
  userId: string;
}

export type LoanStatusTab = 'all' | 'active' | 'finished';

export interface LoanPaginationParams extends PaginationParams {
  status?: string;
}
