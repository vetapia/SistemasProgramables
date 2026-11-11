import { Service, signal } from '@angular/core';

@Service()
export class PaginationService {

  private _page = signal(1)
  private _perPage = signal(15)

  public page = this._page.asReadonly()
  public perPage = this._perPage.asReadonly()

  public nextPage(){
    this._page.update(old => old + 1)
  }

  public prevPage(){
    this._page.update(old => Math.max(1, old - 1))
  }

  public changePage(page: number){
    this._page.set(Math.max(1, page))
  }

}
