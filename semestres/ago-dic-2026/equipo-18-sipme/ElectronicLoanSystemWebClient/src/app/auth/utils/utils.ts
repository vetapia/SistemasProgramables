import { Role } from "../../shared/interfaces/app.intefaces";

export function verifyContainRole(excpectedRoles: Role[], userRole: Role){
    return excpectedRoles.some(role => role == userRole)
}