using System;
using System.IO;
using System.Net.Mail;

namespace SampleCsharpProject.SOLID
{
    // VIOLATION: Single Responsibility Principle (SRP)
    // This class manages user profile data in the database, formats reports, sends emails, and performs file logging.
    // It has multiple reasons to change.
    public class UserProfileManager
    {
        public void UpdateUserProfile(int userId, string newEmail, string newBio)
        {
            // 1. Direct database interaction (mocked)
            Console.WriteLine($"Updating user {userId} in the database: Email={newEmail}, Bio={newBio}");
            
            // 2. Logging to a file (Responsibility: Logging)
            try
            {
                File.AppendAllText("logs.txt", $"User {userId} profile updated at {DateTime.Now}\n");
            }
            catch (IOException ex)
            {
                Console.WriteLine($"Failed to write log: {ex.Message}");
            }

            // 3. Formatting report (Responsibility: Formatting/Presentation)
            string report = $"=== USER PROFILE REPORT ===\nID: {userId}\nEmail: {newEmail}\nBio: {newBio}\n";
            Console.WriteLine(report);

            // 4. Sending notification email (Responsibility: Notification Delivery)
            try
            {
                using (var smtpClient = new SmtpClient("smtp.mailtrap.io"))
                {
                    var mailMessage = new MailMessage(
                        "system@app.com",
                        newEmail,
                        "Profile Updated",
                        "Your profile details have been successfully modified."
                    );
                    smtpClient.Send(mailMessage);
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to send email: {ex.Message}");
            }
        }
    }
}
