import { FormGroup, ValidationErrors } from "@angular/forms"

export class FormUtils {
    static namePattern = '([a-zA-Z]+) ([a-zA-Z]+)';
    static emailPattern = '^[a-z0-9._%+-]+@[a-z0-9.-]+\\.[a-z]{2,4}$';
    static notOnlySpacesPattern = '^[a-zA-Z0-9]+$';

    static isValidField(form: FormGroup ,fildName: string): boolean | null{
        return (form.controls[fildName].errors && form.controls[fildName].touched)
    }

    private static getTextError(errors: ValidationErrors){
        for(const key of Object.keys(errors)){
            switch(key){
            case "required":
                return "Este campo es rerquerido"
            case "minlength":
                return `Minimo de ${errors['minlength'].requiredLength} caracteres`
            case "maxlength":
                return `Máximo de ${errors['maxlength'].requiredLength} caracteres`
            case "min":
                return `Valor minimo de ${ errors['min'].min }`
            case "max":
                return `Valor maximo de ${ errors['max'].max }`
            case "email":
                return `El valor ingrsado no es un correo electronico`
            case "pattern":
                if(errors["pattern"].requiredPattern == FormUtils.emailPattern){
                    return "el correo electrino no es permitido"
                }
                return "Error de patron contra expresion regular"
            case "serverError":
                return errors['serverError'];
            default:
                return typeof errors[key] === 'string' ? errors[key] : "Error de validación"
            }
            
        }

        return null
    }

    static getFildError(form: FormGroup ,fildName : string): string | null {
      if(!form.controls[fildName]) return null
    
      const errors = form.controls[fildName].errors ?? {}
    
      return this.getTextError(errors)
    }

    static addErrorsFromBadApiResponse(errors: Record<string, string[]>, form: FormGroup){
        Object.keys(errors).forEach((key) => {
            const control = form.get(key)
            if (control) {
                control.setErrors({ serverError: errors[key][0] })
            }
        });
    }
}