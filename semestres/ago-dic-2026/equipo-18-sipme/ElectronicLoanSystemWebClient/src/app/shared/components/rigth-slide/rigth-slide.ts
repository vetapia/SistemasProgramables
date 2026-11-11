import { Component, output } from '@angular/core';
import { LucideBadgeX } from '@lucide/angular';

@Component({
  selector: 'rigth-slide',
  imports: [LucideBadgeX],
  templateUrl: './rigth-slide.html',
})
export class RigthSlide {

  closeSlide = output()

}
