import { HttpParams } from '@angular/common/http'

export function toHttpParams(params: object): HttpParams {
    let result = new HttpParams()

    for (const [key, value] of Object.entries(params)) {
        if (value === undefined || value === null) continue
        result = result.set(key, String(value))
    }

    return result
}
