using System;
using System.IO;
using System.Collections.Generic;

namespace AiReviewTest
{
    public class Customer
    {
        public int Id { get; set; }
        public string Name { get; set; }
        public string Email { get; set; }
    }

    public class CustomerService
    {
        private List<Customer> _customers = new List<Customer>();

        // Method 1: Adding a customer
        public void AddCustomer(Customer customer)
        {
            // BUG 1: No null check. If 'customer' is null, this will crash!
            Console.WriteLine("Adding customer: " + customer.Name);
            _customers.Add(customer);
        }

        // Method 2: Reading customer data from a file
        public void ProcessCustomerData(string filePath)
        {
            try
            {
                // BUG 2: Resource leak! Missing 'using' statement to close the file.
                StreamReader reader = new StreamReader(filePath);
                string content = reader.ReadToEnd();
                Console.WriteLine("Data length: " + content.Length);
            }
            catch (Exception ex)
            {
                // BUG 3: Empty catch block! This silently swallows errors.
            }
        }

        // Method 3: Finding a customer
        public Customer GetCustomerById(int id)
        {
            foreach (var c in _customers)
            {
                if (c.Id == id)
                {
                    return c;
                }
            }
            // Returns null if customer is not found
            return null; 
        }

        // Method 4: Printing email
        public void PrintCustomerEmail(int id)
        {
            Customer c = GetCustomerById(id);
            
            // BUG 4: Potential NullReferenceException. 
            // If GetCustomerById returns null, calling .Email will crash!
            Console.WriteLine("Customer Email: " + c.Email.ToLower());
        }
    }

    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("Starting Customer Service...");
            CustomerService service = new CustomerService();
            
            // This will trigger Bug 1 instantly
            service.AddCustomer(null);
            
            // This will trigger Bug 4 instantly
            service.PrintCustomerEmail(99);
        }
    }
}
