import { Component, inject, input, output } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Material } from '../../interfaces/material.interfaces';
import { FormUtils } from '../../../shared/utils/form.utils';

@Component({
  selector: 'material-form',
  imports: [ReactiveFormsModule],
  templateUrl: './material-form.html',
})
export class CreateMaterialForm {

  private fb = inject(FormBuilder)
  public successAction = output<Material>()
  public materialEdit = input<Material | null>()
  public formUtils = FormUtils
  
  public materialForm = this.fb.group({
    name: ["", [Validators.required]],
    materialId: ["", [Validators.required]]
  })

  public ngOnInit(){
    const material = this.materialEdit()

    if(material){
      this.initMaterialEdit(material)
    }

  }

  private initMaterialEdit(material: Material){
    this.materialForm.patchValue({
      name: material.name,
      materialId: material.materialUid
    })
  }

  public onSendMaterial(){

    this.materialForm.markAllAsTouched()

    if (this.materialForm.valid) {
      const {name, materialId} = this.materialForm.value
      
      if (this.materialEdit()) {
          this.successAction.emit({
            id: this.materialEdit()?.id!,
            name: name!,
            materialUid: materialId!
          })
        }else{
          this.successAction.emit({
            id: 0,
            name: name!,
            materialUid: materialId!
          })
        }
    }
  }

}
