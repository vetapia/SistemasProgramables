import { Component, inject, input, OnInit, output, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { FormUtils } from '../../../shared/utils/form.utils';
import { Group } from '../../../groups/interfaces/grups.interfaces';
import { GroupInputFind } from '../../../groups/components/group-input-find/group-input-find';
import { Student, StudentRequest } from '../../interfaces/students.intefaces';

@Component({
  selector: 'student-form',
  imports: [ReactiveFormsModule, GroupInputFind],
  templateUrl: './student-form.html',
})
export class StudentForm implements OnInit {
  private fb = inject(FormBuilder);

  public successAction = output<StudentRequest>();
  public studentEdit = input<Student | null>();
  public formUtils = FormUtils;

  public selectedGroup = signal<Group | null>(null);

  public studentForm = this.fb.group({
    userName: ['', [Validators.required, Validators.minLength(5), Validators.maxLength(50)]],
    name: ['', [Validators.required, Validators.maxLength(100)]],
    lastName: ['', [Validators.required, Validators.maxLength(100)]],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]],
    controlNumber: ['', [Validators.required, Validators.minLength(6), Validators.maxLength(50)]],
    semester: [1, [Validators.required, Validators.min(1), Validators.max(13)]],
    groupId: [null as number | null, [Validators.required, Validators.min(1)]],
  });

  ngOnInit() {
    const student = this.studentEdit();
    if (student) {
      this.initStudentEdit(student);
    }
  }

  private initStudentEdit(student: Student) {
    if (student.group) {
      this.selectedGroup.set(student.group);
    }

    // Al editar, la contraseña no es obligatoria
    this.studentForm.get('password')?.clearValidators();
    this.studentForm.get('password')?.setValidators([Validators.minLength(8)]);
    this.studentForm.get('password')?.updateValueAndValidity();

    this.studentForm.patchValue({
      userName: student.user?.userName ?? '',
      name: student.user?.name ?? '',
      lastName: student.user?.lastName ?? '',
      email: student.user?.email ?? '',
      controlNumber: student.controlNumber,
      semester: student.semester,
      groupId: student.group?.id ?? null,
    });
  }

  public onGroupChange(group: Group | null) {
    this.selectedGroup.set(group);
    this.studentForm.patchValue({
      groupId: group?.id ?? null,
    });
    this.studentForm.get('groupId')?.markAsTouched();
  }

  public onSendStudent() {
    this.studentForm.markAllAsTouched();

    if (this.studentForm.valid) {
      const val = this.studentForm.value;

      const studentRequest: StudentRequest = {
        student: {
          controlNumber: val.controlNumber!,
          semester: Number(val.semester!),
          groupId: Number(val.groupId!),
        },
        user: {
          userName: val.userName!,
          name: val.name!,
          lastName: val.lastName!,
          email: val.email!,
          ...(val.password ? { password: val.password } : {}),
        },
      };

      this.successAction.emit(studentRequest);
    }
  }
}
