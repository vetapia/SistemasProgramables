import { ChangeDetectionStrategy, Component, computed, inject, input } from '@angular/core';
import { PaginationService } from '../../services/pagination.service';
import { PaginatedResponse } from '../../interfaces/app.intefaces';

@Component({
  selector: 'pagination',
  imports: [],
  templateUrl: './pagination.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Pagination<T> {

  public itemsPagination = input.required<PaginatedResponse<T>>()
  public isLoading = input(false)
  private paginationService = inject(PaginationService)

  protected hasNext = computed(() => this.itemsPagination().hasNext)
  protected hasPrev = computed(() => this.itemsPagination().hasPrevious)

  public onPrevPage(){
    if (!this.isLoading() && this.itemsPagination().hasPrevious) {
      this.paginationService.prevPage()
    }
  }

  public onNextPage(){
    if (!this.isLoading() && this.itemsPagination().hasNext) {
      this.paginationService.nextPage()
    }
  }
}
