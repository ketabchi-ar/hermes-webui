import pathlib
import json
import subprocess

ROOT = pathlib.Path(__file__).parent.parent.resolve()
I18N = ROOT / "static" / "i18n.js"

def test_fa_locale_structure_and_rtl():
    script = """
    const fs = require('fs');
    const vm = require('vm');
    const src = fs.readFileSync(process.argv[1], 'utf8');
    const storage = {};
    const classes = new Set();
    const ctx = {
      localStorage: {
        getItem: (k) => storage[k] || null,
        setItem: (k, v) => { storage[k] = String(v); },
      },
      document: {
        documentElement: {
          lang: '',
          classList: {
            add: (c) => classes.add(c),
            remove: (c) => classes.delete(c),
            contains: (c) => classes.has(c),
          },
          setAttribute: function(k, v) { this[k] = v; },
          removeAttribute: function(k) { delete this[k]; }
        },
        querySelectorAll: () => [],
      },
    };
    vm.createContext(ctx);
    vm.runInContext(src, ctx);
    const resolved = vm.runInContext("resolveLocale('fa')", ctx);
    const faBundle = vm.runInContext("LOCALES.fa", ctx);
    vm.runInContext("setLocale('fa')", ctx);
    const hasRtlClass = classes.has('chat-content-rtl');
    const lang = ctx.document.documentElement.lang;
    process.stdout.write(JSON.stringify({
      resolved,
      label: faBundle._label,
      hasRtlClass,
      lang,
      settings_tab_preferences: faBundle.settings_tab_preferences,
      settings_label_rtl: faBundle.settings_label_rtl
    }));
    """
    proc = subprocess.run(["node", "-e", script, str(I18N)], check=True, capture_output=True, text=True)
    res = json.loads(proc.stdout)
    assert res["resolved"] == "fa"
    assert res["label"] == "فارسی"
    assert res["hasRtlClass"] is True
    assert res["lang"] == "fa-IR"
    assert res["settings_tab_preferences"] == "ترجیحات"
    assert res["settings_label_rtl"] == "چیدمان راست‌به‌چپ چت"


def test_sessions_source_placeholders_preserved():
    """Item 4 regression: sessions_source_webui and sessions_source_cli must contain {0} count placeholder."""
    script = """
    const fs = require('fs');
    const vm = require('vm');
    const src = fs.readFileSync(process.argv[1], 'utf8');
    const ctx = {
      localStorage: { getItem: () => null, setItem: () => {} },
      document: { documentElement: { lang: '' }, querySelectorAll: () => [] }
    };
    vm.createContext(ctx);
    vm.runInContext(src, ctx);
    const fa = vm.runInContext("LOCALES.fa", ctx);
    process.stdout.write(JSON.stringify({
      webui: fa.sessions_source_webui,
      cli: fa.sessions_source_cli
    }));
    """
    proc = subprocess.run(["node", "-e", script, str(I18N)], check=True, capture_output=True, text=True)
    res = json.loads(proc.stdout)
    assert "{0}" in res["webui"], f"Expected {0} placeholder in sessions_source_webui, got: {res['webui']}"
    assert "{0}" in res["cli"], f"Expected {0} placeholder in sessions_source_cli, got: {res['cli']}"


def test_opening_settings_preserves_persian_auto_rtl():
    """Item 5 regression: Opening settings panel must not revert automatic RTL for Persian users."""
    panels_src = (ROOT / "static" / "panels.js").read_text(encoding="utf-8")
    assert "const isFaLocale = currentLocale === 'fa';" in panels_src
    assert "if (storedRtl !== null)" in panels_src
    assert "else if (settings && typeof settings.rtl === 'boolean')" in panels_src
    assert "saved = isFaLocale;" in panels_src
    # Must NOT write to localStorage merely on settings open
    assert "rtlCb.checked = saved;\n      document.documentElement.classList.toggle('chat-content-rtl', saved);" in panels_src


def test_vazirmatn_font_license_exists():
    """Item 6: SIL Open Font License must accompany the Vazirmatn font files in static/fonts/."""
    ofl = ROOT / "static" / "fonts" / "OFL.txt"
    assert ofl.exists(), "static/fonts/OFL.txt is missing"
    content = ofl.read_text(encoding="utf-8")
    assert "Saber Rastikerdar" in content
    assert "SIL OPEN FONT LICENSE" in content


