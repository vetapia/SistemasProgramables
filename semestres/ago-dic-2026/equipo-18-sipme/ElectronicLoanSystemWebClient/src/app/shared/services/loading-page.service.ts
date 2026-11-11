import { Service, signal } from '@angular/core';

@Service()
export class LoadingPageService {
    private showLoading = signal(false)

    public isLoading = this.showLoading.asReadonly()

    public onLoading(){
        this.showLoading.set(true)
    }

    public offLoading(){
        this.showLoading.set(false)
    }

}
