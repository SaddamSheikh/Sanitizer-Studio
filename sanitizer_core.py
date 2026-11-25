#!/usr/bin/env python3
"""
Sanitizer Core Engine
Provides centralized rule management, validation, collision detection,
encoding-aware transformation (URL & JSON escaping), and breakdown reporting.
"""

import os
import sys
import json
import re
import math
import urllib.parse
import hashlib
import hmac
import secrets
import shutil
import uuid
from typing import Dict, List, Tuple, Optional, Any

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DEFAULT_CONFIG_PATH = os.path.join(BASE_DIR, "replacement.json")


def get_vault_pepper() -> bytes:
    """
    Returns a unique local cryptographically-secure master pepper for deterministic pseudonymization.
    Stored in .vault_pepper.key in the workspace so synthetic outputs on this workstation
    cannot be de-anonymized via public rainbow tables.
    """
    salt_file = os.path.join(BASE_DIR, ".vault_pepper.key")
    try:
        if os.path.exists(salt_file):
            with open(salt_file, "rb") as f:
                data = f.read()
                if len(data) >= 32:
                    return data[:32]

        pepper = secrets.token_bytes(32)
        temp_salt = f"{salt_file}.tmp.{os.getpid()}"
        with open(temp_salt, "wb") as f:
            f.write(pepper)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_salt, salt_file)
        return pepper
    except Exception:
        return b"sanitizer_studio_local_pepper_v1_fixed_fallback"


class Clipboard:
    """Robust cross-platform / Windows clipboard manager with multi-backend fallbacks."""

    _active_root = None

    @classmethod
    def register_root(cls, root: Any):
        cls._active_root = root

    @classmethod
    def get(cls, root: Optional[Any] = None) -> str:
        r = root or cls._active_root
        if r is not None:
            try:
                text = r.clipboard_get()
                if text:
                    return text
            except Exception:
                pass

        if sys.platform == "win32":
            try:
                import ctypes
                user32 = ctypes.windll.user32
                kernel32 = ctypes.windll.kernel32
                user32.OpenClipboard.restype = ctypes.c_int
                user32.OpenClipboard.argtypes = [ctypes.c_void_p]
                user32.CloseClipboard.restype = ctypes.c_int
                user32.CloseClipboard.argtypes = []
                user32.GetClipboardData.restype = ctypes.c_void_p
                user32.GetClipboardData.argtypes = [ctypes.c_uint]
                kernel32.GlobalLock.restype = ctypes.c_void_p
                kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
                kernel32.GlobalUnlock.restype = ctypes.c_int
                kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]

                if user32.OpenClipboard(None):
                    hMem = user32.GetClipboardData(13)  # CF_UNICODETEXT
                    if hMem:
                        ptr = kernel32.GlobalLock(hMem)
                        if ptr:
                            text = ctypes.wstring_at(ptr)
                            kernel32.GlobalUnlock(hMem)
                            user32.CloseClipboard()
                            return text
                    user32.CloseClipboard()
            except Exception:
                pass

        return ""

    @classmethod
    def set(cls, text: str, root: Optional[Any] = None) -> bool:
        r = root or cls._active_root
        if r is not None:
            try:
                r.clipboard_clear()
                r.clipboard_append(text)
                r.update()
                return True
            except Exception:
                pass

        if sys.platform == "win32":
            try:
                import ctypes
                user32 = ctypes.windll.user32
                kernel32 = ctypes.windll.kernel32
                user32.OpenClipboard.restype = ctypes.c_int
                user32.OpenClipboard.argtypes = [ctypes.c_void_p]
                user32.CloseClipboard.restype = ctypes.c_int
                user32.CloseClipboard.argtypes = []
                user32.EmptyClipboard.restype = ctypes.c_int
                user32.EmptyClipboard.argtypes = []
                user32.SetClipboardData.restype = ctypes.c_void_p
                user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
                kernel32.GlobalAlloc.restype = ctypes.c_void_p
                kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
                kernel32.GlobalLock.restype = ctypes.c_void_p
                kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
                kernel32.GlobalUnlock.restype = ctypes.c_int
                kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]

                if user32.OpenClipboard(None):
                    user32.EmptyClipboard()
                    encoded = text.encode("utf-16-le") + b"\x00\x00"
                    hMem = kernel32.GlobalAlloc(2, len(encoded))  # GMEM_MOVEABLE
                    if hMem:
                        ptr = kernel32.GlobalLock(hMem)
                        if ptr:
                            ctypes.memmove(ptr, encoded, len(encoded))
                            kernel32.GlobalUnlock(hMem)
                            user32.SetClipboardData(13, hMem)
                    user32.CloseClipboard()
                    return True
            except Exception:
                pass

        return False


