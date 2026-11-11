import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { rxResource } from '@angular/core/rxjs-interop';
import { LucidePencil, LucideTrash, LucidePackage } from '@lucide/angular';
import { finalize } from 'rxjs';
import { LoadingPageService } from '../../../shared/services/loading-page.service';
import { RigthSlide } from '../../../shared/components/rigth-slide/rigth-slide';
import { Pagination } from '../../../shared/components/pagination/pagination';
import { PaginationService } from '../../../shared/services/pagination.service';
import { BucketForm } from '../../components/bucket-form/bucket-form';
import { BucketMaterialsManager } from '../../components/bucket-materials-manager/bucket-materials-manager';
import { Bucket, BucketRequest } from '../../interfaces/bucket.interfaces';
import { BucketService } from '../../services/bucket.service';

@Component({
  selector: 'home-page-buckets',
  imports: [
    LucidePencil,
    LucideTrash,
    LucidePackage,
    RigthSlide,
    BucketForm,
    BucketMaterialsManager,
    Pagination,
  ],
  templateUrl: './home-page-buckets.html',
})
export class HomePageBuckets {
  private bucketService = inject(BucketService);
  private loadingPageService = inject(LoadingPageService);
  private paginationService = inject(PaginationService);

  public showCreateBucket = signal(false);
  public showEditBucket = signal(false);
  public showMaterialsBucket = signal(false);

  public bucketToEdit = signal<Bucket | null>(null);
  public bucketToManage = signal<Bucket | null>(null);
  public errorMessage = signal<string | null>(null);

  public bucketResource = rxResource({
    params: () => ({
      page: this.paginationService.page(),
      size: this.paginationService.perPage(),
    }),
    stream: ({ params }) => this.bucketService.getAll(params),
  });

  public openCreateBucket() {
    this.errorMessage.set(null);
    this.bucketToEdit.set(null);
    this.showCreateBucket.set(true);
  }

  public handlerEdit(bucket: Bucket) {
    this.errorMessage.set(null);
    this.bucketToEdit.set(bucket);
    this.showEditBucket.set(true);
  }

  public handlerManageMaterials(bucket: Bucket) {
    this.errorMessage.set(null);
    this.bucketToManage.set(bucket);
    this.showMaterialsBucket.set(true);
  }

  public handlerDelete(bucket: Bucket) {
    const confirmed = confirm(
      `¿Estás seguro de que deseas eliminar el cajón #${bucket.bucketNumber} (${bucket.name})?`
    );
    if (!confirmed) return;

    this.errorMessage.set(null);
    this.loadingPageService.onLoading();

    this.bucketService
      .delete(bucket.id)
      .pipe(finalize(() => this.loadingPageService.offLoading()))
      .subscribe({
        next: () => this.bucketResource.reload(),
        error: (err: HttpErrorResponse) => this.onErrorHandler(err),
      });
  }

  private onErrorHandler(err: HttpErrorResponse) {
    const message =
      typeof err.error === 'string'
        ? err.error
        : err.error?.detail ?? err.error?.title;

    this.errorMessage.set(
      message ?? 'Ocurrió un error al procesar la solicitud. Inténtalo de nuevo.'
    );
  }

  private onSuccessCreate() {
    if (this.paginationService.page() === 1) {
      this.bucketResource.reload();
      return;
    }
    this.paginationService.changePage(1);
  }

  private onSuccessEdit() {
    this.bucketResource.reload();
  }

  public onCreateBucket(request: BucketRequest) {
    this.errorMessage.set(null);
    this.loadingPageService.onLoading();

    this.bucketService
      .create(request)
      .pipe(
        finalize(() => {
          this.showCreateBucket.set(false);
          this.loadingPageService.offLoading();
        })
      )
      .subscribe({
        next: () => this.onSuccessCreate(),
        error: (err: HttpErrorResponse) => this.onErrorHandler(err),
      });
  }

  public onEditBucket(request: BucketRequest) {
    this.errorMessage.set(null);
    this.loadingPageService.onLoading();

    this.bucketService
      .edit(request, request.id ?? 0)
      .pipe(
        finalize(() => {
          this.showEditBucket.set(false);
          this.loadingPageService.offLoading();
        })
      )
      .subscribe({
        next: () => this.onSuccessEdit(),
        error: (err: HttpErrorResponse) => this.onErrorHandler(err),
      });
  }
}