def test_fa_function_signatures_and_destructive_warnings():
    """Item 2: Ensure function signatures, named arguments, and safety warnings match en exactly."""
    script = """
    const fs = require('fs');
    const vm = require('vm');
    const src = fs.readFileSync(process.argv[1], 'utf8');
    const ctx = {
      localStorage: { getItem: () => null, setItem: () => {} },
      document: { documentElement: { lang: '' }, querySelectorAll: () => [] }
    };
    vm.createContext(ctx);
    vm.runInContext(src, ctx);
    const fa = vm.runInContext("LOCALES.fa", ctx);
    const t = vm.runInContext("t", ctx);
    vm.runInContext("_locale = LOCALES.fa", ctx);

    const ckpt = t('checkpoint_restore_confirm_message', 'test-snap');
    const untracked = t('session_worktree_remove_untracked_warning', 5);
    const ahead = t('session_worktree_remove_ahead_warning', 3);
    const paused = t('goal_paused', 'build app');
    const resumed = t('goal_resumed', 'build app');
    const achieved = t('goal_achieved', 'tests green');
    const goalSet = t('goal_set', 10, 'my goal');
    const dl = t('downloading', 'file.txt');
    const delConfirm = t('delete_confirm', 'item1');

    process.stdout.write(JSON.stringify({
      ckpt, untracked, ahead, paused, resumed, achieved, goalSet, dl, delConfirm
    }));
    """
    proc = subprocess.run(["node", "-e", script, str(I18N)], check=True, capture_output=True, text=True)
    res = json.loads(proc.stdout)
    assert "test-snap" in res["ckpt"], f"Checkpoint label missing: {res['ckpt']}"
    assert "رونویسی" in res["ckpt"] or "بازگردانده" in res["ckpt"]
    assert "5" in res["untracked"] and "ردیابی‌نشده" in res["untracked"]
    assert "3" in res["ahead"] and "ارسال‌نشده" in res["ahead"]
    assert "build app" in res["paused"]
    assert "build app" in res["resumed"]
    assert "tests green" in res["achieved"]
    assert "10" in res["goalSet"] and "my goal" in res["goalSet"]
    assert "file.txt" in res["dl"]
    assert "item1" in res["delConfirm"]


def test_rtl_state_transitions_default_and_explicit():
    """Item 1: End-to-end state transitions for automatic locale default vs explicit user override."""
    script = """
    const fs = require('fs');
    const vm = require('vm');
    const i18nSrc = fs.readFileSync(process.argv[1], 'utf8');

    function setup(storage = {}) {
      const classes = new Set();
      const doc = {
        documentElement: {
          lang: '',
          classList: {
            add: (c) => classes.add(c),
            remove: (c) => classes.delete(c),
            contains: (c) => classes.has(c),
            toggle: (c, force) => {
              if (force !== undefined) {
                if (force) classes.add(c);
                else classes.delete(c);
              } else {
                if (classes.has(c)) classes.delete(c);
                else classes.add(c);
              }
            }
          },
          setAttribute: () => {},
          removeAttribute: () => {}
        },
        querySelectorAll: () => []
      };
      const ctx = {
        localStorage: {
          getItem: (k) => storage[k] !== undefined ? storage[k] : null,
          setItem: (k, v) => { storage[k] = String(v); },
          removeItem: (k) => { delete storage[k]; }
        },
        document: doc,
        window: {}
      };
      ctx.window = ctx;
      vm.createContext(ctx);
      vm.runInContext(i18nSrc, ctx);
      return { ctx, storage, classes };
    }

    // 1. Initial en locale, no localStorage -> no RTL, no localStorage dirtying
    const s1 = setup();
    s1.ctx.setLocale('en');
    const enHasRtl = s1.classes.has('chat-content-rtl');
    const enStorageClean = s1.storage['hermes-rtl'] === undefined;

    // 2. Switch en -> fa without prior localStorage -> automatic RTL, storage remains clean
    s1.ctx.setLocale('fa');
    const faAutoRtl = s1.classes.has('chat-content-rtl');
    const faStorageClean = s1.storage['hermes-rtl'] === undefined;

    // 3. Explicit fa opt-out -> user unchecks RTL checkbox (stored 'false')
    s1.storage['hermes-rtl'] = 'false';
    s1.ctx.setLocale('fa');
    const explicitFaOff = !s1.classes.has('chat-content-rtl');

    // 4. Explicit en opt-in -> user checks RTL in en (stored 'true')
    const s2 = setup({ 'hermes-rtl': 'true' });
    s2.ctx.setLocale('en');
    const explicitEnOn = s2.classes.has('chat-content-rtl');

    process.stdout.write(JSON.stringify({
      enHasRtl,
      enStorageClean,
      faAutoRtl,
      faStorageClean,
      explicitFaOff,
      explicitEnOn
    }));
    """
    proc = subprocess.run(["node", "-e", script, str(I18N)], check=True, capture_output=True, text=True)
    res = json.loads(proc.stdout)
    assert res["enHasRtl"] is False
    assert res["enStorageClean"] is True
    assert res["faAutoRtl"] is True
    assert res["faStorageClean"] is True
    assert res["explicitFaOff"] is True
    assert res["explicitEnOn"] is True
