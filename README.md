# Sanitizer Studio — Modern Desktop Edition

A 100% native, security-grade desktop application built with Python to safely sanitize sensitive logs, tokens, secrets, and IP addresses before sharing them with AI models, and accurately restore AI-generated responses back to their original values.

Designed specifically for desktop workflows with high-performance async processing, cryptographic anonymization, zero-corruption atomic storage, and ephemeral clipboard safety.

---

## 🚀 Quick Launcher

Launch the desktop app with one click using the included Windows batch file:

* **[Launch_Studio.bat](Launch_Studio.bat)** — Launches the complete **Sanitizer Studio** desktop application with Sanitize, Unsanitize, and Rules Management workspaces.

---

## 🛡️ Key Features & Architectural Highlights

### 1. Cryptographic Deterministic Synthetic Anonymization
* **Realistic Fake Lookalikes**: Instead of clumsy `<IP_1>` or `<EMAIL_1>` placeholders that can degrade AI code understanding, secrets can be swapped with realistic synthetic data:
  * IPv4 addresses $\rightarrow$ Realistic synthetic IPs (e.g., `10.214.83.19`)
  * Email addresses $\rightarrow$ Valid-looking fake emails (e.g., `user-9f4a@corp-relay.internal`)
  * UUIDs $\rightarrow$ Standard compliant v4-format UUIDs
  * Bearer Tokens $\rightarrow$ Hexadecimal synthetic tokens
* **Deterministic Output**: An identical secret always produces the exact same synthetic alias across your sessions on your machine.
* **Local Master Pepper (`.vault_pepper.key`)**: Synthetic generation uses **HMAC-SHA256** seeded by a locally generated 32-byte cryptographic pepper. Even if someone inspects the synthetic output, they cannot use precomputed rainbow tables to reverse-engineer your original values.

### 2. High-Performance Asynchronous Threading
* **Non-Blocking GUI**: Sanitization, unsanitization, regex matching, and multi-pattern leak scans run in isolated background worker threads.
* **Responsive Event Loop**: The Tkinter main thread stays completely responsive via a thread-safe `queue.Queue` message pump, eliminating Windows `(Not Responding)` lockups even when processing 5MB–50MB log dumps.

### 3. Ephemeral Clipboard Security
* **60-Second Auto-Wipe Timer**: When you copy restored, sensitive secrets from the **Unsanitize** tab, an ephemeral countdown timer appears in the status bar:
  `⏱️ Sensitive Clipboard Auto-Clears: 60s`
* **Direct Controls**: Includes live `[Keep]` (to cancel auto-wipe) and `[Clear Now]` buttons. If left untouched, the clipboard is automatically purged after 60 seconds to prevent real credentials from lingering in memory or Windows Clipboard History (`Win + V`).

### 4. Zero-Corruption Atomic File Storage
* **Crash-Proof Config Writes**: Rule saves write to an isolated PID-tagged temporary file (`replacement.json.tmp.<pid>`), force a hard disk sync via `os.fsync()`, archive a rolling `.bak` backup copy (`replacement.json.bak`), and atomically replace the active file (`os.replace`). 
* Guarantees zero 0-byte file corruptions even during sudden process termination or system power loss.

### 5. Pre-Flight Input Collision Detection
* **Input Integrity Guard**: Before processing raw text, the engine checks whether any active replacement aliases already exist in your source payload. If a collision is found, a warning banner alerts you immediately, preventing accidental double-masking or broken restoration mappings.

### 6. Industry-Grade Secret Leakage & Exposure Detection
* **Multi-Provider Signature Catalog**: Scans sanitized output for unmasked secrets across leading cloud, AI, and developer platforms:
  * **AI / LLM Keys**: OpenAI (`sk-proj-...`, `sk-...`), Anthropic Claude (`sk-ant-...`), HuggingFace (`hf_...`).
  * **Cloud & Infrastructure**: AWS Access Key ID (`AKIA...`), AWS Secret Access Key (`aws_secret_key = ...`), Google Cloud API Keys (`AIzaSy...`).
  * **Developer & SaaS**: GitHub Modern PATs (`github_pat_...`, `ghp_...`), Stripe keys (`sk_live_...`, `rk_live_...`), Slack tokens (`xoxb-...`, `xoxp-...`), SendGrid (`SG....`).
  * **Database URIs**: Sniffs embedded passwords in connection strings (`postgres://`, `mysql://`, `mongodb://`, `redis://`).
  * **Config Assignments**: Detects unmasked credentials in `.env`, JSON, or YAML assignments (`client_secret = "..."`, `db_password: "..."`).
  * **Private Keys**: Detects RSA, OPENSSH, EC, DSA, and PGP private key headers.
* **Shannon Entropy Engine**: Heuristic analysis calculates information density to identify unbranded, internal high-entropy cryptographic keys and salts ($\ge 3.8$ entropy, $\ge 22$ chars) that lack standard public prefixes.
* **Severity Tiering & Filtering**: Categorizes issues into 🔴 **CRITICAL** (Active AI/Cloud keys, DB passwords, private keys), 🟠 **HIGH** (Service tokens, JWTs, config assignments, compound partial leaks), and 🟡 **MEDIUM** (High-entropy tokens, query secrets).
* **Interactive Remediation in Inspector**:
  * **`[ ⚡ Synthetic ]`**: One-click generation of a deterministic realistic fake lookalike, automatically added to your rules and re-sanitized.
  * **`[ 🏷️ Placeholder ]`**: One-click standard `<CATEGORY>` alias generation.
  * **`[ ✕ Ignore ]`**: Dismiss false positives or accepted items for the current session.
