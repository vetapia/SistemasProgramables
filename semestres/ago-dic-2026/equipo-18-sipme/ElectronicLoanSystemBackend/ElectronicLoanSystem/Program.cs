using ElectronicLoanSystem.Data;
using ElectronicLoanSystem.Data.Seeders;
using ElectronicLoanSystem.Exceptions;
using ElectronicLoanSystem.Extensions;
using ElectronicLoanSystem.Models;
using ElectronicLoanSystem.Services;
using Microsoft.AspNetCore.Identity;
using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);

//Services controllers
builder.Services.AddControllers();
builder.Services.AddProblemDetails();
builder.Services.AddExceptionHandler<ApiExceptionHandler>();

//database
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("DefaultConnection"))
);

//cors
builder.Services.AddCors(options =>
{
    options.AddPolicy("AngularPolicy", policy =>
    {
        policy.WithOrigins("http://localhost:4200")
        .AllowAnyHeader()
        .AllowAnyMethod();
    });
});

//Auth and Roles
builder.Services.AddApplicationIdentity(builder.Configuration);

//Jwt Configuration
builder.Services.AddAuthenticationExt(builder.Configuration);
builder.Services.AddAuthorization();

//Services
builder.Services.AddScoped<IMaterialService, MaterialService>();
builder.Services.AddScoped<IGroupService, GroupService>();
builder.Services.AddScoped<IBucketService, BucketService>();
builder.Services.AddScoped<IStudentService, StudentService>();
builder.Services.AddScoped<ILoanService, LoanService>();
builder.Services.AddScoped<IAuthService, AuthService>();

// Add services to the container.
// Learn more about configuring OpenAPI at https://aka.ms/aspnet/openapi
builder.Services.AddOpenApi();

var app = builder.Build();

//exceptions
app.UseExceptionHandler();

//cors
app.UseCors("AngularPolicy");

using (var scope = app.Services.CreateScope())
{
    var context = scope.ServiceProvider.GetRequiredService<AppDbContext>();
    var userManager = scope.ServiceProvider.GetRequiredService<UserManager<User>>(); // 👈 Ojo aquí
    var roleManager = scope.ServiceProvider.GetRequiredService<RoleManager<IdentityRole>>();

    await SeedData.InitializeAsync(context, userManager, roleManager);
}

//auth middlewares 
app.UseAuthentication();
app.UseAuthorization();

//Map controllers
app.MapControllers();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
}

app.UseHttpsRedirection();

app.Run();
