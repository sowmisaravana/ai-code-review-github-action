using System;

namespace SampleCsharpProject.SOLID
{
    public enum CustomerType
    {
        Regular,
        Premium,
        VIP
    }

    // VIOLATION: Open/Closed Principle (OCP)
    // This class relies on a switch statement over the CustomerType enum.
    // Adding a new customer type (e.g. "SuperVIP" or "Enterprise") requires modifying the calculate method.
    // It should be open for extension, but closed for modification via polymorphism or abstract strategy.
    public class InvoiceDiscountCalculator
    {
        public decimal CalculateDiscount(decimal invoiceAmount, CustomerType customerType)
        {
            switch (customerType)
            {
                case CustomerType.Regular:
                    return invoiceAmount * 0.05m; // 5% discount
                case CustomerType.Premium:
                    return invoiceAmount * 0.15m; // 15% discount
                case CustomerType.VIP:
                    return invoiceAmount * 0.30m; // 30% discount
                default:
                    throw new ArgumentOutOfRangeException(nameof(customerType), "Unknown customer type");
            }
        }
    }
}