* **Known Mask Suppression**: Automatically filters out already-masked synthetic values and placeholders so sanitized payloads never self-flag.

### 7. Modern Ergonomics & Desktop Aesthetics
* **Code Editor Line Number Gutters**: Integrated line number gutter on the left side of every input and output editor (just like VS Code). Features synchronized scrolling, dynamic digit width expansion, and theme-adaptive styling.
* **Side-by-Side Default View**: The studio defaults directly to side-by-side split view for comfortable side-by-side comparison on desktop screens, with one-click toggle to stacked view (`[ ⬒ Stacked View ]`).
* **High-DPI Razor-Sharp Scaling**: Per-monitor DPI awareness (`shcore.SetProcessDpiAwareness(2)`) ensures crisp fonts and borders on 1080p, 2K, and 4K monitors.
* **One-Click File I/O**: Direct `[ 📂 Open File... ]` and `[ 💾 Save File... ]` buttons on both Sanitize and Unsanitize card headers.
* **Paste & Sanitize**: One-click action button that pulls text directly from your clipboard and processes it in a single step.
* **Visual Diff Inspector (`[ 🔍 Inspect Diff ]`)**: Side-by-side color-coded modal showing line-by-line additions, deletions, and exact modifications.
* **Interactive Breakdown Badges**: Interactive summary pills underneath the output view display the count of each replaced secret with click-to-jump highlighting.
* **Dark / Light Themes**: Switch between an obsidian dark developer theme and an eye-friendly light daylight palette at any time.
* **Quick-Mask Context Menu**: Select any text in the input card and right-click to instantly create a rule or generate a realistic synthetic mask.
* **Smart Auto-Mask Presets**: One-click scanner that automatically extracts all IPv4s, emails, UUIDs, and Bearer tokens found in the active text and adds rules for them.

---

## 📖 Desktop Workflows

### Sanitize Workflow
1. **Load Input**:
   - Type or paste your logs into the **Original / Sensitive Input** box, OR
   - Click `[ 📂 Open File... ]` to load from disk, OR
   - Click `[ 📋 Paste & Sanitize ]` to ingest and process your clipboard directly.
2. **Execute**:
   - Click `[ 🛡️ Sanitize Payload ]` (or press `Ctrl+Enter`).
3. **Review**:
   - Inspect the **Leak Warning Bar** (if any unmasked secrets remain).
   - Check the **Interactive Breakdown Badges** to see what was replaced.
   - Click `[ 🔍 Inspect Diff ]` to view side-by-side visual diffs.
4. **Export**:
   - Click `[ 📋 Copy Sanitized ]` to copy the safe text to your clipboard, OR
   - Click `[ 💾 Save File... ]` to export to disk.

### Unsanitize Workflow
1. **Load AI Output**:
   - Paste the AI's response or command script into the **Sanitized Input** box, or click `[ 📂 Open File... ]`.
2. **Restore**:
   - Click `[ 🔓 Unsanitize Payload ]` (or press `Ctrl+Enter`).
3. **Copy with Auto-Wipe Protection**:
   - Click `[ 📋 Copy Unsanitized ]`.
   - The status bar initiates a **60s countdown timer** with `[Keep]` and `[Clear Now]` buttons to protect your restored credentials from persisting in clipboard history.

### Managing Rules
* Switch to the **Rules Management** tab to view your active aliases.
* Add rules manually or click `[ ⚡ Auto-Mask Presets... ]` to bulk-extract IPv4s, Emails, UUIDs, and Tokens from current text.
* Toggle between **Realistic Synthetic** mode (deterministic lookalikes) and **Classic Placeholder** mode (`<IP_1>`, `<TOKEN_1>`).

---

## 📁 File Architecture

| File | Description |
| :--- | :--- |
| **[Launch_Studio.bat](Launch_Studio.bat)** | Double-click Windows shortcut to launch the unified desktop studio. |
| **[sanitizer_app.py](sanitizer_app.py)** | Main modern desktop application containing the unified multi-tab studio, threaded async controller, diff inspector, and clipboard timer. |
| **[sanitizer_core.py](sanitizer_core.py)** | Core engine: HMAC-SHA256 synthetic generator, atomic file operations, regex engine, leak scanners, preflight collision detector. |
| **[replacement.json](replacement.json)** | Active configuration mapping real secrets to anonymized placeholders/synthetic aliases. |
| **[replacement.json.bak](replacement.json.bak)** | Rolling backup of the configuration created automatically before each atomic write. |
| **[.vault_pepper.key](.vault_pepper.key)** | Local 32-byte cryptographic pepper for deterministic HMAC-SHA256 synthetic generation. |
| **[.gitignore](.gitignore)** | Git exclusion rules for clean repository sharing. |
