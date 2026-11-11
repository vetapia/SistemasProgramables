import {
  Component,
  inject,
  input,
  OnInit,
  output,
  signal,
} from '@angular/core';
import { rxResource } from '@angular/core/rxjs-interop';
import { tap } from 'rxjs';
import { InputFind } from '../../../shared/components/input-find/input-find';
import { PaginationService } from '../../../shared/services/pagination.service';
import { Material } from '../../interfaces/material.interfaces';
import { MaterialService } from '../../services/material.service';

@Component({
  selector: 'material-input-find',
  imports: [InputFind],
  templateUrl: './material-input-find.html',
  providers: [PaginationService],
})
export class MaterialInputFind implements OnInit {
  private materialService = inject(MaterialService);
  private paginationService = inject(PaginationService);

  protected materialSelected = signal<Material | null>(null);
  protected searchSubject = signal('');
  protected materials = signal<Material[]>([]);

  public selectedAction = output<Material | null>();
  public label = input<string>('Materiales');
  public initialValue = input<Material | null>(null);
  public displayKey = input<keyof Material | null>(null);
  public displayFn = input<((material: Material) => string) | null>(null);
  public withoutBucket = input<boolean>(false);
  public clearOnSelect = input<boolean>(false);

  protected materialsResource = rxResource({
    params: () => ({
      page: this.paginationService.page(),
      size: this.paginationService.perPage(),
      name: this.searchSubject(),
      withoutBucket: this.withoutBucket() ? true : undefined,
    }),
    stream: ({ params }) =>
      this.materialService.getAll(params).pipe(
        tap((response) => {
          if (this.paginationService.page() === 1) {
            this.materials.set(response.items);
          } else {
            this.materials.update((old) => [...old, ...response.items]);
          }
        })
      ),
  });

  ngOnInit() {
    if (this.initialValue()) {
      this.materialSelected.set(this.initialValue());
    }
  }

  public onFind(term: string) {
    this.paginationService.changePage(1);
    this.searchSubject.set(term);
  }

  public onLoadMore() {
    const hasNext = this.materialsResource.value()?.hasNext;
    const loading = this.materialsResource.isLoading();

    if (hasNext && !loading) {
      this.paginationService.nextPage();
    }
  }

  public onMaterialSelected(material: Material) {
    if (this.clearOnSelect()) {
      this.materialSelected.set(null);
      this.searchSubject.set('');
      this.selectedAction.emit(material);
      return;
    }

    this.materialSelected.set(material);
    this.selectedAction.emit(material);
  }

  protected getSelectedText(): string {
    const material = this.materialSelected();
    if (!material) return '';
    return this.getDisplayText(material);
  }

  protected getDisplayText = (material: Material): string => {
    const customFn = this.displayFn();
    if (customFn) {
      return customFn(material);
    }
    const key = this.displayKey();
    if (key) {
      return String(material[key] ?? '');
    }
    if (material.materialUid && material.name) {
      return `${material.materialUid} - ${material.name}`;
    }
    return material.name ?? material.materialUid ?? '';
  };
}
