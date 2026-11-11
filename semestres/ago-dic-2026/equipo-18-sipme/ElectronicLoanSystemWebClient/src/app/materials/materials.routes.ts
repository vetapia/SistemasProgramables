import { Routes } from "@angular/router";
import { HomePageMaterials } from "./pages/home-page-materials/home-page-materials";
import { PaginationService } from "../shared/services/pagination.service";

const routes: Routes = [
    {
        path: "",
        component: HomePageMaterials,
        providers: [PaginationService]
    }
]

export default routes
