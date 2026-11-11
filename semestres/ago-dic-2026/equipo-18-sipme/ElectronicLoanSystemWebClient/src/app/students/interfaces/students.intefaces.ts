import { Group } from "../../groups/interfaces/grups.interfaces"
import { PaginationParams, User } from "../../shared/interfaces/app.intefaces"

export interface Student {
    id: number
    controlNumber: string
    semester: number
    user: User
    group: Group | null
}

export interface StudentPaginationParams extends PaginationParams {
    name?: string
}

export interface StudentRequest {
    student: {
        controlNumber: string
        semester: number
        groupId: number
    }
    user: {
        userName: string
        name: string
        lastName: string
        email: string
        password?: string
    }
}