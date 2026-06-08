using System;
using System.IO;
using System.Net.Http;
using System.Threading.Tasks;

namespace SampleCsharpProject.AsyncCorrectness
{
    public class AsyncViolations
    {
        private static readonly HttpClient _httpClient = new HttpClient();

        // VIOLATION: Async Correctness (Blocking Async Code)
        // Using `.Result` or `.Wait()` blocks the executing thread, potentially causing deadlocks.
        public string FetchDataSync(string url)
        {
            var task = _httpClient.GetStringAsync(url);
            return task.Result; // Sync-over-async blocking!
        }

        // VIOLATION: Async Correctness (async void)
        // Async void should only be used for event handlers. Exceptions thrown cannot be caught by callers.
        public async void LogDataAsync(string logMessage)
        {
            await Task.Delay(100);
            Console.WriteLine($"Logged: {logMessage}");
        }

        // VIOLATION: Async Correctness (Missing await)
        // Method returns void and is marked async, but does not use 'await' anywhere. It runs synchronously.
        #pragma warning disable CS1998 // Async method lacks 'await' operators and will run synchronously
        public async Task PerformFakeAsyncWork()
        {
            Console.WriteLine("Doing some work...");
        }
        #pragma warning restore CS1998

        // VIOLATION: Async Correctness (Dispose before execution completes)
        // Returning a task from within a using block without awaiting it. 
        // The Stream/StreamReader will be disposed before the reader task actually runs.
        public Task<string> ReadFileContentsAsync(string filePath)
        {
            using (var reader = new StreamReader(filePath))
            {
                return reader.ReadToEndAsync(); // Bug! Reader will be disposed before ReadToEndAsync finishes.
            }
        }
    }
}
