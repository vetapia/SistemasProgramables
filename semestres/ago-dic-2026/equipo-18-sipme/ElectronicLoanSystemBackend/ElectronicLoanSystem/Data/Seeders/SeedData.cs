using ElectronicLoanSystem.Models;
using Microsoft.AspNetCore.Identity;

namespace ElectronicLoanSystem.Data.Seeders;

public static class SeedData
{
    public static async Task InitializeAsync(
        AppDbContext context,
        UserManager<User> userManager,
        RoleManager<IdentityRole> roleManager
        )
    {
        await context.Database.EnsureCreatedAsync();
        
        var roles = new string[]{ "Admin", "Student" };
        foreach (var role in roles)
        {
            if (!await roleManager.RoleExistsAsync(role))
            {
                await roleManager.CreateAsync(new IdentityRole(role));
            }    
        }

        if (!context.Users.Any())
        {
            var user = new User{
                UserName = "Mau",
                Name = "Mauricio Fernando",
                LastName = "Salcedo olivares",
                Email = "2526321@leon.tencm.mx"
            };
            var resultUser = await userManager.CreateAsync(user, "123456Abc123!");
            if (resultUser.Succeeded)
            {
                await userManager.AddToRoleAsync(user, "Admin");
            }
            
            var christian = new User{
                UserName = "Christian",
                Name = "Christian de Jesús",
                Email = "23240405@leon.tecnm.mx",
                LastName = "Ramirez Ramos"
            };
            var resultChristian = await userManager.CreateAsync(christian, "123456Abc123!");
            if (resultChristian.Succeeded)
            {
                await userManager.AddToRoleAsync(christian, "Student");
            }
        }

        if (!context.Groups.Any())
        {
            var group = new Group {
                Name = "7C",
                Period = "ENERO-JUNIO-2026",
                Schedule = "10:30-12:15"
            };
            context.Groups.Add(group);
            await context.SaveChangesAsync();
        }

        if (!context.Students.Any())
        {
            var userDb = await userManager.FindByEmailAsync("23240405@leon.tecnm.mx");
            var groupDb = context.Groups.FirstOrDefault(c => c.Name.Equals("7C"));
            var student = new Student
            {
                ControlNumber = "23240405",
                Semester = 7,
                Group = groupDb,
                User = userDb
            };
            context.Students.Add(student);
            await context.SaveChangesAsync();
        }
    }
}