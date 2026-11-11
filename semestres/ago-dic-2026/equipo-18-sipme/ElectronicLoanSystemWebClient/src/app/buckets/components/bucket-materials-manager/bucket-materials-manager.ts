import {
  Component,
  inject,
  input,
  OnInit,
  output,
  signal,
} from '@angular/core';
import { rxResource } from '@angular/core/rxjs-interop';
import { LucideTrash2, LucidePlus, LucideX } from '@lucide/angular';
import { finalize } from 'rxjs';
import { PaginationService } from '../../../shared/services/pagination.service';
import { Pagination } from '../../../shared/components/pagination/pagination';
import { MaterialInputFind } from '../../../materials/components/material-input-find/material-input-find';
import { Material } from '../../../materials/interfaces/material.interfaces';
import { Bucket } from '../../interfaces/bucket.interfaces';
import { BucketService } from '../../services/bucket.service';

@Component({
  selector: 'bucket-materials-manager',
  imports: [MaterialInputFind, Pagination, LucideTrash2, LucidePlus, LucideX],
  templateUrl: './bucket-materials-manager.html',
  providers: [PaginationService],
})
export class BucketMaterialsManager implements OnInit {
  private bucketService = inject(BucketService);
  protected paginationService = inject(PaginationService);

  public bucket = input.required<Bucket>();
  public updatedAction = output<void>();

  public isBusy = signal(false);
  public errorMessage = signal<string | null>(null);
  public selectedToRemove = signal<number[]>([]);
  public pendingToAdd = signal<Material[]>([]);

  public materialsResource = rxResource({
    params: () => ({
      bucketId: this.bucket().id,
      page: this.paginationService.page(),
      size: this.paginationService.perPage(),
    }),
    stream: ({ params }) =>
      this.bucketService.getMaterials(params.bucketId, {
        page: params.page,
        size: params.size,
      }),
  });

  ngOnInit() {
    this.paginationService.changePage(1);
  }

  public onMaterialSelectedToAdd(material: Material | null) {
    if (!material) return;
    const exists = this.pendingToAdd().some((m) => m.id === material.id);
    if (!exists) {
      this.pendingToAdd.update((list) => [...list, material]);
    }
  }

  public removePendingToAdd(materialId: number) {
    this.pendingToAdd.update((list) => list.filter((m) => m.id !== materialId));
  }

  public toggleSelectToRemove(materialId: number) {
    this.selectedToRemove.update((list) =>
      list.includes(materialId)
        ? list.filter((id) => id !== materialId)
        : [...list, materialId]
    );
  }

  public toggleSelectAllCurrent() {
    const currentItems = this.materialsResource.value()?.items ?? [];
    const allSelected = currentItems.every((item) =>
      this.selectedToRemove().includes(item.id)
    );

    if (allSelected) {
      const currentIds = new Set(currentItems.map((m) => m.id));
      this.selectedToRemove.update((list) =>
        list.filter((id) => !currentIds.has(id))
      );
    } else {
      const newIds = currentItems.map((m) => m.id);
      this.selectedToRemove.update((list) => [
        ...new Set([...list, ...newIds]),
      ]);
    }
  }

  public onAddMaterials() {
    const ids = this.pendingToAdd().map((m) => m.id);
    if (ids.length === 0) return;

    this.isBusy.set(true);
    this.errorMessage.set(null);

    this.bucketService
      .addMaterials(this.bucket().id, ids)
      .pipe(finalize(() => this.isBusy.set(false)))
      .subscribe({
        next: () => {
          this.pendingToAdd.set([]);
          this.materialsResource.reload();
          this.updatedAction.emit();
        },
        error: (err) => {
          const message =
            typeof err.error === 'string'
              ? err.error
              : err.error?.detail ?? err.error?.title;
          this.errorMessage.set(message ?? 'Error al agregar materiales.');
        },
      });
  }

  public onRemoveSelectedMaterials() {
    const ids = this.selectedToRemove();
    if (ids.length === 0) return;

    this.isBusy.set(true);
    this.errorMessage.set(null);

    this.bucketService
      .removeMaterials(this.bucket().id, ids)
      .pipe(finalize(() => this.isBusy.set(false)))
      .subscribe({
        next: () => {
          this.selectedToRemove.set([]);
          this.materialsResource.reload();
          this.updatedAction.emit();
        },
        error: (err) => {
          const message =
            typeof err.error === 'string'
              ? err.error
              : err.error?.detail ?? err.error?.title;
          this.errorMessage.set(message ?? 'Error al desvincular materiales.');
        },
      });
  }

  public onRemoveSingleMaterial(materialId: number) {
    this.isBusy.set(true);
    this.errorMessage.set(null);

    this.bucketService
      .removeMaterials(this.bucket().id, [materialId])
      .pipe(finalize(() => this.isBusy.set(false)))
      .subscribe({
        next: () => {
          this.selectedToRemove.update((list) =>
            list.filter((id) => id !== materialId)
          );
          this.materialsResource.reload();
          this.updatedAction.emit();
        },
        error: (err) => {
          const message =
            typeof err.error === 'string'
              ? err.error
              : err.error?.detail ?? err.error?.title;
          this.errorMessage.set(message ?? 'Error al desvincular material.');
        },
      });
  }
}
