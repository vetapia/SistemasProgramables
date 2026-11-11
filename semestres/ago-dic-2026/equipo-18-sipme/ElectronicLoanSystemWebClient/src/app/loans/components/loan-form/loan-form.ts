import { Component, inject, output, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { FormUtils } from '../../../shared/utils/form.utils';
import { StudentInputFind } from '../../../students/components/student-input-find/student-input-find';
import { MaterialInputFind } from '../../../materials/components/material-input-find/material-input-find';
import { Student } from '../../../students/interfaces/students.intefaces';
import { Material } from '../../../materials/interfaces/material.interfaces';
import { LoanRequest } from '../../interfaces/loan.interfaces';

@Component({
  selector: 'loan-form',
  imports: [ReactiveFormsModule, StudentInputFind, MaterialInputFind],
  templateUrl: './loan-form.html',
})
export class LoanForm {
  private fb = inject(FormBuilder);

  public successAction = output<LoanRequest>();
  public formUtils = FormUtils;

  public selectedStudent = signal<Student | null>(null);
  public selectedMaterial = signal<Material | null>(null);

  public loanForm = this.fb.group({
    userId: ['', [Validators.required]],
    materialId: [null as number | null, [Validators.required, Validators.min(1)]],
  });

  protected showStudent(student: Student){
    return `${student.controlNumber}: ${student.user.name} ${student.user.lastName}`
  }

  public onStudentChange(student: Student | null) {
    this.selectedStudent.set(student);
    this.loanForm.patchValue({
      userId: student?.user?.id ?? '',
    });
    this.loanForm.get('userId')?.markAsTouched();
  }

  public onMaterialChange(material: Material | null) {
    this.selectedMaterial.set(material);
    this.loanForm.patchValue({
      materialId: material?.id ?? null,
    });
    this.loanForm.get('materialId')?.markAsTouched();
  }

  public onSendLoan() {
    this.loanForm.markAllAsTouched();

    if (this.loanForm.valid) {
      const { userId, materialId } = this.loanForm.value;

      this.successAction.emit({
        userId: userId!,
        materialId: Number(materialId!),
      });
    }
  }
}
