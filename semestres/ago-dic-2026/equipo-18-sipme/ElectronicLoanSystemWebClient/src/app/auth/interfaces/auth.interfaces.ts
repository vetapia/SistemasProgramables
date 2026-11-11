import { Role, User } from "../../shared/interfaces/app.intefaces"


export interface AuthResponse {
    user: User
    token: string
    role: Role
}

export interface VerifyResponse {
    user: User
    role: Role
}