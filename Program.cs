using System;

class Program
{
    static void Main(string[] args)
    {
        Console.WriteLine("Testing Abdul's AI Code Reviewer...");

        // Intentional Flaw: This will crash with a NullReferenceException!
        string text = null;
        int length = text.Length; 

        Console.WriteLine($"The length is: {length}");
    }
}
