// Trigger AI Review
using System;

namespace SampleCsharpProject.NullHandling
{
    public class Address
    {
        public string Street { get; set; } = string.Empty;
        public string City { get; set; } = string.Empty;
    }

    public class Profile
    {
        public string Bio { get; set; } = string.Empty;
        public Address HomeAddress { get; set; }
    }

    public class User
    {
        public string Username { get; set; } = string.Empty;
        public Profile UserProfile { get; set; }
    }

    public class CustomerService
    {
        // VIOLATION: Null Handling
        // 1. Parameter 'user' is not validated for null before accessing its properties.
        // 2. Nested property access (user.UserProfile.HomeAddress.City) can trigger NullReferenceException.
        // 3. ToString() call on potentially null values.
        public void ProcessCustomerDetails(User user)
        {
            string username = user.Username; 
            Console.WriteLine($"Username: {username.ToUpper()}");

            // Danger: user.UserProfile or HomeAddress can easily be null.
            string city = user.UserProfile.HomeAddress.City;
            Console.WriteLine($"Customer lives in: {city}");

            // Danger: GetProfile(user.Username) might return null if user not found.
            var profile = GetProfile(user.Username);
            Console.WriteLine($"Bio Length: {profile.Bio.Length}");
        }

        private Profile GetProfile(string username)
        {
            if (username == "guest")
            {
                return null; // Can return null!
            }
            return new Profile { Bio = "Regular user profile." };
        }
    }
}
// Test PR for AI Review
