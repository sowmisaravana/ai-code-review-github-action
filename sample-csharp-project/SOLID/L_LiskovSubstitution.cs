using System;

namespace SampleCsharpProject.SOLID
{
    public class Document
    {
        public string Title { get; set; } = string.Empty;
        public string Content { get; set; } = string.Empty;

        public virtual void Save()
        {
            Console.WriteLine($"Saving document '{Title}' content to file...");
        }
    }

    // VIOLATION: Liskov Substitution Principle (LSP)
    // ReadOnlyDocument inherits from Document but throws NotSupportedException when Save is called.
    // Clients using Document cannot safely substitute it with ReadOnlyDocument without breaking.
    public class ReadOnlyDocument : Document
    {
        public override void Save()
        {
            throw new NotSupportedException("Cannot save a read-only document. Action is not supported!");
        }
    }
}
