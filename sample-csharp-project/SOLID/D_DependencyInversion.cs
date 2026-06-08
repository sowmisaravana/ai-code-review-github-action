using System;

namespace SampleCsharpProject.SOLID
{
    public class SqlServerDatabase
    {
        public void SaveOrder(string orderId)
        {
            Console.WriteLine($"Order {orderId} saved to SqlServerDatabase.");
        }
    }

    public class SmsSender
    {
        public void SendSms(string message)
        {
            Console.WriteLine($"Sms sent: {message}");
        }
    }

    // VIOLATION: Dependency Inversion Principle (DIP)
    // OrderProcessor (high-level) directly instantiates SqlServerDatabase and SmsSender (low-level modules) using the 'new' keyword.
    // It should depend on abstractions (interfaces) rather than concrete implementations.
    public class OrderProcessor
    {
        private SqlServerDatabase _database;
        private SmsSender _smsSender;

        public OrderProcessor()
        {
            // Direct coupling to concrete implementations
            _database = new SqlServerDatabase();
            _smsSender = new SmsSender();
        }

        public void ProcessOrder(string orderId)
        {
            _database.SaveOrder(orderId);
            _smsSender.SendSms($"Order {orderId} has been successfully processed.");
        }
    }
}
