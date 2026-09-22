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
    const ctx = {
      localStorage: {
        getItem: (k) => storage[k] || null,
        setItem: (k, v) => { storage[k] = String(v); },
      },
      document: {
        documentElement: {
          lang: '',
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
    const dir = ctx.document.documentElement.dir;
    const lang = ctx.document.documentElement.lang;
    process.stdout.write(JSON.stringify({
      resolved,
      label: faBundle._label,
      dir,
      lang,
      settings_tab_preferences: faBundle.settings_tab_preferences,
      settings_label_rtl: faBundle.settings_label_rtl
    }));
    """
    proc = subprocess.run(["node", "-e", script, str(I18N)], check=True, capture_output=True, text=True)
    res = json.loads(proc.stdout)
    assert res["resolved"] == "fa"
    assert res["label"] == "فارسی"
    assert res["dir"] == "rtl"
    assert res["lang"] == "fa-IR"
    assert res["settings_tab_preferences"] == "ترجیحات"
    assert res["settings_label_rtl"] == "چیدمان راست‌به‌چپ چت"
