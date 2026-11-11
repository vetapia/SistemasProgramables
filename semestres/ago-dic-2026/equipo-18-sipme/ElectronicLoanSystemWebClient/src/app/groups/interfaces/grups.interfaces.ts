import { PaginationParams } from "../../shared/interfaces/app.intefaces"

export interface Group{
    id: number
    name: string
    schedule: string
    period: string
}

export interface GroupPaginationParams extends PaginationParams {
    name?: string
}