class SanitizerEngine:
    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        self.config_path = os.path.abspath(config_path)
        self.rules: Dict[str, str] = {}         # Forward: secret -> placeholder
        self.reverse_rules: Dict[str, str] = {} # Inverted: placeholder -> secret
        self.collisions: Dict[str, List[str]] = {} # placeholder -> [secret1, secret2]
        self.load_config(self.config_path)

    def load_config(self, path: Optional[str] = None) -> bool:
        """Loads and parses rules from JSON, handling trailing commas and detecting collisions."""
        if path:
            self.config_path = os.path.abspath(path)

        if not os.path.exists(self.config_path):
            self.rules = {}
            self.reverse_rules = {}
            self.collisions = {}
            return False

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                content = f.read()

            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                cleaned = re.sub(r",\s*([}\]])", r"\1", content)
                data = json.loads(cleaned)

            if not isinstance(data, dict):
                self.rules = {}
                self.reverse_rules = {}
                self.collisions = {}
                return False

            self.rules = {str(k).strip(): str(v).strip() for k, v in data.items() if str(k).strip()}
            self._compute_reverse_rules()
            return True
        except Exception:
            self.rules = {}
            self.reverse_rules = {}
            self.collisions = {}
            return False

    def _compute_reverse_rules(self):
        """Builds reverse mapping and detects any placeholder collision."""
        self.reverse_rules = {}
        self.collisions = {}
        grouped: Dict[str, List[str]] = {}

        for secret, placeholder in self.rules.items():
            if not placeholder:
                continue
            grouped.setdefault(placeholder, []).append(secret)
            if placeholder not in self.reverse_rules:
                self.reverse_rules[placeholder] = secret

        self.collisions = {p: secrets for p, secrets in grouped.items() if len(secrets) > 1}

    def save_config(self, path: Optional[str] = None) -> bool:
        """
        Saves current rules to JSON using an atomic write pattern with rolling backup.
        Prevents 0-byte file truncation during sudden termination/power cut.
        """
        save_path = os.path.abspath(path) if path else self.config_path
        try:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            # 1. Create rolling backup if target file already exists and is non-empty
            if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
                bak_path = save_path + ".bak"
                try:
                    shutil.copy2(save_path, bak_path)
                except Exception:
                    pass

            # 2. Atomic write to temporary file
            temp_path = f"{save_path}.tmp.{os.getpid()}"
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(self.rules, f, indent=4, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())

            # 3. Atomic replace
            os.replace(temp_path, save_path)

            self.config_path = save_path
            self._compute_reverse_rules()
            return True
        except Exception:
            return False

    def add_rule(self, secret: str, placeholder: str) -> None:
        """Adds or updates a rule and refreshes reverse mapping."""
        secret = str(secret).strip()
        placeholder = str(placeholder).strip()
        if not secret or not placeholder:
            return
        self.rules[secret] = placeholder
        self._compute_reverse_rules()

    def remove_rule(self, secret: str) -> bool:
        """Removes a rule by its original secret key."""
        if secret in self.rules:
            del self.rules[secret]
            self._compute_reverse_rules()
            return True
        return False

    @staticmethod
    def _get_encoded_variants(k: str, v: str) -> Dict[str, Tuple[str, str, str]]:
        """
        Generates URL-encoded (%20 and +) and JSON-escaped variations of key and value.
        Returns: {matched_variant: (replacement_variant, original_k, original_v)}
        """
        variants = {k: (v, k, v)}

        # URL encoded (%20)
        url_k = urllib.parse.quote(k)
        url_v = urllib.parse.quote(v)
        if url_k != k:
            variants[url_k] = (url_v, k, v)

        # URL quote_plus (+)
        plus_k = urllib.parse.quote_plus(k)
        plus_v = urllib.parse.quote_plus(v)
        if plus_k != k and plus_k != url_k:
            variants[plus_k] = (plus_v, k, v)

        # JSON escaped
        try:
            json_k = json.dumps(k)[1:-1]
            json_v = json.dumps(v)[1:-1]
            if json_k != k:
                variants[json_k] = (json_v, k, v)
        except Exception:
            pass

        return variants

    @staticmethod
    def _build_regex(keys: List[str], word_boundaries: bool = True, ignore_case: bool = False) -> Optional[re.Pattern]:
        """
        Builds a compiled regex from keys.
        Sorts descending by length to prevent partial prefix collisions.
        Applies smart word boundaries for alphanumeric keys so 'OSS' doesn't match 'POSSIBLE'.
        """
        if not keys:
            return None

        sorted_keys = sorted(keys, key=len, reverse=True)
        patterns = []

        for k in sorted_keys:
            esc = re.escape(k)
            if word_boundaries:
                prefix = r"\b" if re.match(r"^\w", k) else ""
                suffix = r"\b" if re.search(r"\w$", k) else ""
                patterns.append(f"{prefix}{esc}{suffix}")
            else:
                patterns.append(esc)

        flags = re.IGNORECASE if ignore_case else 0
        return re.compile("|".join(patterns), flags)

    def sanitize(
        self,
        text: str,
        case_insensitive: bool = False,
        word_boundaries: bool = True,
        encoding_aware: bool = False
    ) -> Tuple[str, int, List[Tuple[int, int, str, str, str, str]], Dict[str, int]]:
        """
        Replaces real secrets with placeholders.
        Returns: (sanitized_text, replacement_count, match_spans, breakdown)
        where match_spans is a list of (start_idx, end_idx, matched_str, replaced_val, orig_k, orig_v)
        and breakdown is a dict of {"orig_k ➔ orig_v": count}.
        """
        return self._transform(
            text=text,
            rule_map=self.rules,
            case_insensitive=case_insensitive,
            word_boundaries=word_boundaries,
            encoding_aware=encoding_aware
        )

    def unsanitize(
        self,
        text: str,
        case_insensitive: bool = False,
        word_boundaries: bool = True,
        encoding_aware: bool = False
    ) -> Tuple[str, int, List[Tuple[int, int, str, str, str, str]], Dict[str, int]]:
        """
        Reverses placeholders back into real secrets.
        Returns: (restored_text, replacement_count, match_spans, breakdown)
        where match_spans is a list of (start_idx, end_idx, matched_str, replaced_val, orig_k, orig_v)
        and breakdown is a dict of {"orig_k ➔ orig_v": count}.
        """
        return self._transform(
            text=text,
            rule_map=self.reverse_rules,
            case_insensitive=case_insensitive,
            word_boundaries=word_boundaries,
            encoding_aware=encoding_aware
        )

    def _transform(
        self,
        text: str,
        rule_map: Dict[str, str],
        case_insensitive: bool,
        word_boundaries: bool,
        encoding_aware: bool
    ) -> Tuple[str, int, List[Tuple[int, int, str, str, str, str]], Dict[str, int]]:
        if not text or not rule_map:
            return text, 0, [], {}

        # Build variant lookup: matched_key -> (replacement, orig_k, orig_v)
        variant_map: Dict[str, Tuple[str, str, str]] = {}
        for k, v in rule_map.items():
            if encoding_aware:
                for var_k, meta in self._get_encoded_variants(k, v).items():
                    if var_k not in variant_map:
                        variant_map[var_k] = meta
            else:
                variant_map[k] = (v, k, v)

        pattern = self._build_regex(list(variant_map.keys()), word_boundaries=word_boundaries, ignore_case=case_insensitive)
        if not pattern:
            return text, 0, [], {}

        lower_variant_map = {k.lower(): v for k, v in variant_map.items()} if case_insensitive else None

        chunks = []
        spans = []
        breakdown: Dict[str, int] = {}
        last_idx = 0
        count = 0
        current_len = 0

        for match in pattern.finditer(text):
            start, end = match.span()

            # Untouched prefix
            if start > last_idx:
                prefix_str = text[last_idx:start]
                chunks.append(prefix_str)
                current_len += len(prefix_str)

            matched_str = match.group(0)
            if case_insensitive:
                new_val, orig_k, orig_v = lower_variant_map.get(matched_str.lower(), (matched_str, matched_str, matched_str))
            else:
                new_val, orig_k, orig_v = variant_map.get(matched_str, (matched_str, matched_str, matched_str))

            val_len = len(new_val)
            spans.append((current_len, current_len + val_len, matched_str, new_val, orig_k, orig_v))
            chunks.append(new_val)
            current_len += val_len
            count += 1

            label = f"{orig_k} ➔ {orig_v}"
            breakdown[label] = breakdown.get(label, 0) + 1

            last_idx = end

        if last_idx < len(text):
            tail_str = text[last_idx:]
            chunks.append(tail_str)

        return "".join(chunks), count, spans, breakdown

    # =========================================================================
    # FEATURE 2B: SMART AUTO-MASKING PRESETS
    # =========================================================================
    @staticmethod
    def detect_preset_entities(text: str) -> Dict[str, List[str]]:
        """
        Scans text for common sensitive entities: IPv4 addresses, emails, UUIDs,
        and API tokens/hashes.
        Returns: {'ip': [...], 'email': [...], 'uuid': [...], 'token': [...]}
        """
        results: Dict[str, List[str]] = {
            "ip": [],
            "email": [],
            "uuid": [],
            "token": []
        }
        if not text:
            return results

        # 1. IPv4 addresses
        ip_matches = re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", text)
        valid_ips = []
        for ip in ip_matches:
            parts = ip.split(".")
            if len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
                if ip not in valid_ips:
                    valid_ips.append(ip)
        results["ip"] = valid_ips

        # 2. Email addresses
        email_matches = re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", text)
        results["email"] = list(dict.fromkeys(email_matches))

        # 3. UUIDs / GUIDs
        uuid_matches = re.findall(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b", text)
        results["uuid"] = list(dict.fromkeys(uuid_matches))

        # 4. API Keys / Tokens / Hashes
        token_patterns = [
            r"\bghp_[A-Za-z0-9]{36}\b",
            r"\bAKIA[0-9A-Z]{16}\b",
            r"\bBearer\s+([A-Za-z0-9_\-\.]+\.[A-Za-z0-9_\-\.]+\.[A-Za-z0-9_\-\.]+)\b",
            r"\bey[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*\b",
            r"\b[0-9a-fA-F]{32,64}\b"
        ]
        tokens = []
        for pat in token_patterns:
            for m in re.finditer(pat, text):
                val = m.group(1) if m.groups() else m.group(0)
                if val not in tokens and val not in valid_ips:
                    tokens.append(val)
        results["token"] = tokens

        return results

    @staticmethod
    def generate_synthetic_value(val: str, category: str, attempt: int = 0) -> str:
        """
        Generates a realistic, syntactically-valid, deterministic synthetic replacement
        for sensitive values (IPs, emails, UUIDs, tokens).
        Uses workstation master pepper + HMAC-SHA-256 seed so the same input always maps
        to the same synthetic fake value, but cannot be inverted via public rainbow tables.
        Guaranteed to not match the original value.
        """
        pepper = get_vault_pepper()
        salt = f"sanitizer_v1:{category}:{attempt}:".encode("utf-8")
        seed = hmac.new(pepper, salt + val.strip().encode("utf-8"), hashlib.sha256).digest()

        if category == "ip":
            b1, b2, b3, b4 = seed[0], seed[1], seed[2], seed[3]
            if val.startswith("192.168."):
                fake = f"192.168.{(b2 % 250) + 1}.{(b3 % 250) + 1}"
            elif val.startswith("10."):
                fake = f"10.{(b1 % 250) + 1}.{(b2 % 250) + 1}.{(b3 % 250) + 1}"
            elif val.startswith("172."):
                fake = f"172.{(16 + (b1 % 15))}.{(b2 % 250) + 1}.{(b3 % 250) + 1}"
            else:
                # Use RFC 5737 TEST-NET documentation subnet (198.51.100.x / 203.0.113.x)
                sub = 100 if (b1 % 2 == 0) else 113
                fake = f"198.51.{sub}.{(b2 % 250) + 1}"
            if fake == val:
                fake = f"198.51.100.{(b3 % 250) + 1}"
            return fake

        elif category == "email":
            first_names = ["alex", "jordan", "taylor", "morgan", "sam", "casey", "riley", "cameron", "avery", "quinn", "logan", "reese", "dakota", "skyler"]
            last_names = ["smith", "johnson", "williams", "brown", "jones", "garcia", "miller", "davis", "rodriguez", "martinez", "taylor", "anderson", "thomas"]
            fn = first_names[seed[0] % len(first_names)]
            ln = last_names[seed[1] % len(last_names)]
            num = (seed[2] % 90) + 10
            domain = "example.com"
            if "@" in val:
                orig_domain = val.split("@")[-1]
                tld = orig_domain.split(".")[-1] if "." in orig_domain else "com"
                domain = f"example.{tld}"
            fake = f"{fn}.{ln}{num}@{domain}"
            return fake if fake != val else f"user{num}@{domain}"

        elif category == "uuid":
            raw = bytearray(seed[0:16])
            raw[6] = (raw[6] & 0x0f) | 0x40  # RFC 4122 v4
            raw[8] = (raw[8] & 0x3f) | 0x80  # Variant 1
            return str(uuid.UUID(bytes=bytes(raw)))

        elif category == "token":
            hex_hash = hashlib.sha256(seed).hexdigest()
            if val.startswith("ghp_"):
                return "ghp_" + hex_hash[:36]
            elif val.startswith("github_pat_"):
                return "github_pat_" + hex_hash[:82]
            elif val.startswith("sk-proj-"):
                return "sk-proj-" + hex_hash[:48]
            elif val.startswith("sk-ant-"):
                return "sk-ant-" + hex_hash[:48]
            elif val.startswith("sk_live_"):
                return "sk_live_" + hex_hash[:24]
            elif val.startswith("rk_live_"):
                return "rk_live_" + hex_hash[:24]
            elif val.startswith("xoxb-"):
                return "xoxb-" + hex_hash[:24]
            elif val.startswith("xoxp-"):
                return "xoxp-" + hex_hash[:24]
            elif val.startswith("hf_"):
                return "hf_" + hex_hash[:34]
            elif val.startswith("AIza"):
                return "AIza" + hex_hash[:35]
            elif val.startswith("SG."):
                return "SG." + hex_hash[:22] + "." + hex_hash[:43]
            elif val.startswith("AKIA") and len(val) == 20:
                chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
                return "AKIA" + "".join(chars[b % len(chars)] for b in seed[:16])
            elif val.startswith("ey") and "." in val:
                return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzeW50aGV0aWMiLCJpYXQiOjE2MDAwMDAwMDB9." + hex_hash[:43]
            elif all(c in "0123456789abcdefABCDEF" for c in val):
                extended = hex_hash + hashlib.sha256(seed + b"ext").hexdigest()
                return extended[:len(val)]
            else:
                chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
                return "".join(chars[b % len(chars)] for b in seed[:len(val)])

        return f"SYNTH_{category.upper()}_{seed[0]}"

    def generate_preset_rules(
        self,
        text: str,
        categories: Optional[List[str]] = None,
        existing_rules: Optional[Dict[str, str]] = None,
        mode: str = "synthetic"
    ) -> Dict[str, str]:
        """
        Auto-generates deterministic placeholder rules for detected entities.
        Modes:
        - 'synthetic' (default): Generates realistic fake IPs (192.168.x.y, 10.x.y.z),
          authentic emails (alex.smith42@example.com), valid UUIDs, and realistic token hashes.
          100% deterministic (same input produces the exact same fake value every time).
        - 'semantic': Generates sequential aliases (IP_1, EMAIL_1, UUID_1, etc.)
        """
        entities = self.detect_preset_entities(text)
        if categories is None:
            categories = ["ip", "email", "uuid", "token"]

        rules = existing_rules if existing_rules is not None else self.rules
        generated: Dict[str, str] = {}

        if mode == "synthetic":
            used_values = set(rules.values())
            for cat in categories:
                if cat not in entities:
                    continue
                for val in entities[cat]:
                    if val in rules or val in generated:
                        continue
                    attempt = 0
                    while True:
                        synth = self.generate_synthetic_value(val, cat, attempt)
                        if synth != val and synth not in used_values and synth not in generated.values():
                            generated[val] = synth
                            used_values.add(synth)
                            break
                        attempt += 1
                        if attempt > 10:
                            generated[val] = f"{synth}_{attempt}"
                            break
            return generated

        category_labels = {
            "ip": "IP",
            "email": "EMAIL",
            "uuid": "UUID",
            "token": "TOKEN"
        }

        # Determine starting counter per category based on existing placeholders
        counters: Dict[str, int] = {}
        for cat, label in category_labels.items():
            max_c = 0
            for existing_ph in rules.values():
                m = re.match(rf"^{label}_(\d+)$", existing_ph)
                if m:
                    max_c = max(max_c, int(m.group(1)))
            counters[cat] = max_c + 1

        for cat in categories:
            if cat not in entities:
                continue
            label = category_labels.get(cat, cat.upper())
            for val in entities[cat]:
                if val in rules or val in generated:
                    continue
                placeholder = f"{label}_{counters[cat]}"
                counters[cat] += 1
                generated[val] = placeholder

        return generated

    def check_preflight_collisions(self, text: str) -> List[Tuple[str, str]]:
        """
        Scans raw input text BEFORE sanitization to see if it already naturally contains
        any of the active placeholder aliases.
        Returns: [(placeholder, associated_secret), ...]
        """
        if not text or not self.reverse_rules:
            return []

        conflicts = []
        for placeholder, secret in self.reverse_rules.items():
            if len(placeholder) < 3:
                continue
            if placeholder in text:
                conflicts.append((placeholder, secret))
        return conflicts

    # =========================================================================
    # FEATURE 2C: PARTIAL-SECRET LEAK WARNING SCANNER
    # =========================================================================
    @staticmethod
    def detect_partial_secret_leaks(sanitized_text: str, rules: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Detects if any original secret appears inside the sanitized output:
        1. Exact unmasked occurrence (e.g. due to word-boundary regex \b skipping compound words).
        2. Substring inside an unmasked token (e.g. 'prod_secret' inside 'my_prod_secret_v2').
        Returns list of warnings with context and line number.
        """
        warnings = []
        if not sanitized_text or not rules:
            return warnings

        # Filter out very short rules (< 3 chars) to avoid false positives on punctuation or 1-2 char keys
        candidate_rules = {k: v for k, v in rules.items() if len(k) >= 3}
        if not candidate_rules:
            return warnings

        lines = sanitized_text.splitlines()

        for secret, placeholder in candidate_rules.items():
            sec_lower = secret.lower()
            for line_idx, line in enumerate(lines):
                line_lower = line.lower()
                start_search = 0
                while True:
                    idx = line_lower.find(sec_lower, start_search)
                    if idx == -1:
                        break

                    matched_slice = line[idx:idx + len(secret)]
                    start_char = idx
                    end_char = idx + len(secret)

                    # Extract the enclosing word/token
                    # Walk left to boundary
                    w_start = start_char
                    while w_start > 0 and not line[w_start - 1].isspace() and line[w_start - 1] not in ",;'\"()[]{}<>":
                        w_start -= 1
                    # Walk right to boundary
                    w_end = end_char
                    while w_end < len(line) and not line[w_end].isspace() and line[w_end] not in ",;'\"()[]{}<>":
                        w_end += 1

                    enclosing_token = line[w_start:w_end]

                    # Context snippet (up to 25 chars before and after)
                    c_start = max(0, start_char - 25)
                    c_end = min(len(line), end_char + 25)
                    context_snippet = ("..." if c_start > 0 else "") + line[c_start:c_end] + ("..." if c_end < len(line) else "")

                    is_compound = (enclosing_token != matched_slice)

                    warnings.append({
                        "secret": secret,
                        "placeholder": placeholder,
                        "matched_text": matched_slice,
                        "enclosing_token": enclosing_token,
                        "line_num": line_idx + 1,
                        "col": start_char,
                        "context": context_snippet,
                        "is_compound": is_compound,
                        "reason": f"Secret was left unmasked inside compound token '{enclosing_token}'" if is_compound else f"Secret was left unmasked in line {line_idx + 1}"
                    })

                    start_search = idx + len(secret)

        return warnings

    @staticmethod
    def calculate_shannon_entropy(data: str) -> float:
        """
        Calculates the Shannon entropy (information density) of a string.
        Higher entropy values (typically >= 3.8 for strings of length >= 20)
        indicate high randomness characteristic of cryptographic keys and proprietary secrets.
        """
        if not data:
            return 0.0
        entropy = 0.0
        length = len(data)
        counts: Dict[str, int] = {}
        for char in data:
            counts[char] = counts.get(char, 0) + 1
        for count in counts.values():
            p = count / length
            entropy -= p * math.log2(p)
        return entropy

    @staticmethod
    def detect_potential_leaks(text: str, rules: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """
        Scans text for unmasked credentials, API keys, database URLs, config assignments,
        and high-entropy tokens to warn users before sharing with AI.
        Categorizes findings by severity: CRITICAL, HIGH, MEDIUM.
        """
        findings = []
        if not text:
            return findings

        # Known mask values to suppress (if rule replacements already masked them)
        known_masks = set()
        if rules:
            for v in rules.values():
                if v:
                    known_masks.add(v.strip())
                    known_masks.add(v.strip().lower())

        # (Label, Regex, Severity, Group Index for secret value)
        patterns = [
            # CRITICAL: Private Keys, Database Passwords, Master Cloud/AI Keys
            ("Private Key Block", r"-----BEGIN\s+[A-Z0-9\s_-]+PRIVATE KEY-----|-----BEGIN PGP PRIVATE KEY BLOCK-----", "CRITICAL", 0),
            ("Database Connection String", r"(?i)\b(?:postgres|postgresql|mysql|mongodb|mongodb\+srv|redis|amqp|mssql):\/\/[^\s:@\/]+:([^\s@\/]+)@[^\s\/]+", "CRITICAL", 1),
            ("AWS Secret Access Key", r"""(?i)(?:aws_secret_access_key|aws_secret_key)\s*[:=]\s*["']?([A-Za-z0-9/+=]{40})["']?""", "CRITICAL", 1),
            ("OpenAI API Key", r"\b(sk-proj-[A-Za-z0-9_-]{30,}|sk-[A-Za-z0-9]{30,})\b", "CRITICAL", 1),
            ("Anthropic API Key", r"\b(sk-ant-[A-Za-z0-9_-]{30,})\b", "CRITICAL", 1),
            ("Google Cloud API Key", r"\b(AIza[0-9A-Za-z\\-_]{30,40})\b", "CRITICAL", 1),
            ("AWS Access Key ID", r"\b(AKIA[0-9A-Z]{16})\b", "CRITICAL", 1),

            # HIGH: Service Tokens, JWTs, Bearer, Config Assignments
            ("JWT / Bearer Token", r"Bearer\s+([A-Za-z0-9_\-\.]+\.[A-Za-z0-9_\-\.]+\.[A-Za-z0-9_\-\.]+)", "HIGH", 1),
            ("JWT Token", r"\b(ey[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{10,})\b", "HIGH", 1),
            ("GitHub Personal Access Token", r"\b(gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{60,})\b", "HIGH", 1),
            ("Stripe API Key", r"\b([rs]k_(?:live|test)_[0-9a-zA-Z]{24,})\b", "HIGH", 1),
            ("Slack API Token", r"\b(xox[baprs]-[0-9A-Za-z-]{20,})\b", "HIGH", 1),
            ("SendGrid API Key", r"\b(SG\.[A-Za-z0-9_-]{16,32}\.[A-Za-z0-9_-]{32,64})\b", "HIGH", 1),
            ("HuggingFace Token", r"\b(hf_[A-Za-z0-9]{34,})\b", "HIGH", 1),
            ("Basic Auth Header", r"(?i)Authorization:\s*Basic\s+([A-Za-z0-9+/=]{10,})", "HIGH", 1),
            ("Config Secret Assignment", r"""(?i)\b(?:api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret|db[_-]?password|password|passwd|pwd)\s*[:=]\s*["']?([^\s"';,]{8,})["']?""", "HIGH", 1),

            # MEDIUM: Query parameters
            ("Password in URL/Query", r"(?i)(?:password|passwd|pwd|secret)=([^&\s]+)", "MEDIUM", 1)
        ]

        seen_spans = set()

        for label, regex, severity, grp in patterns:
            for match in re.finditer(regex, text):
                m_start = match.start()
                m_end = match.end()

                # Deduplicate overlapping spans
                if any(abs(m_start - s[0]) < 3 and abs(m_end - s[1]) < 3 for s in seen_spans):
                    continue

                secret_val = match.group(grp) if grp <= len(match.groups()) and match.group(grp) else match.group(0)

                # Skip if secret_val is already one of the replacement masks
                if secret_val in known_masks or secret_val.lower() in known_masks:
                    continue

                seen_spans.add((m_start, m_end))

                line_num = text.count("\n", 0, m_start) + 1
                last_nl = text.rfind("\n", 0, m_start)
                col = m_start - (last_nl if last_nl != -1 else 0)

                c_start = max(0, m_start - 30)
                c_end = min(len(text), m_end + 30)
                context_snippet = ("..." if c_start > 0 else "") + text[c_start:c_end] + ("..." if c_end < len(text) else "")

                findings.append({
                    "type": label,
                    "severity": severity,
                    "matched": match.group(0),
                    "secret_value": secret_val,
                    "start": m_start,
                    "end": m_end,
                    "line_num": line_num,
                    "col": col,
                    "context": context_snippet
                })

        # High Entropy Token Detector (Shannon Entropy)
        # Scan words of length >= 20 composed of base64/hex/alphanumeric characters
        word_pattern = r"\b([A-Za-z0-9+/=_-]{20,})\b"
        for w_match in re.finditer(word_pattern, text):
            w_start = w_match.start()
            w_end = w_match.end()

            # Skip if already captured by structured patterns
            if any(s[0] <= w_start and w_end <= s[1] for s in seen_spans):
                continue

            word = w_match.group(1)

            # Ignore if known mask
            if word in known_masks or word.lower() in known_masks:
                continue

            # Ignore pure numeric strings
            if word.isdigit():
                continue

            # Standard UUID pattern check
            if re.fullmatch(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", word):
                continue

            # Check entropy
            entropy = SanitizerEngine.calculate_shannon_entropy(word)
            if entropy >= 3.8 and len(word) >= 22:
                seen_spans.add((w_start, w_end))
                line_num = text.count("\n", 0, w_start) + 1
                last_nl = text.rfind("\n", 0, w_start)
                col = w_start - (last_nl if last_nl != -1 else 0)
                c_start = max(0, w_start - 30)
                c_end = min(len(text), w_end + 30)
                context_snippet = ("..." if c_start > 0 else "") + text[c_start:c_end] + ("..." if c_end < len(text) else "")

                findings.append({
                    "type": f"High-Entropy Secret (Entropy: {entropy:.2f})",
                    "severity": "MEDIUM",
                    "matched": word,
                    "secret_value": word,
                    "start": w_start,
                    "end": w_end,
                    "line_num": line_num,
                    "col": col,
                    "context": context_snippet
                })

        return findings
