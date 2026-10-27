using Avalonia;
using System;
using System.IO;
using System.Linq;
using System.Threading.Tasks;

namespace Warpstorm.Configurator;

internal static class Program
{
    private static string LogPath => Path.Combine(AppContext.BaseDirectory, "warpstorm-configurator.log");

    [STAThread]
    public static void Main(string[] args)
    {
        AppDomain.CurrentDomain.UnhandledException += (_, e) => Log("Unhandled exception: " + e.ExceptionObject);
        TaskScheduler.UnobservedTaskException += (_, e) => Log("Unobserved task exception: " + e.Exception);

        if (args.Length >= 3 && args[0] == "--bake-test")
        {
            // Dev check: bake one faction into a scratch folder (never the game). Args: <faction> <outRoot> [packDir]
            var game = GameLocator.Find();
            var job = new Baker.Job { Faction = args[1], Primary = "24572B", Secondary = "B08A4A", HueWindow = 0.16f, SatThreshold = 0.08f, Feather = 0.08f, MaxSize = 2048 };
            if (args.Length > 3) job.Pack = Warpstorm.Shared.SchemePack.Load(args[3]);
            var sw = System.Diagnostics.Stopwatch.StartNew();
            var r = Baker.Bake(game, job, Console.WriteLine, default, args[2]);
            Console.WriteLine($"baked={r.Baked} skipped={r.Skipped} failed={r.Failed} total={r.Total} in {sw.Elapsed.TotalSeconds:F1}s key={job.Key} {r.Note}");
            return;
        }
        if (args.Contains("--selftest"))
        {
            Environment.ExitCode = SelfTest.Run();
            return;
        }

        try
        {
            Log($"Starting Warpstorm Configurator (baseDir={AppContext.BaseDirectory}).");
            BuildAvaloniaApp().StartWithClassicDesktopLifetime(args);
        }
        catch (Exception ex)
        {
            Log("Fatal startup error: " + ex);
            throw;
        }
    }

    public static AppBuilder BuildAvaloniaApp()
        => AppBuilder.Configure<App>()
            .UsePlatformDetect()
            .LogToTrace();

    private static void Log(string message)
    {
        try
        {
            File.AppendAllText(LogPath, $"[{DateTime.Now:O}] {message}{Environment.NewLine}");
        }
        catch
        {
            // logging is best-effort (the base dir may be read-only)
        }
    }
}
