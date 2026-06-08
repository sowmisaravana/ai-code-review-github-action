using System;

namespace SampleCsharpProject.SOLID
{
    // VIOLATION: Interface Segregation Principle (ISP)
    // IMultiFunctionDevice is a fat interface that combines too many independent operations.
    // Clients are forced to depend on methods they do not use.
    public interface IMultiFunctionDevice
    {
        void Print(string document);
        void Scan(string document);
        void Fax(string document);
        void Copy(string document);
    }

    public class PremiumMultiOfficeDevice : IMultiFunctionDevice
    {
        public void Print(string document) => Console.WriteLine($"Printing: {document}");
        public void Scan(string document) => Console.WriteLine($"Scanning: {document}");
        public void Fax(string document) => Console.WriteLine($"Faxing: {document}");
        public void Copy(string document) => Console.WriteLine($"Copying: {document}");
    }

    // This basic printer only needs Print capability, but is forced to implement Scan, Fax, and Copy.
    public class BasicPrinter : IMultiFunctionDevice
    {
        public void Print(string document)
        {
            Console.WriteLine($"Printing: {document}");
        }

        public void Scan(string document)
        {
            throw new NotImplementedException("Scan capability is not supported on basic printers.");
        }

        public void Fax(string document)
        {
            throw new NotImplementedException("Fax capability is not supported on basic printers.");
        }

        public void Copy(string document)
        {
            throw new NotImplementedException("Copy capability is not supported on basic printers.");
        }
    }
}
