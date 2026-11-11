import { Routes } from "@angular/router";
import { HomePageGroups } from "./pages/home-page-groups/home-page-groups";
import { PaginationService } from "../shared/services/pagination.service";

const routes: Routes = [
    {
        path: "",
        component: HomePageGroups,
        providers: [PaginationService]
    }
]

export default routes
