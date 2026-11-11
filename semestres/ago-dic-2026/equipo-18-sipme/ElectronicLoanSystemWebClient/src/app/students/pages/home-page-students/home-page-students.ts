import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { rxResource } from '@angular/core/rxjs-interop';
import { LucidePencil } from '@lucide/angular';
import { finalize } from 'rxjs';
import { LoadingPageService } from '../../../shared/services/loading-page.service';
import { RigthSlide } from '../../../shared/components/rigth-slide/rigth-slide';
import { Pagination } from '../../../shared/components/pagination/pagination';
import { PaginationService } from '../../../shared/services/pagination.service';
import { StudentForm } from '../../components/student-form/student-form';
import { Student, StudentRequest } from '../../interfaces/students.intefaces';
import { StudentService } from '../../services/student.service';

@Component({
  selector: 'home-page-students',
  imports: [LucidePencil, RigthSlide, StudentForm, Pagination],
  templateUrl: './home-page-students.html',
})
export class HomePageStudents {
  private studentService = inject(StudentService);
  private loadingPageService = inject(LoadingPageService);
  private paginationService = inject(PaginationService);

  public showCreateStudent = signal(false);
  public showEditStudent = signal(false);
  public studentToEdit = signal<Student | null>(null);
  public errorMessage = signal<string | null>(null);

  public studentsResource = rxResource({
    params: () => ({
      page: this.paginationService.page(),
      size: this.paginationService.perPage(),
    }),
    stream: ({ params }) => this.studentService.getAll(params),
  });

  public openCreateStudent() {
    this.errorMessage.set(null);
    this.studentToEdit.set(null);
    this.showCreateStudent.set(true);
  }

  public handlerEdit(student: Student) {
    this.errorMessage.set(null);
    this.studentToEdit.set(student);
    this.showEditStudent.set(true);
  }

  private onErrorHandler(err: HttpErrorResponse) {
    const message =
      typeof err.error === 'string'
        ? err.error
        : err.error?.detail ?? err.error?.title;

    this.errorMessage.set(message ?? 'No se pudo guardar el estudiante. Inténtalo de nuevo.');
  }

  private onSuccessCreate() {
    if (this.paginationService.page() === 1) {
      this.studentsResource.reload();
      return;
    }

    this.paginationService.changePage(1);
  }

  private onSuccessEdit() {
    this.studentsResource.reload();
  }

  public onCreateStudent(studentRequest: StudentRequest) {
    this.errorMessage.set(null);
    this.loadingPageService.onLoading();

    this.studentService
      .create(studentRequest)
      .pipe(
        finalize(() => {
          this.showCreateStudent.set(false);
          this.loadingPageService.offLoading();
        })
      )
      .subscribe({
        next: () => this.onSuccessCreate(),
        error: (err: HttpErrorResponse) => this.onErrorHandler(err),
      });
  }

  public onEditStudent(studentRequest: StudentRequest) {
    const id = this.studentToEdit()?.id;
    if (!id) return;

    this.errorMessage.set(null);
    this.loadingPageService.onLoading();

    this.studentService
      .edit(studentRequest, id)
      .pipe(
        finalize(() => {
          this.showEditStudent.set(false);
          this.loadingPageService.offLoading();
        })
      )
      .subscribe({
        next: () => this.onSuccessEdit(),
        error: (err: HttpErrorResponse) => this.onErrorHandler(err),
      });
  }
}
