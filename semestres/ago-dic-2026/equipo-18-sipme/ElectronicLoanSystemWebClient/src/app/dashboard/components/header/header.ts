import { Component, computed, inject } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../../auth/services/auth.service';

@Component({
  selector: 'dashboard-header',
  imports: [],
  templateUrl: './header.html',
})
export class DashboardHeader {
  private authService = inject(AuthService);
  private router = inject(Router);

  protected readonly user = this.authService.user;

  protected readonly initials = computed(() => {
    const user = this.user();

    if (!user) {
      return '?';
    }

    return `${user.name.charAt(0)}${user.lastName.charAt(0)}`.toUpperCase();
  });

  protected logout() {
    this.authService.logout().subscribe(() => this.router.navigateByUrl('/login'));
  }
}
