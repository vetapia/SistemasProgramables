import { PaginationParams } from '../../shared/interfaces/app.intefaces';

export interface Material {
    id: number
    materialUid: string
    name: string
    bucketId?: number | null
}

export interface MaterialPaginationParams extends PaginationParams {
    name?: string
    withoutBucket?: boolean
}