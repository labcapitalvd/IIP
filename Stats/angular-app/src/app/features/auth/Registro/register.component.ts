import { Component, OnInit } from '@angular/core';
import { FormGroup, FormBuilder, Validators } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';

@Component({
  selector: 'app-register',
  templateUrl: './register.component.html',
  styleUrls: ['./register.component.scss']
})
export class RegisterComponent implements OnInit {
  loginForm!: FormGroup;
  loading = false;
  error: string | null = null;

  constructor(
    private fb: FormBuilder,
    private http: HttpClient,
    private router: Router
  ) { }

  ngOnInit(): void {
    this.loginForm = this.fb.group({
      username: ['', [Validators.required]],
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required]]
    });
  }

  onSubmit(): void {
    if (this.loginForm.invalid) {
      return;
    }

    this.loading = true;
    this.error = null;

    const { username, password, email } = this.loginForm.value;
    const body = new URLSearchParams();
    body.set('grant_type', 'password');
    body.set('username', username);
    body.set('password', password);
    body.set('email', email);

    // Cambiar URL según tu configuración real
    this.http.post<any>('https://localhost:8001/public/auth/register', body.toString(), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }).subscribe({
      next: (response) => {
        this.loading = false;
        console.log('Registro exitoso', response);
        localStorage.setItem('access_token', response.access_token);
        if (response.refresh_token) {
          localStorage.setItem('refresh_token', response.refresh_token);
        }
        this.router.navigate(['/dashboard']);
      },
      error: (err) => {
        this.loading = false;
        this.error = 'Credenciales inválidas o error del servidor';
        console.error('Registro error', err);
      }
    });
  }
}
