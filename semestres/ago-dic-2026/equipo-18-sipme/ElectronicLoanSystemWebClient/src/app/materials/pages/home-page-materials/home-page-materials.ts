import { Component, computed, inject, signal } from '@angular/core';
import { MaterialService } from '../../services/material.service';
import { rxResource } from '@angular/core/rxjs-interop';
import { LucidePencil, LucideTrash } from '@lucide/angular';
import { CreateMaterialForm } from '../../components/create-material-form/material-form';
import { Material } from '../../interfaces/material.interfaces';
import { HttpErrorResponse } from '@angular/common/http';
import { finalize } from 'rxjs';
import { RigthSlide } from '../../../shared/components/rigth-slide/rigth-slide';
import { LoadingPageService } from '../../../shared/services/loading-page.service';
import { Pagination } from '../../../shared/components/pagination/pagination';
import { PaginationService } from '../../../shared/services/pagination.service';
import { AuthService } from '../../../auth/services/auth.service';
import { Roles } from '../../../auth/utils/constants';

@Component({
  selector: 'home-page-materials',
  imports: [LucidePencil, LucideTrash, RigthSlide, CreateMaterialForm, Pagination],
  templateUrl: './home-page-materials.html',
})
export class HomePageMaterials {

  private materialService = inject(MaterialService)
  private loadingPageService = inject(LoadingPageService)
  private paginationService = inject(PaginationService)
  protected authService = inject(AuthService)

  public isStudent = computed(() => this.authService.role() === Roles.STUDENT)

  public showCreateMaterial = signal(false)
  public showEditMaterial = signal(false)
  public materialToEdit = signal<Material | null>(null)
  public errorMessage = signal<string | null>(null)

  public materialResource = rxResource({
    params: () => ({
      page: this.paginationService.page(),
      size: this.paginationService.perPage()
    }),
    stream: ({params}) => this.materialService.getAll(params)
  })

  public handlerEdit(material: Material){
    if (this.isStudent()) return;
    this.errorMessage.set(null)
    this.materialToEdit.set(material)
    this.showEditMaterial.set(true)
  }

  private onErrorHandler(err: HttpErrorResponse){
    const message = typeof err.error === 'string'
      ? err.error
      : err.error?.detail ?? err.error?.title

    this.errorMessage.set(message ?? 'No se pudo completar la operación. Inténtalo de nuevo.')
  }

  private onSuccessCreate(){
    if (this.paginationService.page() === 1) {
      this.materialResource.reload()
      return
    }

    this.paginationService.changePage(1)
  }

  private onSuccessEdit(){
    this.materialResource.reload()
  }

  public onEditMaterial(material: Material){
    if (this.isStudent()) return;
    this.errorMessage.set(null)
    this.loadingPageService.onLoading()
    this.materialService.edit(material, material.id)
    .pipe(
      finalize(() => {
        this.showEditMaterial.set(false)
        this.loadingPageService.offLoading()
      })
    )
    .subscribe({
      next: () => this.onSuccessEdit(),
      error: (err: HttpErrorResponse) => this.onErrorHandler(err) 
    })
  }

  public onCreateMaterial(material: Material){
    if (this.isStudent()) return;
    this.errorMessage.set(null)
    this.loadingPageService.onLoading()
    this.materialService.create(material)
    .pipe(
      finalize(() => {
        this.showCreateMaterial.set(false)
        this.loadingPageService.offLoading()
      })
    )
    .subscribe({
      next: () => this.onSuccessCreate(),
      error: (err: HttpErrorResponse) => this.onErrorHandler(err) 
    })
  }

}
