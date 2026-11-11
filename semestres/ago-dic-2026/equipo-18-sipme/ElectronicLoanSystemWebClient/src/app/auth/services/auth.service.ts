import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { inject, Service, signal } from '@angular/core';
import { catchError, finalize, map, of, single, tap } from 'rxjs';
import { AuthResponse, VerifyResponse } from '../interfaces/auth.interfaces';
import { environment } from '../../../environments/environment.development';
import { Role, User } from '../../shared/interfaces/app.intefaces';

type AuthStatus = "cheking" | "authenticated" | "not-authenticated"
const baseUrl = environment.apiUrl

@Service()
export class AuthService {

    private http = inject(HttpClient)

    private _user = signal<User | null>(null);
    private _token = signal<string | null>(localStorage.getItem("token"))
    private _authStatus = signal<AuthStatus>(
        localStorage.getItem("token") ? "cheking" : "not-authenticated"
    )
    private _role = signal<Role | null>(null)

    public user = this._user.asReadonly()
    public token = this._token.asReadonly()
    public role = this._role.asReadonly()

    public login(email: string, password: string){
        return this.http.post<AuthResponse>(`${baseUrl}/auth/login`, {
            email,
            password
        })
        .pipe(
            tap(data => this.handleAuthSuccess(data.token, data.user, data.role))
        )
    }

    public checkStatus(){
        const token = this._token()

        if(!token){
            this.clearData()
            return of(false)
        }

        return this.http.get<VerifyResponse>(`${baseUrl}/auth/verify`).pipe(
            map(res => {
                this.handleAuthSuccess(token, res.user, res.role)
                return true
            }),
            catchError((err: HttpErrorResponse) => {
                if(err.status == 401) this.clearData()
                return of(false)
            })
        )
    }

    public logout(){
        return this.http.post(`${baseUrl}/auth/logout`, {}).pipe(
            catchError(() => of(null)),
            finalize(() => {
                this.clearData()
            })
        )
    }

    private clearData(){
        localStorage.removeItem("token")
        this._token.set(null)
        this._user.set(null)
        this._authStatus.set("not-authenticated")
    }

    private handleAuthSuccess(token: string, user: User, role: Role){
        this._user.set(user)
        this._token.set(token)
        this._role.set(role)
        this._authStatus.set("authenticated")
        localStorage.setItem("token", token)
    }

}
