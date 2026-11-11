import { Component, inject, input, output } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { FormUtils } from '../../../shared/utils/form.utils';
import { Group } from '../../interfaces/grups.interfaces';

@Component({
  selector: 'group-form',
  imports: [ReactiveFormsModule],
  templateUrl: './group-form.html',
})
export class GroupForm {

  private fb = inject(FormBuilder)
  public successAction = output<Group>()
  public groupEdit = input<Group | null>()
  public formUtils = FormUtils

  public groupForm = this.fb.group({
    name: ["", [Validators.required, Validators.maxLength(50)]],
    period: ["", [Validators.required, Validators.maxLength(50)]],
    schedule: ["", [Validators.required, Validators.maxLength(50)]]
  })

  public ngOnInit(){
    const group = this.groupEdit()

    if(group){
      this.initGroupEdit(group)
    }
  }

  private initGroupEdit(group: Group){
    this.groupForm.patchValue({
      name: group.name,
      period: group.period,
      schedule: group.schedule
    })
  }

  public onSendGroup(){
    this.groupForm.markAllAsTouched()

    if (this.groupForm.valid) {
      const {name, period, schedule} = this.groupForm.value

      this.successAction.emit({
        id: this.groupEdit()?.id ?? 0,
        name: name!,
        period: period!,
        schedule: schedule!
      })
    }
  }
}
