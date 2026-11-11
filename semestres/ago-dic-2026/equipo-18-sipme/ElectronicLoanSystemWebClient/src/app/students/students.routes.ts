import { Routes } from "@angular/router";
import { HomePageStudents } from "./pages/home-page-students/home-page-students";
import { PaginationService } from "../shared/services/pagination.service";

const routes : Routes = [
    {
        path: "",
        component: HomePageStudents,
        providers: [PaginationService]
    }
]

export default routes