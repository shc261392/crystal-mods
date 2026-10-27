using System;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Layout;
using Avalonia.Threading;
using Warpstorm.Shared;
using static Warpstorm.Configurator.Loc;

namespace Warpstorm.Configurator;

public partial class MainWindow
{
    private CancellationTokenSource _bakeCts;
    private ProgressBar _bakeBar;
    private TextBlock _bakeStatus;
    private Button _bakeButton, _bakeCancel;
    private bool BakeRunning => _bakeCts != null;

    private static readonly int[] TextureSizes = { 1024, 2048, 4096 };

    private Control BuildBakeCard()
    {
        _bakeBar = new ProgressBar { IsIndeterminate = true, Height = 6, IsVisible = BakeRunning };
        _bakeStatus = Wrap(Ui.Text(BakeSummary(), "faint", 11));
        _bakeButton = Ui.IconTextButton(Icons.Bolt, T("bake.now"), () => StartBake(false), "ghost", T("bake.now.tip"));
        _bakeButton.IsEnabled = !BakeRunning && _session.HasGame;
        _bakeCancel = Ui.Button(T("common.cancel"), () => _bakeCts?.Cancel(), "ghost");
        _bakeCancel.IsVisible = BakeRunning;
        var clear = Ui.IconTextButton(Icons.Delete, T("bake.clear"), () =>
        {
            if (BakeRunning) return;
            try { if (Directory.Exists(Baker.CacheRoot(_session.GameDir))) Directory.Delete(Baker.CacheRoot(_session.GameDir), true); }
            catch (Exception ex) { SetStatus(ex.Message); }
            _bakeStatus.Text = BakeSummary();
        }, "ghost", T("bake.clear.tip"));

        var sizeDef = EditSession.Settings.First(s => s.Name == "MaxTextureSize");
        int.TryParse(_session.SettingValues[sizeDef.Id], out int size);
        var sizeBox = new ComboBox { ItemsSource = TextureSizes.Select(v => $"{v} px").ToList(), SelectedIndex = Math.Max(0, Array.IndexOf(TextureSizes, size)) };
        sizeBox.SelectionChanged += (_, _) =>
        {
            if (sizeBox.SelectedIndex >= 0) _session.SetSetting(sizeDef.Id, TextureSizes[sizeBox.SelectedIndex].ToString());
            _bakeStatus.Text = BakeSummary();
        };
        ToolTip.SetTip(sizeBox, SettingHint(sizeDef));

        return Ui.Surface(Ui.Column(8,
            Ui.Text(T("bake.title"), "groupTitle"),
            Wrap(Ui.Text(T("bake.hint"), "muted", 12)),
            Ui.Row(8, Ui.Text(SettingLabel(sizeDef), null, 12.5), sizeBox),
            Ui.Row(6, _bakeButton, _bakeCancel, clear),
            _bakeBar,
            _bakeStatus));
    }

    /// <summary>"Ultramarines 54 · Blood Angels 0 baked textures · 312 MB on disk".</summary>
    private string BakeSummary()
    {
        if (_session == null || !_session.HasGame) return "";
        var root = Baker.CacheRoot(_session.GameDir);
        var parts = _session.BakeJobs().Select(j =>
        {
            var dir = PaintCache.Folder(root, j.Key);
            int n = Directory.Exists(dir) ? Directory.GetFiles(dir, "*.wpt").Length : 0;
            var name = _catalog.Factions.FirstOrDefault(f => f.Id == _session.PaintDefault(j.Faction)?.FactionId)?.DisplayName(Lang) ?? j.Faction;
            return F("bake.factionCount", name, n);
        }).ToList();
        if (parts.Count == 0) return T("bake.nothing");
        return Loc.List(parts.ToArray()) + "\n" + F("bake.onDisk", PaintCache.SizeOnDisk(root) / 1048576.0);
    }

    private void StartBake(bool auto)
    {
        if (BakeRunning || _session == null || !_session.HasGame) return;
        // The game builds its cache key from the SAVED settings, so bake what is saved.
        if (!auto && _session.UnsavedCount > 0)
        {
            Save();          // a successful Save starts the bake itself
            return;
        }
        var jobs = _session.BakeJobs();
        if (jobs.Count == 0)
        {
            SetStatus(T("bake.nothing"));
            return;
        }

        var gameDir = _session.GameDir;
        _bakeCts = new CancellationTokenSource();
        var token = _bakeCts.Token;
        VerifyBar.IsVisible = true;
        if (_bakeBar != null) _bakeBar.IsVisible = true;
        if (_bakeButton != null) _bakeButton.IsEnabled = false;
        if (_bakeCancel != null) _bakeCancel.IsVisible = true;
        var started = DateTime.UtcNow;

        Task.Run(() =>
        {
            int baked = 0, skipped = 0, failed = 0;
            string notes = "";
            foreach (var job in jobs)
            {
                token.ThrowIfCancellationRequested();
                var r = Baker.Bake(gameDir, job, msg => Dispatcher.UIThread.Post(() =>
                {
                    SetStatus(msg);
                    if (_bakeStatus != null) _bakeStatus.Text = msg;
                }), token);
                baked += r.Baked; skipped += r.Skipped; failed += r.Failed;
                if (r.Note.Length > 0) notes += " " + r.Note;
            }
            Baker.Prune(gameDir, jobs.Select(j => j.Key));
            return (baked, skipped, failed, notes);
        }, token).ContinueWith(t => Dispatcher.UIThread.Post(() =>
        {
            _bakeCts = null;
            VerifyBar.IsVisible = false;
            if (_bakeBar != null) _bakeBar.IsVisible = false;
            if (_bakeButton != null) _bakeButton.IsEnabled = true;
            if (_bakeCancel != null) _bakeCancel.IsVisible = false;
            if (t.IsCanceled) SetStatus(T("bake.cancelled"));
            else if (t.IsFaulted) SetStatus(F("bake.failed", t.Exception?.GetBaseException().Message));
            else
            {
                var (baked, skipped, failed, notes) = t.Result;
                SetStatus(F("bake.done", baked, skipped, failed, (int)(DateTime.UtcNow - started).TotalSeconds) + notes);
            }
            if (_bakeStatus != null) _bakeStatus.Text = BakeSummary() + "\n" + StatusText.Text;
        }));
    }
}
