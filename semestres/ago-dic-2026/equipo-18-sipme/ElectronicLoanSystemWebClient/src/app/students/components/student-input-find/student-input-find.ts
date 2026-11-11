import {
  Component,
  inject,
  input,
  output,
  signal,
} from '@angular/core';
import { rxResource } from '@angular/core/rxjs-interop';
import { tap } from 'rxjs';
import { InputFind } from '../../../shared/components/input-find/input-find';
import { PaginationService } from '../../../shared/services/pagination.service';
import { Student } from '../../interfaces/students.intefaces';
import { StudentService } from '../../services/student.service';

@Component({
  selector: 'student-input-find',
  imports: [InputFind],
  templateUrl: './student-input-find.html',
  providers: [PaginationService],
})
export class StudentInputFind {
  private studentService = inject(StudentService);
  private paginationService = inject(PaginationService);

  protected studentSelected = signal<Student | null>(null);
  protected searchSubject = signal('');
  protected students = signal<Student[]>([]);

  public selectedAction = output<Student | null>();
  public label = input<string>('Estudiantes');
  public initialValue = input<Student | null>(null);
  public displayKey = input<keyof Student | null>(null);
  public displayFn = input<((student: Student) => string) | null>(null);

  protected studentsResource = rxResource({
    params: () => ({
      page: this.paginationService.page(),
      size: this.paginationService.perPage(),
      name: this.searchSubject(),
    }),
    stream: ({ params }) =>
      this.studentService.getAll(params).pipe(
        tap((response) => {
          if (this.paginationService.page() === 1) {
            this.students.set(response.items);
          } else {
            this.students.update((old) => [...old, ...response.items]);
          }
        })
      ),
  });

  ngOnInit() {
    if (this.initialValue()) {
      this.studentSelected.set(this.initialValue());
    }
  }

  public onFind(term: string) {
    this.paginationService.changePage(1);
    this.searchSubject.set(term);
  }

  public onLoadMore() {
    const hasNext = this.studentsResource.value()?.hasNext;
    const loading = this.studentsResource.isLoading();

    if (hasNext && !loading) {
      this.paginationService.nextPage();
    }
  }

  public onStudentSelected(student: Student) {
    this.studentSelected.set(student);
    this.selectedAction.emit(student);
  }

  protected getSelectedText() {
    const student = this.studentSelected();
    if (!student) return '';
    return this.getDisplayText(student);
  };

  protected getDisplayText = (student: Student) => {
    if (this.displayFn()) {
      return this.displayFn()!(student);
    }
    if (this.displayKey()) {
      return String(student[this.displayKey()!] ?? '');
    }
    if (student.user?.name) {
      return `${student.controlNumber} - ${student.user.name} ${student.user.lastName}`;
    }
    return student.controlNumber ?? '';
  };
}
