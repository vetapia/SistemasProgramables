import { Component, inject, input, OnInit, output, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { LucideX } from '@lucide/angular';
import { FormUtils } from '../../../shared/utils/form.utils';
import { MaterialInputFind } from '../../../materials/components/material-input-find/material-input-find';
import { Material } from '../../../materials/interfaces/material.interfaces';
import { Bucket, BucketRequest } from '../../interfaces/bucket.interfaces';

@Component({
  selector: 'bucket-form',
  imports: [ReactiveFormsModule, MaterialInputFind, LucideX],
  templateUrl: './bucket-form.html',
})
export class BucketForm implements OnInit {
  private fb = inject(FormBuilder);

  public successAction = output<BucketRequest>();
  public bucketEdit = input<Bucket | null>(null);
  public formUtils = FormUtils;

  public pendingMaterials = signal<Material[]>([]);

  public bucketForm = this.fb.group({
    bucketNumber: [
      null as number | null,
      [Validators.required, Validators.min(1)],
    ],
    name: ['', [Validators.required, Validators.maxLength(50)]],
  });

  public ngOnInit() {
    const bucket = this.bucketEdit();
    if (bucket) {
      this.initBucketEdit(bucket);
    }
  }

  private initBucketEdit(bucket: Bucket) {
    this.bucketForm.patchValue({
      bucketNumber: bucket.bucketNumber,
      name: bucket.name,
    });
  }

  public onMaterialSelected(material: Material | null) {
    if (!material) return;
    const exists = this.pendingMaterials().some((m) => m.id === material.id);
    if (!exists) {
      this.pendingMaterials.update((list) => [...list, material]);
    }
  }

  public removePendingMaterial(materialId: number) {
    this.pendingMaterials.update((list) =>
      list.filter((m) => m.id !== materialId)
    );
  }

  public onSendBucket() {
    this.bucketForm.markAllAsTouched();

    if (this.bucketForm.valid) {
      const { bucketNumber, name } = this.bucketForm.value;

      this.successAction.emit({
        id: this.bucketEdit()?.id ?? 0,
        bucketNumber: Number(bucketNumber),
        name: name!,
        materialIds: this.pendingMaterials().map((m) => m.id),
      });
    }
  }
}
