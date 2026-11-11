import { Component, computed, inject } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from '../../../auth/services/auth.service';
import { Role } from '../../../shared/interfaces/app.intefaces';
import { Roles } from '../../../auth/utils/constants';
import { verifyContainRole } from '../../../auth/utils/utils';

interface NavItem {
  label: string;
  path: string;
  icon: string;
  roles: Role[];
  exact?: boolean;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

@Component({
  selector: 'dashboard-sidebar',
  imports: [RouterLink, RouterLinkActive],
  templateUrl: './sidebar.html',
  host: {
    class: 'drawer-side',
  },
})
export class DashboardSidebar {

  private readonly navSections: NavSection[] = [
    {
      title: 'Principal',
      items: [
        {
          label: 'Inicio',
          path: '/panel',
          exact: true,
          roles: [Roles.ADMIN, Roles.STUDENT],
          icon: 'M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25',
        },
      ],
    },
    {
      title: 'Académico',
      items: [
        {
          label: 'Estudiantes',
          path: '/panel/estudiantes',
          roles: [Roles.ADMIN],
          icon: 'M4.26 10.147a60.438 60.438 0 0 0-.491 6.347A48.62 48.62 0 0 1 12 20.904a48.62 48.62 0 0 1 8.232-4.41 60.46 60.46 0 0 0-.491-6.347m-15.482 0a50.636 50.636 0 0 0-2.658-.813A59.906 59.906 0 0 1 12 3.493a59.903 59.903 0 0 1 10.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.717 50.717 0 0 1 12 13.489a50.702 50.702 0 0 1 7.74-3.342M6.75 15a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Zm0 0v-3.675A55.378 55.378 0 0 1 12 8.443m-7.007 11.55A5.981 5.981 0 0 0 6.75 15.75v-1.5',
        },
        {
          label: 'Grupos',
          path: '/panel/grupos',
          roles: [Roles.ADMIN],
          icon: 'M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 0 1 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0 1 11.964-3.07M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0Zm8.25 2.25a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0Z',
        },
      ],
    },
    {
      title: 'Inventario',
      items: [
        {
          label: 'Materiales',
          path: '/panel/materiales',
          roles: [Roles.ADMIN, Roles.STUDENT],
          icon: 'm21 7.5-9-5.25L3 7.5m18 0-9 5.25m9-5.25v9l-9 5.25M3 7.5l9 5.25M3 7.5v9l9 5.25m0-9v9',
        },
        {
          label: 'Cajones',
          path: '/panel/cajones',
          roles: [Roles.ADMIN],
          icon: 'm20.25 7.5-.625 10.632a2.25 2.25 0 0 1-2.247 2.118H6.622a2.25 2.25 0 0 1-2.247-2.118L3.75 7.5m8.25 3v6.75m0 0-3-3m3 3 3-3M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125Z',
        },
      ],
    },
    {
      title: 'Operación',
      items: [
        {
          label: 'Préstamos',
          path: '/panel/prestamos',
          roles: [Roles.ADMIN, Roles.STUDENT],
          icon: 'M7.5 21 3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5',
        },
      ],
    },
  ];

  protected readonly authService = inject(AuthService);

  protected readonly visibleSections = computed(() => {
    const role = this.authService.role();

    if (!role) {
      return [];
    }

    return this.navSections
      .map(section => ({
        ...section,
        items: section.items.filter(item => verifyContainRole(item.roles, role)),
      }))
      .filter(section => section.items.length > 0);
  });

}
