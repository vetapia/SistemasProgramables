import { Component, computed, inject, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { rxResource } from '@angular/core/rxjs-interop';
import { HttpErrorResponse } from '@angular/common/http';
import { finalize } from 'rxjs';
import { LoanService } from '../../services/loan.service';
import { LoanRequest, LoanStatusTab } from '../../interfaces/loan.interfaces';
import { LoadingPageService } from '../../../shared/services/loading-page.service';
import { PaginationService } from '../../../shared/services/pagination.service';
import { Pagination } from '../../../shared/components/pagination/pagination';
import { RigthSlide } from '../../../shared/components/rigth-slide/rigth-slide';
import { LoanForm } from '../../components/loan-form/loan-form';
import { AuthService } from '../../../auth/services/auth.service';
import { Roles } from '../../../auth/utils/constants';

@Component({
  selector: 'home-page-loans',
  imports: [DatePipe, Pagination, RigthSlide, LoanForm],
  templateUrl: './home-page-loans.html',
})
export class HomePageLoans {
  private loanService = inject(LoanService);
  private loadingPageService = inject(LoadingPageService);
  private paginationService = inject(PaginationService);
  protected authService = inject(AuthService);

  public isStudent = computed(() => this.authService.role() === Roles.STUDENT);

  public currentStatus = signal<LoanStatusTab>('active');
  public showCreateLoan = signal(false);
  public errorMessage = signal<string | null>(null);

  public loansResource = rxResource({
    params: () => ({
      page: this.paginationService.page(),
      size: this.paginationService.perPage(),
      status: this.currentStatus() === 'all' ? undefined : this.currentStatus(),
    }),
    stream: ({ params }) => this.loanService.getAll(params),
  });

  public onChangeStatus(status: LoanStatusTab) {
    this.errorMessage.set(null);
    this.currentStatus.set(status);
    this.paginationService.changePage(1);
  }

  private onErrorHandler(err: HttpErrorResponse) {
    const message =
      typeof err.error === 'string'
        ? err.error
        : err.error?.detail ?? err.error?.title;

    this.errorMessage.set(
      message ?? 'No se pudo completar la operación. Inténtalo de nuevo.'
    );
  }

  private onSuccessCreate() {
    if (this.paginationService.page() === 1) {
      this.loansResource.reload();
      return;
    }
    this.paginationService.changePage(1);
  }

  public onCreateLoan(loanRequest: LoanRequest) {
    if (this.isStudent()) return;
    this.errorMessage.set(null);
    this.loadingPageService.onLoading();
    this.loanService
      .create(loanRequest)
      .pipe(
        finalize(() => {
          this.showCreateLoan.set(false);
          this.loadingPageService.offLoading();
        })
      )
      .subscribe({
        next: () => this.onSuccessCreate(),
        error: (err: HttpErrorResponse) => this.onErrorHandler(err),
      });
  }

  public onReturnLoan(loanId: number) {
    if (this.isStudent()) return;
    this.errorMessage.set(null);
    this.loadingPageService.onLoading();
    this.loanService
      .endLoan(loanId)
      .pipe(
        finalize(() => {
          this.loadingPageService.offLoading();
        })
      )
      .subscribe({
        next: () => this.loansResource.reload(),
        error: (err: HttpErrorResponse) => this.onErrorHandler(err),
      });
  }
}
