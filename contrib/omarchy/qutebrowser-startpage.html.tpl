<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>~ · qutebrowser</title>
    <style>
        :root {
            --bg: {{ background }};
            --bg-trans: rgba({{ background_rgb }}, 0.85);
            --dark-bg: {{ dark_background }};
            --darker-bg: {{ darker_background }};
            --lighter-bg: {{ lighter_background }};
            --fg: {{ foreground }};
            --muted: {{ muted }};
            --accent: {{ accent }};
            --accent-rgb: {{ accent_rgb }};
            --red: {{ red }};
            --green: {{ green }};
            --yellow: {{ yellow }};
            --blue: {{ blue }};
            --magenta: {{ magenta }};
            --cyan: {{ cyan }};
            --selection: {{ selection_background }};
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: transparent;
            color: var(--fg);
            font-family: 'JetBrains Mono', monospace;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 2rem;
            user-select: none;
            overflow-x: hidden;
        }

        .container {
            width: 100%;
            max-width: 820px;
            background: var(--bg-trans);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4);
            overflow: hidden;
            animation: fadeIn 0.3s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Titlebar */
        .titlebar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.75rem 1.25rem;
            background: rgba({{ darker_background_rgb }}, 0.6);
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            font-size: 0.8rem;
        }

        .dots {
            display: flex;
            gap: 6px;
        }

        .dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }

        .dot-red { background: var(--red); }
        .dot-yellow { background: var(--yellow); }
        .dot-green { background: var(--green); }

        .titlebar-text {
            color: var(--muted);
            font-size: 0.75rem;
            letter-spacing: 0.05em;
        }

        .titlebar-badge {
            color: var(--accent);
            background: rgba({{ accent_rgb }}, 0.12);
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.7rem;
            font-weight: 600;
        }

        /* Main Body */
        .content {
            padding: 2.5rem 2rem 2rem;
            display: flex;
            flex-direction: column;
            gap: 2rem;
        }

        /* Header */
        .header {
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
            padding-bottom: 1.5rem;
        }

        .prompt {
            color: var(--green);
            font-size: 0.95rem;
            margin-bottom: 0.4rem;
        }

        .prompt span {
            color: var(--accent);
        }

        .clock {
            font-size: 2.4rem;
            font-weight: 700;
            color: var(--fg);
            letter-spacing: -0.02em;
            line-height: 1;
        }

        .date {
            color: var(--muted);
            font-size: 0.85rem;
            margin-top: 0.35rem;
        }

        .tagline {
            text-align: right;
            color: var(--muted);
            font-size: 0.8rem;
        }

        .tagline-accent {
            color: var(--accent);
            font-weight: 600;
        }

        /* Search Bar */
        .search-container {
            position: relative;
        }

        .search-box {
            width: 100%;
            background: rgba({{ darker_background_rgb }}, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 0.9rem 1.25rem 0.9rem 3rem;
            color: var(--fg);
            font-family: inherit;
            font-size: 0.95rem;
            outline: none;
            transition: all 0.2s ease;
        }

        .search-box:focus {
            border-color: var(--accent);
            box-shadow: 0 0 0 2px rgba({{ accent_rgb }}, 0.2);
            background: rgba({{ darker_background_rgb }}, 0.9);
        }

        .search-icon {
            position: absolute;
            left: 1.1rem;
            top: 50%;
            transform: translateY(-50%);
            color: var(--accent);
            font-size: 1rem;
            pointer-events: none;
        }

        /* Quick Links Grid */
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 0.75rem;
        }

        .card {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.85rem 1rem;
            background: rgba({{ dark_background_rgb }}, 0.5);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            text-decoration: none;
            color: var(--fg);
            transition: all 0.2s ease;
        }

        .card:hover {
            background: rgba({{ lighter_background_rgb }}, 0.5);
            border-color: var(--accent);
            transform: translateY(-2px);
        }

        .card-icon {
            font-size: 1.1rem;
            color: var(--accent);
        }

        .card-info {
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .card-title {
            font-size: 0.85rem;
            font-weight: 600;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .card-key {
            font-size: 0.7rem;
            color: var(--muted);
        }

        /* Keybindings cheatsheet */
        .cheatsheet {
            background: rgba({{ darker_background_rgb }}, 0.4);
            border-radius: 8px;
            padding: 1rem 1.25rem;
            font-size: 0.78rem;
            color: var(--muted);
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 0.6rem 1.5rem;
            border: 1px dashed rgba(255, 255, 255, 0.08);
        }

        .cheat-item {
            display: flex;
            justify-content: space-between;
        }

        .cheat-key {
            color: var(--yellow);
            font-weight: 600;
        }

        .cheat-desc {
            color: var(--fg);
        }
    </style>
</head>
<body>

    <div class="container">
        <!-- Titlebar -->
        <div class="titlebar">
            <div class="dots">
                <span class="dot dot-red"></span>
                <span class="dot dot-yellow"></span>
                <span class="dot dot-green"></span>
            </div>
            <div class="titlebar-text">qutebrowser // omarchy linux</div>
            <div class="titlebar-badge">{{ mode }}</div>
        </div>

        <div class="content">
            <!-- Header -->
            <div class="header">
                <div>
                    <div class="prompt">mush@omarchy:~$ <span>open</span></div>
                    <div class="clock" id="clock">00:00</div>
                    <div class="date" id="date">Loading...</div>
                </div>
                <div class="tagline">
                    <span class="tagline-accent">Vim-driven Wayland Web</span><br>
                    Hyprland + QtWebEngine
                </div>
            </div>

            <!-- Search Form -->
            <form action="https://duckduckgo.com/" method="GET" class="search-container" id="search-form">
                <span class="search-icon">❯</span>
                <input 
                    type="text" 
                    name="q" 
                    id="search-input" 
                    class="search-box" 
                    placeholder="Search or enter URL... (or press 'o' in qutebrowser)" 
                    autocomplete="off" 
                    autofocus
                />
            </form>

            <!-- Bookmarks Grid -->
            <div class="grid">
                <a href="https://github.com/m7sh" class="card">
                    <span class="card-icon"></span>
                    <div class="card-info">
                        <span class="card-title">GitHub (m7sh)</span>
                        <span class="card-key">:open gh</span>
                    </div>
                </a>

                <a href="https://wiki.archlinux.org/" class="card">
                    <span class="card-icon">󰣇</span>
                    <div class="card-info">
                        <span class="card-title">ArchWiki</span>
                        <span class="card-key">:open aw</span>
                    </div>
                </a>

                <a href="https://youtube.com/" class="card">
                    <span class="card-icon">󰗃</span>
                    <div class="card-info">
                        <span class="card-title">YouTube</span>
                        <span class="card-key">:open yt</span>
                    </div>
                </a>

                <a href="https://reddit.com/r/unixporn" class="card">
                    <span class="card-icon"></span>
                    <div class="card-info">
                        <span class="card-title">r/unixporn</span>
                        <span class="card-key">:open r/unixporn</span>
                    </div>
                </a>

                <a href="https://m7sh.github.io/m7sh/" class="card">
                    <span class="card-icon">󰸌</span>
                    <div class="card-info">
                        <span class="card-title">Portfolio</span>
                        <span class="card-key">m7sh.github.io</span>
                    </div>
                </a>

                <a href="https://omarchy.org/" class="card">
                    <span class="card-icon">󰣆</span>
                    <div class="card-info">
                        <span class="card-title">Omarchy</span>
                        <span class="card-key">omarchy.org</span>
                    </div>
                </a>
            </div>

            <!-- Cheatsheet -->
            <div class="cheatsheet">
                <div class="cheat-item"><span class="cheat-key">o / O</span> <span class="cheat-desc">Open URL / new tab</span></div>
                <div class="cheat-item"><span class="cheat-key">f / F</span> <span class="cheat-desc">Follow link hints</span></div>
                <div class="cheat-item"><span class="cheat-key">d / u</span> <span class="cheat-desc">Close / restore tab</span></div>
                <div class="cheat-item"><span class="cheat-key">J / K</span> <span class="cheat-desc">Prev / next tab</span></div>
                <div class="cheat-item"><span class="cheat-key">M</span> <span class="cheat-desc">Stream video in MPV</span></div>
                <div class="cheat-item"><span class="cheat-key">td</span> <span class="cheat-desc">Toggle dark mode</span></div>
                <div class="cheat-item"><span class="cheat-key">tt / ts</span> <span class="cheat-desc">Toggle tabs / statusbar</span></div>
                <div class="cheat-item"><span class="cheat-key">tr</span> <span class="cheat-desc">Reload config / theme</span></div>
            </div>
        </div>
    </div>

    <script>
        function updateTime() {
            const now = new Date();
            const hours = String(now.getHours()).padStart(2, '0');
            const minutes = String(now.getMinutes()).padStart(2, '0');
            document.getElementById('clock').textContent = `${hours}:${minutes}`;

            const options = { weekday: 'long', month: 'short', day: 'numeric', year: 'numeric' };
            document.getElementById('date').textContent = now.toLocaleDateString(undefined, options);
        }

        updateTime();
        setInterval(updateTime, 1000);

        // Quick search handler
        const form = document.getElementById('search-form');
        const input = document.getElementById('search-input');
        form.addEventListener('submit', (e) => {
            const val = input.value.trim();
            if (!val) {
                e.preventDefault();
                return;
            }
            if (val.startsWith('http://') || val.startsWith('https://') || (val.includes('.') && !val.includes(' '))) {
                e.preventDefault();
                window.location.href = val.startsWith('http') ? val : 'https://' + val;
            }
        });
    </script>
</body>
</html>
