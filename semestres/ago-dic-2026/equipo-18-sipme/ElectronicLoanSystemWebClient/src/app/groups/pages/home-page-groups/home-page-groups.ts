import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { rxResource } from '@angular/core/rxjs-interop';
import { LucidePencil } from '@lucide/angular';
import { finalize } from 'rxjs';
import { LoadingPageService } from '../../../shared/services/loading-page.service';
import { RigthSlide } from '../../../shared/components/rigth-slide/rigth-slide';
import { Pagination } from '../../../shared/components/pagination/pagination';
import { PaginationService } from '../../../shared/services/pagination.service';
import { GroupForm } from '../../components/group-form/group-form';
import { Group } from '../../interfaces/grups.interfaces';
import { GroupService } from '../../services/group.service';

@Component({
  selector: 'home-page-groups',
  imports: [LucidePencil, RigthSlide, GroupForm, Pagination],
  templateUrl: './home-page-groups.html',
})
export class HomePageGroups {

  private groupService = inject(GroupService)
  private loadingPageService = inject(LoadingPageService)
  private paginationService = inject(PaginationService)

  public showCreateGroup = signal(false)
  public showEditGroup = signal(false)
  public groupToEdit = signal<Group | null>(null)
  public errorMessage = signal<string | null>(null)

  public groupResource = rxResource({
    params: () => ({
      page: this.paginationService.page(),
      size: this.paginationService.perPage()
    }),
    stream: ({params}) => this.groupService.getAll(params)
  })

  public openCreateGroup(){
    this.errorMessage.set(null)
    this.groupToEdit.set(null)
    this.showCreateGroup.set(true)
  }

  public handlerEdit(group: Group){
    this.errorMessage.set(null)
    this.groupToEdit.set(group)
    this.showEditGroup.set(true)
  }

  private onErrorHandler(err: HttpErrorResponse){
    const message = typeof err.error === 'string'
      ? err.error
      : err.error?.detail ?? err.error?.title

    this.errorMessage.set(message ?? 'No se pudo guardar el grupo. Inténtalo de nuevo.')
  }

  private onSuccessCreate(){
    if (this.paginationService.page() === 1) {
      this.groupResource.reload()
      return
    }

    this.paginationService.changePage(1)
  }

  private onSuccessEdit(){
    this.groupResource.reload()
  }

  public onCreateGroup(group: Group){
    this.errorMessage.set(null)
    this.loadingPageService.onLoading()

    this.groupService.create(group)
    .pipe(
      finalize(() => {
        this.showCreateGroup.set(false)
        this.loadingPageService.offLoading()
      })
    )
    .subscribe({
      next: () => this.onSuccessCreate(),
      error: (err: HttpErrorResponse) => this.onErrorHandler(err)
    })
  }

  public onEditGroup(group: Group){
    this.errorMessage.set(null)
    this.loadingPageService.onLoading()

    this.groupService.edit(group, group.id)
    .pipe(
      finalize(() => {
        this.showEditGroup.set(false)
        this.loadingPageService.offLoading()
      })
    )
    .subscribe({
      next: () => this.onSuccessEdit(),
      error: (err: HttpErrorResponse) => this.onErrorHandler(err)
    })
  }
}
