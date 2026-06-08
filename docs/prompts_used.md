# Prompting Strategy & Examples

This document explains the prompting design, structured JSON output strategy, and self-correction instructions used for the Gemini AI Code Reviewer.

## Prompt Strategy

The system prompt template (located in [review_prompt.txt](file:///c:/Users/sowmi/OneDrive/Desktop/Github/prompts/review_prompt.txt)) is designed around three principles:

1. **Explicit Analysis Boundaries:** The prompt limits Gemini's focus strictly to **SOLID Principles**, **Null Handling**, and **Async Correctness**. This prevents irrelevant stylistic or formatting comments.
2. **Schema Enforcement:** The prompt provides an explicit JSON schema and forbids markdown code-block wrapping (like ` ```json ... ``` `) and conversational text, directing the model to start with `{` and end with `}`.
3. **MIME Type Constraints:** The model is invoked with `response_mime_type: "application/json"`, which tells the Gemini model to output valid JSON.

---

## Agentic self-correction

Despite system instructions and MIME constraints, JSON payloads can occasionally fail parsing or validation (e.g. invalid string escape characters, wrong severity strings, or empty schemas). When validation fails:

1. The script catches the `ValidationError` or `JSONDecodeError`.
2. It constructs a repair prompt containing:
   - The original instruction set.
   - The previous malformed response.
   - The specific error traceback details.
3. It asks Gemini to inspect and repair the payload.

### Correction Prompt Template

```
=== REPAIR REQUEST ===
Your previous JSON output was invalid.
Error: [Error Details, e.g. Field 'severity' must be one of 'High', 'Medium', 'Low']
Previous Response:
[Malforming response text]

Please correct the JSON response. Ensure it matches the JSON schema and has NO syntax errors.
```

---

## Analysis Prompt Example

### Input Context
- **Filename:** `OrderProcessor.cs`
- **File Content:**
```csharp
public class OrderProcessor {
    public void ProcessOrder(string id) {
        var db = new SqlServerDatabase();
        db.Save(id);
    }
}
```

### Prompt Output (Gemini Analysis Result)
```json
{
  "findings": [
    {
      "file": "OrderProcessor.cs",
      "line": 3,
      "severity": "High",
      "category": "SOLID Principles",
      "issue": "Dependency Inversion Principle (DIP) Violation: OrderProcessor directly instantiates SqlServerDatabase.",
      "suggestion": "Introduce an abstract interface (e.g. IDatabase) and pass it into OrderProcessor's constructor via Dependency Injection."
    }
  ]
}
```
