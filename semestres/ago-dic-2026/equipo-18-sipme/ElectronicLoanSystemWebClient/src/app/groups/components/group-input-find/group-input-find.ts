import {
  Component,
  inject,
  input,
  output,
  signal,
} from '@angular/core';
import { InputFind } from '../../../shared/components/input-find/input-find';
import { Group } from '../../interfaces/grups.interfaces';
import { GroupService } from '../../services/group.service';
import { PaginationService } from '../../../shared/services/pagination.service';
import { rxResource } from '@angular/core/rxjs-interop';
import { tap } from 'rxjs';

@Component({
  selector: 'group-input-find',
  imports: [InputFind],
  templateUrl: './group-input-find.html',
  providers: [PaginationService]
})
export class GroupInputFind {
  private groupService = inject(GroupService);
  private paginationService = inject(PaginationService) 

  protected groupSelected = signal<Group | null>(null) 
  protected searchSubject = signal("");
  protected groups = signal<Group[]>([])

  public selectedAction = output<Group | null>();
  public label = input<string>('Grupos');
  public initialValue = input<Group | null>(null)

  protected studentsResource = rxResource({
    params: () => ({
      page: this.paginationService.page(),
      size: this.paginationService.perPage(),
      name: this.searchSubject()
    }),
    stream: ({params}) => this.groupService
      .getAll(params)
      .pipe(
        tap(response => {
          if(this.paginationService.page() == 1){
            this.groups.set(response.items)
          }else{
            this.groups.update(old => [...old, ...response.items])
          }
        })
      )
  })

  ngOnInit() {
    if(this.initialValue()){
      this.groupSelected.set(this.initialValue())
    }
  }

  public onFind(term: string) {
    this.paginationService.changePage(1)
    this.searchSubject.set(term)
  }

  public onLoadMore() {
    const hasNext = this.studentsResource.value()?.hasNext
    const loading = this.studentsResource.isLoading()

    if(hasNext && !loading){
      this.paginationService.nextPage()
    }

  }

  public onGroupSelected(group: Group) {
    this.groupSelected.set(group)
    this.selectedAction.emit(group)
  }

}
