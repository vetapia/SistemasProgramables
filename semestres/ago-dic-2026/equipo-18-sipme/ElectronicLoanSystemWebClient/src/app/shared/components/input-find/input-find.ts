import { ChangeDetectionStrategy, Component, input, output, signal } from '@angular/core';

@Component({
  selector: 'app-input-find',
  imports: [],
  templateUrl: './input-find.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class InputFind<T extends { id: number | string }> {

  showData = signal(false)
  textLabel = input.required<string>()

  results = input.required<T[]>()
  displayKey = input<keyof T>()
  displayFn = input<((item: T) => string) | null>(null)
  isLoading = input.required<boolean>()
  selectedValue = input.required<string>()

  loadMore = output<void>()
  selected = output<T>()
  find = output<string>()

  getLabel(item: T) {
    const fn = this.displayFn()
    if (fn) return fn(item)
    const key = this.displayKey()
    if (key) return String(item[key] ?? '')
    return ''
  }

  onSelect(selected: T){
    this.showData.set(false)
    this.selected.emit(selected)
  }

  onScroll(event: Event) {
    const element = event.target as HTMLElement
    const scrollTop = element.scrollTop
    const scrollHeight = element.scrollHeight
    const clientHeight = element.clientHeight

    const scrollBottom = scrollHeight - (scrollTop + clientHeight)

    const threshold = 30

    if (scrollBottom <= threshold) {
      this.loadMore.emit()
    }
  }

}
