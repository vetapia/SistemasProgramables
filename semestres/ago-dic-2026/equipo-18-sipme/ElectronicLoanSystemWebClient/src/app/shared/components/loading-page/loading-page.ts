import { Component, inject } from '@angular/core';
import { LoadingPageService } from '../../services/loading-page.service';

@Component({
  selector: 'loading-page',
  imports: [],
  templateUrl: './loading-page.html',
})
export class LoadingPage {
  public loadingPageService = inject(LoadingPageService)
}
