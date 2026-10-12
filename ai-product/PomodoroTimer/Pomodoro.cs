// =====================================================================
//  番茄时钟 Pomodoro Timer — Windows 桌面版
//  无需登录 · 不联网 · 数据仅保存在本地 (%APPDATA%\PomodoroTimer)
//  开机自启: HKCU\Software\Microsoft\Windows\CurrentVersion\Run
//  编译: 运行 build.bat（使用系统自带 .NET Framework 编译器，无任何依赖）
// =====================================================================
using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.IO;
using System.Media;
using System.Runtime.InteropServices;
using System.Text;
using System.Windows.Forms;
using Microsoft.Win32;

namespace PomodoroTimer
{
    internal enum Phase { Work, ShortBreak, LongBreak }

    internal static class Program
    {
        [STAThread]
        private static void Main()
        {
            try { NativeMethods.SetProcessDPIAware(); } catch { }
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new MainForm());
        }
    }

    internal static class NativeMethods
    {
        [DllImport("user32.dll")] public static extern bool ReleaseCapture();
        [DllImport("user32.dll")] public static extern int SendMessage(IntPtr hWnd, int msg, IntPtr wParam, IntPtr lParam);
        [DllImport("user32.dll")] public static extern bool DestroyIcon(IntPtr hIcon);
        [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
        public const int WM_NCLBUTTONDOWN = 0xA1;
        public const int HTCAPTION = 0x2;
    }

    // ---------------- 主题 ----------------
    internal static class Theme
    {
        public static readonly Color Bg = Color.FromArgb(27, 30, 40);
        public static readonly Color BgLight = Color.FromArgb(45, 50, 66);
        public static readonly Color Hover = Color.FromArgb(58, 64, 84);
        public static readonly Color Pressed = Color.FromArgb(70, 77, 100);
        public static readonly Color Text = Color.FromArgb(236, 238, 244);
        public static readonly Color TextDim = Color.FromArgb(148, 153, 170);

        public static Color Accent(Phase p)
        {
            if (p == Phase.Work) return Color.FromArgb(255, 106, 106);
            if (p == Phase.ShortBreak) return Color.FromArgb(64, 205, 196);
            return Color.FromArgb(112, 144, 248);
        }

        public static string PhaseName(Phase p)
        {
            if (p == Phase.Work) return "专注时间";
            if (p == Phase.ShortBreak) return "短休息";
            return "长休息";
        }

        public static Font GetFont(string preferred, float size, FontStyle style)
        {
            try
            {
                using (Font probe = new Font(preferred, size, style))
                {
                    if (probe.Name == preferred) return new Font(preferred, size, style);
                }
            }
            catch { }
            return new Font("Segoe UI", size, style);
        }
    }

    internal static class Ui
    {
        public static GraphicsPath RoundRect(Rectangle r, int rad)
        {
            GraphicsPath p = new GraphicsPath();
            int d = rad * 2;
            if (r.Width <= d || r.Height <= d) { p.AddRectangle(r); return p; }
            p.AddArc(r.X, r.Y, d, d, 180, 90);
            p.AddArc(r.Right - d - 1, r.Y, d, d, 270, 90);
            p.AddArc(r.Right - d - 1, r.Bottom - d - 1, d, d, 0, 90);
            p.AddArc(r.X, r.Bottom - d - 1, d, d, 90, 90);
            p.CloseFigure();
            return p;
        }
    }

    // ---------------- 设置 ----------------
    internal class AppSettings
    {
        public int WorkMinutes = 25;
        public int ShortBreakMinutes = 5;
        public int LongBreakMinutes = 15;
        public int LongBreakEvery = 4;
        public bool AutoStartBreak = true;
        public bool AutoStartWork = false;
        public bool SoundOn = true;
        public bool AlwaysOnTop = false;
        public bool StartMinimized = false;

        public static string Dir
        {
            get { return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "PomodoroTimer"); }
        }

        private static string FilePath
        {
            get { return Path.Combine(Dir, "settings.ini"); }
        }

        private static int Clamp(int v, int lo, int hi)
        {
            if (v < lo) return lo;
            if (v > hi) return hi;
            return v;
        }

        public static AppSettings Load()
        {
            AppSettings s = new AppSettings();
            try
            {
                if (File.Exists(FilePath))
                {
                    foreach (string raw in File.ReadAllLines(FilePath))
                    {
                        string line = raw.Trim();
                        if (line.Length == 0 || line.StartsWith("#")) continue;
                        int i = line.IndexOf('=');
                        if (i <= 0) continue;
                        string k = line.Substring(0, i).Trim().ToLowerInvariant();
                        string v = line.Substring(i + 1).Trim();
                        int n; bool b;
                        if (k == "work" && int.TryParse(v, out n)) s.WorkMinutes = Clamp(n, 1, 180);
                        else if (k == "short" && int.TryParse(v, out n)) s.ShortBreakMinutes = Clamp(n, 1, 60);
                        else if (k == "long" && int.TryParse(v, out n)) s.LongBreakMinutes = Clamp(n, 1, 120);
                        else if (k == "every" && int.TryParse(v, out n)) s.LongBreakEvery = Clamp(n, 2, 8);
                        else if (k == "autobreak" && bool.TryParse(v, out b)) s.AutoStartBreak = b;
                        else if (k == "autowork" && bool.TryParse(v, out b)) s.AutoStartWork = b;
                        else if (k == "sound" && bool.TryParse(v, out b)) s.SoundOn = b;
                        else if (k == "topmost" && bool.TryParse(v, out b)) s.AlwaysOnTop = b;
                        else if (k == "minimized" && bool.TryParse(v, out b)) s.StartMinimized = b;
                    }
                }
            }
            catch { }
            return s;
        }

        public void Save()
        {
            try
            {
                Directory.CreateDirectory(Dir);
                StringBuilder sb = new StringBuilder();
                sb.AppendLine("# PomodoroTimer settings");
                sb.AppendLine("work=" + WorkMinutes);
                sb.AppendLine("short=" + ShortBreakMinutes);
                sb.AppendLine("long=" + LongBreakMinutes);
                sb.AppendLine("every=" + LongBreakEvery);
                sb.AppendLine("autobreak=" + AutoStartBreak);
                sb.AppendLine("autowork=" + AutoStartWork);
                sb.AppendLine("sound=" + SoundOn);
                sb.AppendLine("topmost=" + AlwaysOnTop);
                sb.AppendLine("minimized=" + StartMinimized);
                File.WriteAllText(FilePath, sb.ToString(), Encoding.UTF8);
            }
            catch { }
        }
    }

    // ---------------- 每日统计 ----------------
    internal class DailyStats
    {
        public DateTime Date = DateTime.Today;
        public int Count;

        private static string FilePath
        {
            get { return Path.Combine(AppSettings.Dir, "stats.ini"); }
        }

        public static DailyStats Load()
        {
            DailyStats st = new DailyStats();
            try
            {
                if (File.Exists(FilePath))
                {
                    foreach (string raw in File.ReadAllLines(FilePath))
                    {
                        string line = raw.Trim();
                        int i = line.IndexOf('=');
                        if (i <= 0) continue;
                        string k = line.Substring(0, i).Trim().ToLowerInvariant();
                        string v = line.Substring(i + 1).Trim();
                        if (k == "date")
                        {
                            DateTime d;
                            if (DateTime.TryParseExact(v, "yyyy-MM-dd",
                                System.Globalization.CultureInfo.InvariantCulture,
                                System.Globalization.DateTimeStyles.None, out d))
                                st.Date = d;
                        }
                        else if (k == "count")
                        {
                            int c;
                            if (int.TryParse(v, out c) && c >= 0) st.Count = c;
                        }
                    }
                }
            }
            catch { }
            if (st.Date != DateTime.Today) st.Count = 0;
            return st;
        }

        public void Save()
        {
            Date = DateTime.Today;
            try
            {
                Directory.CreateDirectory(AppSettings.Dir);
                File.WriteAllText(FilePath,
                    "date=" + Date.ToString("yyyy-MM-dd") + "\r\ncount=" + Count + "\r\n",
                    Encoding.UTF8);
            }
            catch { }
        }
    }

    // ---------------- 开机自启（当前用户注册表） ----------------
    internal static class AutoStart
    {
        private const string KeyPath = "Software\\Microsoft\\Windows\\CurrentVersion\\Run";
        private const string Name = "PomodoroTimer";

        public static bool IsEnabled()
        {
            try
            {
                using (RegistryKey k = Registry.CurrentUser.OpenSubKey(KeyPath, false))
                {
                    if (k == null) return false;
                    return k.GetValue(Name) != null;
                }
            }
            catch { return false; }
        }

        public static void SetEnabled(bool on, string exePath)
        {
            try
            {
                using (RegistryKey k = Registry.CurrentUser.CreateSubKey(KeyPath))
                {
                    if (k == null) return;
                    if (on) k.SetValue(Name, "\"" + exePath + "\"");
                    else if (k.GetValue(Name) != null) k.DeleteValue(Name);
                }
            }
            catch { }
        }
    }

    // ---------------- 提示音（代码合成，无需音频文件） ----------------
    internal static class Chime
    {
        private static SoundPlayer _player;

        public static void Play()
        {
            try
            {
                if (_player == null) _player = Build();
                _player.Play(); // 异步播放
            }
            catch { }
        }

        private static SoundPlayer Build()
        {
            int rate = 44100;
            // G5 -> B5 -> D6 琶音，柔和三连音
            double[] freqs = { 784.0, 988.0, 1319.0 };
            double[] starts = { 0.0, 0.18, 0.36 };
            double noteLen = 0.5;
            double total = 1.4;
            int n = (int)(total * rate);
            MemoryStream ms = new MemoryStream(44 + n * 2);
            BinaryWriter w = new BinaryWriter(ms);
            w.Write(Encoding.ASCII.GetBytes("RIFF"));
            w.Write(36 + n * 2);
            w.Write(Encoding.ASCII.GetBytes("WAVE"));
            w.Write(Encoding.ASCII.GetBytes("fmt "));
            w.Write(16);
            w.Write((short)1);
            w.Write((short)1);
            w.Write(rate);
            w.Write(rate * 2);
            w.Write((short)2);
            w.Write((short)16);
            w.Write(Encoding.ASCII.GetBytes("data"));
            w.Write(n * 2);
            for (int i = 0; i < n; i++)
            {
                double t = (double)i / rate;
                double s = 0.0;
                for (int j = 0; j < freqs.Length; j++)
                {
                    double dt = t - starts[j];
                    if (dt >= 0 && dt < noteLen)
                    {
                        double env = Math.Exp(-3.2 * dt / noteLen);
                        if (dt < 0.012) env *= dt / 0.012;
                        s += 0.30 * env * Math.Sin(2.0 * Math.PI * freqs[j] * dt);
                    }
                }
                if (s > 1.0) s = 1.0;
                if (s < -1.0) s = -1.0;
                w.Write((short)(s * 32767.0));
            }
            w.Flush();
            return new SoundPlayer(ms);
        }
    }

    // ---------------- 应用图标（代码绘制的番茄） ----------------
    internal static class AppIcon
    {
        public static Bitmap BitmapOf(int size)
        {
            Bitmap b = new Bitmap(size, size);
            using (Graphics g = Graphics.FromImage(b))
            {
                DrawTomato(g, size);
            }
            return b;
        }

        public static Icon Make(int size)
        {
            using (Bitmap b = BitmapOf(size))
            {
                IntPtr h = b.GetHicon();
                Icon clone = (Icon)Icon.FromHandle(h).Clone();
                try { NativeMethods.DestroyIcon(h); } catch { }
                return clone;
            }
        }

        public static void DrawTomato(Graphics g, int size)
        {
            g.SmoothingMode = SmoothingMode.AntiAlias;
            float u = size / 32f;
            using (SolidBrush red = new SolidBrush(Color.FromArgb(235, 87, 74)))
                g.FillEllipse(red, 4f * u, 9f * u, 24f * u, 20f * u);
            using (SolidBrush shine = new SolidBrush(Color.FromArgb(60, 255, 255, 255)))
                g.FillEllipse(shine, 9f * u, 13f * u, 6f * u, 4f * u);
            using (Pen stem = new Pen(Color.FromArgb(94, 138, 62), 2.2f * u))
            {
                stem.StartCap = LineCap.Round;
                stem.EndCap = LineCap.Round;
                g.DrawLine(stem, 16f * u, 10f * u, 16f * u, 5f * u);
            }
            using (SolidBrush leaf = new SolidBrush(Color.FromArgb(102, 170, 80)))
            {
                g.FillEllipse(leaf, 10.5f * u, 3.6f * u, 7f * u, 4f * u);
                g.FillEllipse(leaf, 14.5f * u, 2.8f * u, 7f * u, 4f * u);
            }
        }
    }

    // ---------------- 基础控件 ----------------
    internal class RoundedForm : Form
    {
        public int CornerRadius = 18;

        public RoundedForm()
        {
            FormBorderStyle = FormBorderStyle.None;
            StartPosition = FormStartPosition.CenterParent;
            BackColor = Theme.Bg;
            ForeColor = Theme.Text;
            DoubleBuffered = true;
        }

        protected override void OnResize(EventArgs e)
        {
            base.OnResize(e);
            UpdateRegion();
        }

        protected override void OnHandleCreated(EventArgs e)
        {
            base.OnHandleCreated(e);
            UpdateRegion();
        }

        protected void UpdateRegion()
        {
            if (Width <= 0 || Height <= 0) return;
            using (GraphicsPath p = Ui.RoundRect(new Rectangle(0, 0, Width, Height), CornerRadius))
            {
                Region = new Region(p);
            }
        }

        protected void MakeDraggable(Control c)
        {
            c.MouseDown += OnDragMouseDown;
        }

        private void OnDragMouseDown(object sender, MouseEventArgs e)
        {
            if (e.Button == MouseButtons.Left)
            {
                NativeMethods.ReleaseCapture();
                NativeMethods.SendMessage(Handle, NativeMethods.WM_NCLBUTTONDOWN,
                    (IntPtr)NativeMethods.HTCAPTION, IntPtr.Zero);
            }
        }
    }

    internal class TitleBarButton : Control
    {
        public bool IsClose;
        private bool _hover;

        public TitleBarButton()
        {
            SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.OptimizedDoubleBuffer |
                ControlStyles.UserPaint | ControlStyles.ResizeRedraw, true);
            Cursor = Cursors.Default;
            Font = new Font("Segoe UI", 10F);
            Size = new Size(42, 34);
            Text = "";
        }

        protected override void OnMouseEnter(EventArgs e) { _hover = true; Invalidate(); base.OnMouseEnter(e); }
        protected override void OnMouseLeave(EventArgs e) { _hover = false; Invalidate(); base.OnMouseLeave(e); }

        protected override void OnPaint(PaintEventArgs e)
        {
            base.OnPaint(e);
            Color bg = _hover ? (IsClose ? Color.FromArgb(232, 17, 35) : Theme.Hover) : Theme.Bg;
            using (SolidBrush b = new SolidBrush(bg)) e.Graphics.FillRectangle(b, ClientRectangle);
            TextRenderer.DrawText(e.Graphics, Text, Font, ClientRectangle,
                (_hover && IsClose) ? Color.White : Theme.TextDim,
                TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter | TextFormatFlags.NoPrefix);
        }
    }

    internal class FlatButton : Control
    {
        public Color NormalColor = Theme.BgLight;
        public Color HoverColor = Theme.Hover;
        public Color PressedColor = Theme.Pressed;
        public Color TextColor = Theme.Text;
        public int Radius = 13;
        private bool _hover, _down;

        public FlatButton()
        {
            SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.OptimizedDoubleBuffer |
                ControlStyles.UserPaint | ControlStyles.ResizeRedraw | ControlStyles.SupportsTransparentBackColor, true);
            Cursor = Cursors.Hand;
            Font = new Font("Segoe UI", 11F);
        }

        protected override void OnMouseEnter(EventArgs e) { _hover = true; Invalidate(); base.OnMouseEnter(e); }
        protected override void OnMouseLeave(EventArgs e) { _hover = false; _down = false; Invalidate(); base.OnMouseLeave(e); }
        protected override void OnMouseDown(MouseEventArgs e) { _down = true; Invalidate(); base.OnMouseDown(e); }
        protected override void OnMouseUp(MouseEventArgs e) { _down = false; Invalidate(); base.OnMouseUp(e); }

        protected override void OnPaint(PaintEventArgs e)
        {
            base.OnPaint(e);
            e.Graphics.SmoothingMode = SmoothingMode.AntiAlias;
            using (GraphicsPath p = Ui.RoundRect(ClientRectangle, Radius))
            using (SolidBrush b = new SolidBrush(_down ? PressedColor : (_hover ? HoverColor : NormalColor)))
                e.Graphics.FillPath(b, p);
            TextRenderer.DrawText(e.Graphics, Text, Font, ClientRectangle, TextColor,
                TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter | TextFormatFlags.NoPrefix);
        }
    }

    internal class RingControl : Control
    {
        public float Progress;                       // 0..1 已流逝比例
        public Color RingBaseColor = Color.FromArgb(48, 53, 70);
        public Color RingColor = Color.FromArgb(255, 106, 106);
        public float Stroke = 10f;

        public RingControl()
        {
            SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.OptimizedDoubleBuffer |
                ControlStyles.UserPaint | ControlStyles.ResizeRedraw | ControlStyles.SupportsTransparentBackColor, true);
            BackColor = Color.Transparent;
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            base.OnPaint(e);
            Graphics g = e.Graphics;
            g.SmoothingMode = SmoothingMode.AntiAlias;
            float pad = Stroke / 2f + 2f;
            RectangleF rect = new RectangleF(pad, pad, Width - pad * 2f, Height - pad * 2f);
            using (Pen bp = new Pen(RingBaseColor, Stroke))
            {
                bp.StartCap = LineCap.Round;
                bp.EndCap = LineCap.Round;
                g.DrawArc(bp, rect, 0, 180);
                g.DrawArc(bp, rect, 180, 180);
            }
            float f = Progress;
            if (f < 0f) f = 0f;
            if (f > 1f) f = 1f;
            if (f > 0.002f)
            {
                using (Pen p = new Pen(RingColor, Stroke))
                {
                    p.StartCap = LineCap.Round;
                    p.EndCap = LineCap.Round;
                    g.DrawArc(p, rect, -90f, 359.9f * f);
                }
                double ang = (-90.0 + 359.9 * f) * Math.PI / 180.0;
                float cx = rect.X + rect.Width / 2f;
                float cy = rect.Y + rect.Height / 2f;
                float r = rect.Width / 2f;
                float px = (float)(cx + r * Math.Cos(ang));
                float py = (float)(cy + r * Math.Sin(ang));
                using (SolidBrush db = new SolidBrush(RingColor))
                    g.FillEllipse(db, px - Stroke / 2f, py - Stroke / 2f, Stroke, Stroke);
            }
        }
    }

    // ---------------- 主窗口 ----------------
    internal class MainForm : RoundedForm
    {
        private readonly AppSettings _settings = AppSettings.Load();
        private readonly DailyStats _stats = DailyStats.Load();
        private readonly System.Windows.Forms.Timer _tick = new System.Windows.Forms.Timer();

        private Phase _phase = Phase.Work;
        private TimeSpan _duration, _remaining;
        private DateTime _phaseEnd;
        private bool _running;
        private int _cyclePos;                 // 当前周期已完成的番茄数
        private bool _reallyExit, _hiddenTipShown;

        private RingControl _ring;
        private Label _phaseLabel, _timeLabel, _roundLabel, _todayLabel, _hintLabel, _titleLabel;
        private FlatButton _startBtn, _skipBtn, _resetBtn;
        private TitleBarButton _closeBtn, _minBtn, _gearBtn;
        private NotifyIcon _tray;
        private ToolStripMenuItem _trayStartItem;

        public MainForm()
        {
            Text = "番茄时钟";
            ClientSize = new Size(380, 520);
            StartPosition = FormStartPosition.CenterScreen;
            ShowInTaskbar = true;
            TopMost = _settings.AlwaysOnTop;
            Icon = AppIcon.Make(32);
            Font = Theme.GetFont("Segoe UI", 9.5F, FontStyle.Regular);

            BuildUi();
            BuildTray();

            _duration = PhaseDuration(_phase);
            _remaining = _duration;

            _tick.Interval = 200;
            _tick.Tick += OnTick;

            UpdateAll();
        }

        private void BuildUi()
        {
            // ---- 标题栏 ----
            PictureBox logo = new PictureBox();
            logo.BackColor = Color.Transparent;
            logo.Image = AppIcon.BitmapOf(24);
            logo.SizeMode = PictureBoxSizeMode.Zoom;
            logo.Location = new Point(18, 11);
            logo.Size = new Size(24, 24);
            Controls.Add(logo);
            MakeDraggable(logo);

            _titleLabel = new Label();
            _titleLabel.Text = "番茄时钟";
            _titleLabel.Bounds = new Rectangle(52, 12, 160, 24);
            _titleLabel.BackColor = Color.Transparent;
            _titleLabel.ForeColor = Theme.Text;
            _titleLabel.Font = Theme.GetFont("Segoe UI", 11.5F, FontStyle.Regular);
            _titleLabel.TextAlign = ContentAlignment.MiddleLeft;
            Controls.Add(_titleLabel);
            MakeDraggable(_titleLabel);

            _gearBtn = new TitleBarButton();
            _gearBtn.Text = "⚙";
            _gearBtn.Font = new Font("Segoe UI Symbol", 11F);
            _gearBtn.Bounds = new Rectangle(ClientSize.Width - 130, 6, 42, 34);
            _gearBtn.Click += delegate { OpenSettings(); };
            Controls.Add(_gearBtn);

            _minBtn = new TitleBarButton();
            _minBtn.Text = "—";
            _minBtn.Bounds = new Rectangle(ClientSize.Width - 88, 6, 42, 34);
            _minBtn.Click += delegate { WindowState = FormWindowState.Minimized; };
            Controls.Add(_minBtn);

            _closeBtn = new TitleBarButton();
            _closeBtn.Text = "✕";
            _closeBtn.IsClose = true;
            _closeBtn.Bounds = new Rectangle(ClientSize.Width - 46, 6, 42, 34);
            _closeBtn.Click += delegate { Close(); };
            Controls.Add(_closeBtn);

            // ---- 圆环 + 中央文字 ----
            _ring = new RingControl();
            _ring.Bounds = new Rectangle(70, 96, 240, 240);
            Controls.Add(_ring);

            _phaseLabel = MakeLabel("专注时间", 20, 60, 200, 30, true, _ring);
            _phaseLabel.Font = Theme.GetFont("Segoe UI", 13F, FontStyle.Regular);

            _timeLabel = MakeLabel("25:00", 20, 92, 200, 84, false, _ring);
            _timeLabel.Font = Theme.GetFont("Segoe UI Light", 46F, FontStyle.Regular);

            _roundLabel = MakeLabel("第 1 / 4 个番茄", 20, 182, 200, 26, true, _ring);
            _roundLabel.Font = Theme.GetFont("Segoe UI", 9.5F, FontStyle.Regular);

            // ---- 按钮区 ----
            _skipBtn = MakeFlat("跳过", 22, 372, 106, 48);
            _skipBtn.TextColor = Theme.TextDim;

            _startBtn = MakeFlat("开始", 137, 366, 106, 60);
            _startBtn.TextColor = Color.White;
            _startBtn.Font = Theme.GetFont("Segoe UI", 12F, FontStyle.Regular);

            _resetBtn = MakeFlat("重置", 252, 372, 106, 48);
            _resetBtn.TextColor = Theme.TextDim;

            _startBtn.Click += delegate { ToggleStart(); };
            _skipBtn.Click += delegate { Skip(); };
            _resetBtn.Click += delegate { ResetPhase(); };

            // ---- 底部信息 ----
            _todayLabel = MakeLabel("今天已完成 0 个番茄 🍅", 0, 452, 380, 26, true);
            _todayLabel.Font = Theme.GetFont("Segoe UI", 10F, FontStyle.Regular);

            _hintLabel = MakeLabel("空格 开始/暂停  ·  R 重置  ·  S 跳过", 0, 480, 380, 20, true);
            _hintLabel.Font = Theme.GetFont("Segoe UI", 8.5F, FontStyle.Regular);
        }

        private Label MakeLabel(string text, int x, int y, int w, int h, bool dim)
        {
            return MakeLabel(text, x, y, w, h, dim, this);
        }

        private Label MakeLabel(string text, int x, int y, int w, int h, bool dim, Control parent)
        {
            Label l = new Label();
            l.Text = text;
            l.Bounds = new Rectangle(x, y, w, h);
            l.BackColor = Color.Transparent;
            l.ForeColor = dim ? Theme.TextDim : Theme.Text;
            l.TextAlign = ContentAlignment.MiddleCenter;
            parent.Controls.Add(l);
            return l;
        }

        private FlatButton MakeFlat(string text, int x, int y, int w, int h)
        {
            FlatButton b = new FlatButton();
            b.Text = text;
            b.Bounds = new Rectangle(x, y, w, h);
            b.ForeColor = Theme.Text;
            Controls.Add(b);
            return b;
        }

        private void BuildTray()
        {
            _tray = new NotifyIcon();
            _tray.Icon = AppIcon.Make(16);
            _tray.Text = "番茄时钟";
            _tray.Visible = true;
            _tray.DoubleClick += delegate { ShowFromTray(); };

            ContextMenuStrip m = new ContextMenuStrip();
            m.Items.Add("显示主窗口", null, delegate { ShowFromTray(); });
            m.Items.Add(new ToolStripSeparator());
            _trayStartItem = new ToolStripMenuItem("开始 / 暂停");
            _trayStartItem.Click += delegate { ToggleStart(); };
            m.Items.Add(_trayStartItem);
            m.Items.Add("重置", null, delegate { ResetPhase(); });
            m.Items.Add("跳过", null, delegate { Skip(); });
            m.Items.Add(new ToolStripSeparator());
            m.Items.Add("设置...", null, delegate { OpenSettings(); });
            m.Items.Add(new ToolStripSeparator());
            m.Items.Add("退出", null, delegate { ExitApp(); });
            _tray.ContextMenuStrip = m;
        }

        // ---------------- 计时核心 ----------------
        private TimeSpan PhaseDuration(Phase p)
        {
            if (p == Phase.Work) return TimeSpan.FromMinutes(Math.Max(1, _settings.WorkMinutes));
            if (p == Phase.ShortBreak) return TimeSpan.FromMinutes(Math.Max(1, _settings.ShortBreakMinutes));
            return TimeSpan.FromMinutes(Math.Max(1, _settings.LongBreakMinutes));
        }

        private void ToggleStart()
        {
            if (_running) Pause(); else Start();
            UpdateAll();
        }

        private void Start()
        {
            if (_remaining <= TimeSpan.Zero || _remaining > _duration) _remaining = _duration;
            _phaseEnd = DateTime.Now + _remaining;
            _running = true;
            _tick.Start();
        }

        private void Pause()
        {
            _remaining = _phaseEnd - DateTime.Now;
            if (_remaining < TimeSpan.Zero) _remaining = TimeSpan.Zero;
            _running = false;
            _tick.Stop();
        }

        private void ResetPhase()
        {
            _running = false;
            _tick.Stop();
            _remaining = _duration;
            UpdateAll();
        }

        private void Skip() { Advance(false); }

        private void OnTick(object sender, EventArgs e)
        {
            if (!_running) return;
            _remaining = _phaseEnd - DateTime.Now;
            if (_remaining <= TimeSpan.Zero)
            {
                CompletePhase();
                return;
            }
            UpdateTimeOnly();
        }

        private void CompletePhase()
        {
            bool wasWork = (_phase == Phase.Work);
            if (wasWork)
            {
                _stats.Count++;
                _stats.Save();
                _cyclePos++;
            }
            NotifyDone(wasWork);
            Advance(true);
        }

        private void Advance(bool completed)
        {
            if (_phase == Phase.Work)
            {
                // completed 时 _cyclePos 已在 CompletePhase 中自增
                Phase next = (_cyclePos >= _settings.LongBreakEvery) ? Phase.LongBreak : Phase.ShortBreak;
                EnterPhase(next, _settings.AutoStartBreak);
            }
            else
            {
                if (_phase == Phase.LongBreak) _cyclePos = 0;
                EnterPhase(Phase.Work, _settings.AutoStartWork);
            }
        }

        private void EnterPhase(Phase p, bool autoStart)
        {
            _phase = p;
            _duration = PhaseDuration(p);
            _remaining = _duration;
            if (autoStart) Start();
            else { _running = false; _tick.Stop(); }
            UpdateAll();
        }

        private void NotifyDone(bool wasWork)
        {
            if (_settings.SoundOn) Chime.Play();
            try
            {
                _tray.BalloonTipTitle = wasWork ? "🍅 专注完成！" : "☀️ 休息结束";
                _tray.BalloonTipText = wasWork
                    ? string.Format("完成一个 {0} 分钟的番茄，起来走走吧～", _settings.WorkMinutes)
                    : "准备好开始下一个番茄了吗？";
                _tray.BalloonTipIcon = ToolTipIcon.Info;
                _tray.ShowBalloonTip(3000);
            }
            catch { }
        }

        // ---------------- 界面刷新 ----------------
        private void UpdateAll()
        {
            Color acc = Theme.Accent(_phase);
            _ring.RingColor = acc;
            _ring.Invalidate();

            bool started = _remaining < _duration - TimeSpan.FromMilliseconds(50);
            string phaseText = Theme.PhaseName(_phase);
            if (!_running && started) phaseText += " · 已暂停";
            _phaseLabel.Text = phaseText;
            _phaseLabel.ForeColor = acc;

            _startBtn.NormalColor = acc;
            _startBtn.HoverColor = ControlPaint.Light(acc, 0.18f);
            _startBtn.PressedColor = ControlPaint.Dark(acc, 0.05f);
            _startBtn.Text = _running ? "暂停" : (started ? "继续" : "开始");
            _startBtn.Invalidate();

            UpdateTimeOnly();
        }

        private void UpdateTimeOnly()
        {
            long totalTicks = _duration.Ticks <= 0 ? 1 : _duration.Ticks;
            float f = (float)(1.0 - (double)_remaining.Ticks / totalTicks);
            if (f < 0f) f = 0f;
            if (f > 1f) f = 1f;
            _ring.Progress = f;
            _ring.Invalidate();

            _timeLabel.Text = FormatTime(_remaining);
            _timeLabel.ForeColor = _running ? Theme.Text : Theme.TextDim;

            int cur = (_phase == Phase.Work) ? _cyclePos + 1 : _cyclePos;
            if (cur > _settings.LongBreakEvery) cur = _settings.LongBreakEvery;
            _roundLabel.Text = (_phase == Phase.Work)
                ? string.Format("第 {0} / {1} 个番茄", cur, _settings.LongBreakEvery)
                : string.Format("本轮已完成 {0} / {1}", _cyclePos, _settings.LongBreakEvery);

            _todayLabel.Text = string.Format("今天已完成 {0} 个番茄 🍅", _stats.Count);

            string trayText = FormatTime(_remaining) + " · " + Theme.PhaseName(_phase);
            if (trayText.Length > 63) trayText = trayText.Substring(0, 63);
            _tray.Text = trayText;
            Text = trayText + " — 番茄时钟";
            if (_trayStartItem != null)
                _trayStartItem.Text = _running ? "暂停" : "开始";
        }

        private static string FormatTime(TimeSpan t)
        {
            if (t < TimeSpan.Zero) t = TimeSpan.Zero;
            int totalSec = (int)Math.Ceiling(t.TotalSeconds);
            return string.Format("{0:D2}:{1:D2}", totalSec / 60, totalSec % 60);
        }

        // ---------------- 设置 ----------------
        private void OpenSettings()
        {
            using (SettingsForm f = new SettingsForm(_settings))
            {
                if (f.ShowDialog(this) == DialogResult.OK) ApplySettings();
            }
        }

        private void ApplySettings()
        {
            TopMost = _settings.AlwaysOnTop;
            if (!_running)
            {
                bool fresh = (_duration - _remaining) < TimeSpan.FromMilliseconds(50);
                _duration = PhaseDuration(_phase);
                if (fresh) _remaining = _duration;   // 未开始的阶段直接采用新时长
            }
            if (_cyclePos > _settings.LongBreakEvery) _cyclePos = 0;
            UpdateAll();
        }

        // ---------------- 窗口/托盘行为 ----------------
        protected override void OnLoad(EventArgs e)
        {
            base.OnLoad(e);
            if (_settings.StartMinimized) Hide();
        }

        protected override void OnFormClosing(FormClosingEventArgs e)
        {
            if (!_reallyExit && e.CloseReason == CloseReason.UserClosing)
            {
                e.Cancel = true;
                Hide();
                if (!_hiddenTipShown)
                {
                    _hiddenTipShown = true;
                    try
                    {
                        _tray.BalloonTipTitle = "番茄时钟仍在运行";
                        _tray.BalloonTipText = "已最小化到系统托盘，双击图标可重新打开。";
                        _tray.BalloonTipIcon = ToolTipIcon.Info;
                        _tray.ShowBalloonTip(2500);
                    }
                    catch { }
                }
                return;
            }
            base.OnFormClosing(e);
        }

        protected override void OnFormClosed(FormClosedEventArgs e)
        {
            if (_tray != null)
            {
                _tray.Visible = false;
                _tray.Dispose();
            }
            base.OnFormClosed(e);
        }

        protected override bool ProcessCmdKey(ref Message msg, Keys keyData)
        {
            if (keyData == Keys.Space) { ToggleStart(); return true; }
            if (keyData == Keys.R) { ResetPhase(); return true; }
            if (keyData == Keys.S) { Skip(); return true; }
            return base.ProcessCmdKey(ref msg, keyData);
        }

        private void ShowFromTray()
        {
            Show();
            WindowState = FormWindowState.Normal;
            Activate();
        }

        private void ExitApp()
        {
            _reallyExit = true;
            Close();
        }
    }

    // ---------------- 设置窗口 ----------------
    internal class SettingsForm : RoundedForm
    {
        private readonly AppSettings _s;
        private NumericUpDown _numWork, _numShort, _numLong, _numEvery;
        private CheckBox _chkAutoBreak, _chkAutoWork, _chkSound, _chkTop, _chkMin, _chkAutoStart;

        public SettingsForm(AppSettings s)
        {
            _s = s;
            Text = "设置";
            ClientSize = new Size(380, 656);
            BuildUi();
        }

        private void BuildUi()
        {
            Label drag = new Label();
            drag.Bounds = new Rectangle(0, 0, ClientSize.Width, 46);
            drag.BackColor = Color.Transparent;
            drag.Text = "";
            Controls.Add(drag);
            MakeDraggable(drag);

            Label title = new Label();
            title.Text = "设置";
            title.Bounds = new Rectangle(54, 12, 200, 26);
            title.BackColor = Color.Transparent;
            title.ForeColor = Theme.Text;
            title.Font = Theme.GetFont("Segoe UI", 12.5F, FontStyle.Regular);
            Controls.Add(title);

            TitleBarButton close = new TitleBarButton();
            close.Text = "✕";
            close.IsClose = true;
            close.Bounds = new Rectangle(ClientSize.Width - 46, 6, 42, 34);
            close.Click += delegate { Close(); };
            Controls.Add(close);

            AddHeader("时长", 62);
            _numWork = AddNumRow("专注时长（分钟）", 96, _s.WorkMinutes, 1, 180);
            _numShort = AddNumRow("短休息时长（分钟）", 138, _s.ShortBreakMinutes, 1, 60);
            _numLong = AddNumRow("长休息时长（分钟）", 180, _s.LongBreakMinutes, 1, 120);
            _numEvery = AddNumRow("长休息间隔（番茄数）", 222, _s.LongBreakEvery, 2, 8);

            AddHeader("自动化与提醒", 270);
            _chkAutoBreak = AddCheck("自动开始休息", 304, _s.AutoStartBreak);
            _chkAutoWork = AddCheck("休息结束后自动开始专注", 340, _s.AutoStartWork);
            _chkSound = AddCheck("阶段结束时播放提示音", 376, _s.SoundOn);

            AddHeader("窗口与启动", 424);
            _chkTop = AddCheck("窗口始终置顶", 458, _s.AlwaysOnTop);
            _chkMin = AddCheck("启动时最小化到系统托盘", 494, _s.StartMinimized);
            _chkAutoStart = AddCheck("开机自动启动（当前用户）", 530, AutoStart.IsEnabled());

            FlatButton save = new FlatButton();
            save.Text = "保存";
            save.Bounds = new Rectangle(28, 592, 156, 48);
            save.NormalColor = Theme.Accent(Phase.Work);
            save.HoverColor = ControlPaint.Light(Theme.Accent(Phase.Work), 0.18f);
            save.TextColor = Color.White;
            save.Font = Theme.GetFont("Segoe UI", 11F, FontStyle.Regular);
            save.Click += SaveClick;
            Controls.Add(save);

            FlatButton cancel = new FlatButton();
            cancel.Text = "取消";
            cancel.Bounds = new Rectangle(196, 592, 156, 48);
            cancel.TextColor = Theme.TextDim;
            cancel.Click += delegate { Close(); };
            Controls.Add(cancel);
        }

        private void AddHeader(string text, int y)
        {
            Label h = new Label();
            h.Text = text;
            h.Bounds = new Rectangle(28, y, 300, 24);
            h.BackColor = Color.Transparent;
            h.ForeColor = Theme.TextDim;
            h.Font = Theme.GetFont("Segoe UI", 9F, FontStyle.Bold);
            Controls.Add(h);
        }

        private NumericUpDown AddNumRow(string text, int y, int val, int min, int max)
        {
            Label l = new Label();
            l.Text = text;
            l.Bounds = new Rectangle(28, y + 4, 210, 24);
            l.BackColor = Color.Transparent;
            l.ForeColor = Theme.Text;
            Controls.Add(l);

            NumericUpDown n = new NumericUpDown();
            n.Bounds = new Rectangle(248, y, 100, 30);
            n.Minimum = min;
            n.Maximum = max;
            n.Value = Math.Min(Math.Max(val, min), max);
            n.BackColor = Theme.BgLight;
            n.ForeColor = Theme.Text;
            n.BorderStyle = BorderStyle.FixedSingle;
            n.TextAlign = HorizontalAlignment.Center;
            Controls.Add(n);
            return n;
        }

        private CheckBox AddCheck(string text, int y, bool val)
        {
            CheckBox c = new CheckBox();
            c.Text = text;
            c.Bounds = new Rectangle(28, y, 320, 26);
            c.BackColor = Color.Transparent;
            c.ForeColor = Theme.Text;
            c.Checked = val;
            Controls.Add(c);
            return c;
        }

        private void SaveClick(object sender, EventArgs e)
        {
            _s.WorkMinutes = (int)_numWork.Value;
            _s.ShortBreakMinutes = (int)_numShort.Value;
            _s.LongBreakMinutes = (int)_numLong.Value;
            _s.LongBreakEvery = (int)_numEvery.Value;
            _s.AutoStartBreak = _chkAutoBreak.Checked;
            _s.AutoStartWork = _chkAutoWork.Checked;
            _s.SoundOn = _chkSound.Checked;
            _s.AlwaysOnTop = _chkTop.Checked;
            _s.StartMinimized = _chkMin.Checked;
            _s.Save();
            AutoStart.SetEnabled(_chkAutoStart.Checked, Application.ExecutablePath);
            DialogResult = DialogResult.OK;
            Close();
        }

        protected override bool ProcessCmdKey(ref Message msg, Keys keyData)
        {
            if (keyData == Keys.Escape) { Close(); return true; }
            return base.ProcessCmdKey(ref msg, keyData);
        }
    }
}
