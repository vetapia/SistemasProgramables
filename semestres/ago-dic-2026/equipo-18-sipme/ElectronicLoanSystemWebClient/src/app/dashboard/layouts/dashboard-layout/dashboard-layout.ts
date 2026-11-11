import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { DashboardHeader } from '../../components/header/header';
import { DashboardSidebar } from '../../components/sidebar/sidebar';
import { LoadingPage } from '../../../shared/components/loading-page/loading-page';

@Component({
  selector: 'dashboard-layout',
  imports: [RouterOutlet, DashboardHeader, DashboardSidebar, LoadingPage],
  templateUrl: './dashboard-layout.html',
})
export class DashboardLayout {}
