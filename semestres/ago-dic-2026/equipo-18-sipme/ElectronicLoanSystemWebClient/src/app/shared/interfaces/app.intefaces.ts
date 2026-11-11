export interface User {
    id: string
    userName: string
    name: string
    lastName: string
    email: string
}

export interface PaginationParams {
    page: number
    size: number
}

export interface PaginatedResponse<T>{
    items: T[]
    currentPage: number,
    pageSize: number,
    totalCount: number,
    totalPages: number,
    hasPrevious: boolean,
    hasNext: boolean
}

export type Role = "Student" | "Admin"