#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把「原生触感 + 单击暂停」改动应用到 HGhubX 源码树（语义重放，随上游版本漂移自适应）。

每个编辑都要求唯一匹配，匹配不到或匹配多次即报 FAIL 并退出码 1，
这样不会出现“以为改了其实没改”的情况。
"""
import base64, os, sys

ROOT = sys.argv[1]

ok = []
fail = []

def path(rel):
    return os.path.join(ROOT, rel)

def read(rel):
    with open(path(rel), 'r', encoding='utf-8', newline='') as fh:
        return fh.read()

def write(rel, text):
    p = path(rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='') as fh:
        fh.write(text)

def rep(rel, old, new, label, count=1):
    text = read(rel)
    n = text.count(old)
    if n != count:
        fail.append('%s :: %s (expected %d occurrence, found %d)' % (rel, label, count, n))
        return False
    write(rel, text.replace(old, new, count))
    ok.append('%s :: %s' % (rel, label))
    return True

def ensure_absent(rel, needle, label):
    text = read(rel)
    if needle in text:
        fail.append('%s :: %s (already present)' % (rel, label))
        return False
    ok.append('%s :: %s (absent, good)' % (rel, label))
    return True

# ── 0. 已经打过补丁就直接跳过（CI 重跑/增量友好） ────────────────
if os.path.exists(path('src/shared/lib/haptics.ts')) and 'pub fn haptic' in read('src-tauri/src/api/platform.rs'):
    print('already patched: src/shared/lib/haptics.ts + platform.rs::haptic both present, nothing to do')
    sys.exit(0)

# ── 1. 新文件：内嵌 base64，直接落盘 ───────────────────────────────
NEW_FILES = [
    (r"src/shared/lib/haptics.ts",
    "aW1wb3J0IHsgaW52b2tlIH0gZnJvbSAiQHRhdXJpLWFwcHMvYXBpL2NvcmUiOwppbXBvcnQgeyBp"
    "c0lvcyB9IGZyb20gIi4uL2FwaS9hcGkiOwoKLyoqCiAqIOinpuaEn+WPjemmiOOAggogKgogKiDo"
    "v5nph4znu5/kuIDmlLblj6PvvIzmmK/lm6DkuLrku5PlupPljp/mnaXmlaPokL3nnYAgYG5hdmln"
    "YXRvci52aWJyYXRlPy4oKWDvvJrlroPlnKjlronljZMgV2ViVmlldyDph4zog73nlKjvvIwKICog"
    "5ZyoIGlPUyBXS1dlYlZpZXcg6YeM5qC55pys5LiN5a2Y5Zyo6L+Z5Liq5pa55rOV77yMaU9TIOeU"
    "qOaIt+S4gOebtOaYr+OAjOeCueS6huayoeaEn+inieOAjeOAggogKiDnjrDlnKggaU9TIOi1sOWO"
    "n+eUn+WRveS7pCBgaGFwdGljYO+8iGBzcmMtdGF1cmkvc3JjL2lvc19oYXB0aWMucnNg77yJ77yM"
    "5YW25a6D5bmz5Y+w5LuN55SoIFdlYiBWaWJyYXRpb27jgIIKICovCgovKiog5Y+N6aaI5qGj5L2N"
    "77yb5LiOIGBpb3NfaGFwdGljOjpwbGF5YCDnmoTlrZfnrKbkuLLkuIDkuIDlr7nlupTvvIzkuI3o"
    "poHljZXni6zmlLnlkI3jgIIgKi8KZXhwb3J0IHR5cGUgSGFwdGljS2luZCA9ICJsaWdodCIgfCAi"
    "bWVkaXVtIiB8ICJoZWF2eSIgfCAic2VsZWN0aW9uIiB8ICJzdWNjZXNzIiB8ICJ3YXJuaW5nIiB8"
    "ICJlcnJvciI7CgovKiogV2ViIFZpYnJhdGlvbiDlm57pgIDml7bplb/vvIjmr6vnp5LvvInjgILm"
    "lbDlgLzmjInmiYvmhJ/osIPov4fvvIzkuI3opoHpmo/mhI/mlL7lpKfjgIIgKi8KY29uc3QgVklC"
    "UkFURV9NUzogUmVjb3JkPEhhcHRpY0tpbmQsIG51bWJlciB8IG51bWJlcltdPiA9IHsKICBzZWxl"
    "Y3Rpb246IDgsCiAgbGlnaHQ6IDEyLAogIG1lZGl1bTogMjIsCiAgaGVhdnk6IDMyLAogIHN1Y2Nl"
    "c3M6IFsxMCwgNDAsIDEyXSwKICB3YXJuaW5nOiAxOCwKICBlcnJvcjogWzE0LCA0NiwgMTRdLAp9"
    "OwoKLyoqIOWQjOexu+WPjemmiOeahOacgOWwj+mXtOmalO+8mui/nueCueOAgeaLluWKqOi/m+W6"
    "puaXtuimgeWQiOW5tu+8jOWQpuWImeS8muWPmOaIkOaMgee7reWXoeWXoeWTjeOAgiAqLwpjb25z"
    "dCBNSU5fR0FQX01TID0gNDU7CgpsZXQgbGFzdEF0ID0gMDsKLyoqIOWOn+eUn+mAmumBk+Wksei0"
    "peS4gOasoeWwsemVv+acn+mZjee6p++8jOmBv+WFjeavj+asoeS6pOS6kumDveeZvei3keS4gOi2"
    "nyBJUEPjgIIgKi8KbGV0IG5hdGl2ZUJyb2tlbiA9IGZhbHNlOwoKZnVuY3Rpb24gd2ViKGtpbmQ6"
    "IEhhcHRpY0tpbmQpIHsKICB0cnkgewogICAgbmF2aWdhdG9yLnZpYnJhdGU/LihWSUJSQVRFX01T"
    "W2tpbmRdKTsKICB9IGNhdGNoIHsKICAgIC8qIOS4jeaUr+aMgeeahOiuvuWkh+WwseW9k+ayoeac"
    "iei/meWbnuS6i++8jOmch+WKqOe7neS4jeiDveW9seWTjeS6pOS6kuacrOi6qyAqLwogIH0KfQoK"
    "LyoqIOWOn+eUn+mAmumBk+W9k+WJjeaYr+WQpuWPr+eUqO+8iOWPquivu++8jOS+v+S6juiviuaW"
    "reS4jua1i+ivle+8ieOAgiAqLwpleHBvcnQgZnVuY3Rpb24gaGFwdGljTmF0aXZlUmVhZHkoKTog"
    "Ym9vbGVhbiB7CiAgcmV0dXJuIGlzSW9zICYmICFuYXRpdmVCcm9rZW47Cn0KCi8qKgogKiDop6bl"
    "j5HkuIDmrKHop6bmhJ/jgIIKICogQHBhcmFtIGtpbmQg5qGj5L2N77yM6buY6K6kIGBsaWdodGAK"
    "ICogQHBhcmFtIGdhcE1zIOS4juS4iuS4gOasoeWPjemmiOeahOacgOWwj+mXtOmalO+8m+a7keWK"
    "qOexu+S6pOS6kuS8oOabtOWkp+eahOWAvO+8iOS+i+WmgiAxMjDvvInmnaXov5vkuIDmraXpmY3p"
    "opEKICovCmV4cG9ydCBmdW5jdGlvbiBoYXB0aWMoa2luZDogSGFwdGljS2luZCA9ICJsaWdodCIs"
    "IGdhcE1zID0gTUlOX0dBUF9NUyk6IHZvaWQgewogIGNvbnN0IG5vdyA9IHR5cGVvZiBwZXJmb3Jt"
    "YW5jZSAhPT0gInVuZGVmaW5lZCIgPyBwZXJmb3JtYW5jZS5ub3coKSA6IERhdGUubm93KCk7CiAg"
    "aWYgKG5vdyAtIGxhc3RBdCA8IGdhcE1zKSByZXR1cm47CiAgbGFzdEF0ID0gbm93OwogIGlmICgh"
    "aGFwdGljTmF0aXZlUmVhZHkoKSkgewogICAgd2ViKGtpbmQpOwogICAgcmV0dXJuOwogIH0KICBp"
    "bnZva2U8Ym9vbGVhbj4oImhhcHRpYyIsIHsga2luZCB9KQogICAgLnRoZW4oKG5hdGl2ZSkgPT4g"
    "eyBpZiAoIW5hdGl2ZSkgd2ViKGtpbmQpOyB9KQogICAgLmNhdGNoKCgpID0+IHsgbmF0aXZlQnJv"
    "a2VuID0gdHJ1ZTsgd2ViKGtpbmQpOyB9KTsKfQoKLyoqIOW8gOWFs+exu++8muaJk+W8gOeUqCBg"
    "bWVkaXVtYO+8iOabtOacieehruiupOaEn++8ie+8jOWFs+mXreeUqCBgbGlnaHRg44CCICovCmV4"
    "cG9ydCBjb25zdCBoYXB0aWNUb2dnbGUgPSAob246IGJvb2xlYW4pID0+IGhhcHRpYyhvbiA/ICJt"
    "ZWRpdW0iIDogImxpZ2h0Iik7CgovKiog6YCJ6aG544CBVGFi44CB5YiG5q615o6n5Lu25YiH5o2i"
    "77yaaU9TIOWOn+eUn+eahCBzZWxlY3Rpb24g6LSo5oSf44CCICovCmV4cG9ydCBjb25zdCBoYXB0"
    "aWNTZWxlY3QgPSAoKSA9PiBoYXB0aWMoInNlbGVjdGlvbiIsIDYwKTsKCi8qKiDmu5Hliqjov57n"
    "u63lj5blgLzvvIjpn7Pph4/jgIHov5vluqbjgIHlgI3pgJ/mi5bliqjvvInvvJrpl7TpmpTmi4nl"
    "iLAgMTIwbXPvvIzmjInkuIvkuI7mnb7miYvlkITkuIDmrKHjgIIgKi8KZXhwb3J0IGNvbnN0IGhh"
    "cHRpY1NsaWRlID0gKCkgPT4gaGFwdGljKCJzZWxlY3Rpb24iLCAxMjApOwo="
    ),
    (r"src-tauri/src/ios_haptic.rs",
    "Ly8hIGlPUyDop6bmhJ/lj43ppojjgIIKLy8hCi8vISBXS1dlYlZpZXcg5rKh5pyJIGBuYXZpZ2F0"
    "b3IudmlicmF0ZWDvvIzliY3nq6/ljp/mnaXnmoQgYG5hdmlnYXRvci52aWJyYXRlPy4oKWAg5Zyo"
    "IGlPUyDkuIoKLy8hIOS4gOebtOaYr+epuuiwg+eUqO+8m+i/memHjOeUqCBvYmpjMiDnm7TmjqXl"
    "kJEgYFVJRmVlZGJhY2tHZW5lcmF0b3JgIOWutuaXj+WPkea2iOaBr++8jAovLyEg5LiN5paw5aKe"
    "IGNyYXRlIOS+nei1lu+8jOS5n+S4jemcgOimgemineWklueahCBvYmpjMi11aS1raXQg54m55oCn"
    "5L2N44CCCi8vIQovLyEg6LCD55So5pa577yIYGFwaTo6cGxhdGZvcm06OmhhcHRpY2DvvInkv53o"
    "r4HlnKjmnKzmqKHlnZfnmoTlh73mlbDph4zlj6rlgZrjgIzop6blj5HkuIDmrKHjgI3vvIwKLy8h"
    "IOmikeasoeaOp+WItuS6pOe7meWJjeerr++8iGBzcmMvc2hhcmVkL2xpYi9oYXB0aWNzLnRzYCDp"
    "h4wgNDVtcyDlkIjlubbvvInjgIIKCnVzZSBvYmpjMjo6cmM6OmF1dG9yZWxlYXNlcG9vbDsKdXNl"
    "IG9iamMyOjpydW50aW1lOjpBbnlPYmplY3Q7CnVzZSBvYmpjMjo6e2NsYXNzLCBtc2dfc2VuZH07"
    "CgovLy8gYFVJSW1wYWN0RmVlZGJhY2tTdHlsZWDvvJpMaWdodCA9IDDvvIxNZWRpdW0gPSAx77yM"
    "SGVhdnkgPSAy44CCCmZuIGltcGFjdChzdHlsZTogaTY0KSAtPiBib29sIHsKICAgIHVuc2FmZSB7"
    "CiAgICAgICAgbGV0IGdlbjogKm11dCBBbnlPYmplY3QgPSBtc2dfc2VuZCFbY2xhc3MhKFVJSW1w"
    "YWN0RmVlZGJhY2tHZW5lcmF0b3IpLCBhbGxvY107CiAgICAgICAgaWYgZ2VuLmlzX251bGwoKSB7"
    "CiAgICAgICAgICAgIHJldHVybiBmYWxzZTsKICAgICAgICB9CiAgICAgICAgbGV0IGdlbjogKm11"
    "dCBBbnlPYmplY3QgPSBtc2dfc2VuZCFbZ2VuLCBpbml0V2l0aFN0eWxlOiBzdHlsZV07CiAgICAg"
    "ICAgaWYgZ2VuLmlzX251bGwoKSB7CiAgICAgICAgICAgIHJldHVybiBmYWxzZTsKICAgICAgICB9"
    "CiAgICAgICAgbGV0IF86ICgpID0gbXNnX3NlbmQhW2dlbiwgcHJlcGFyZV07CiAgICAgICAgbGV0"
    "IF86ICgpID0gbXNnX3NlbmQhW2dlbiwgaW1wYWN0T2NjdXJyZWRdOwogICAgICAgIGxldCBfOiAo"
    "KSA9IG1zZ19zZW5kIVtnZW4sIHJlbGVhc2VdOwogICAgfQogICAgdHJ1ZQp9CgpmbiBzZWxlY3Rp"
    "b24oKSAtPiBib29sIHsKICAgIHVuc2FmZSB7CiAgICAgICAgbGV0IGdlbjogKm11dCBBbnlPYmpl"
    "Y3QgPSBtc2dfc2VuZCFbY2xhc3MhKFVJU2VsZWN0aW9uRmVlZGJhY2tHZW5lcmF0b3IpLCBhbGxv"
    "Y107CiAgICAgICAgaWYgZ2VuLmlzX251bGwoKSB7CiAgICAgICAgICAgIHJldHVybiBmYWxzZTsK"
    "ICAgICAgICB9CiAgICAgICAgbGV0IGdlbjogKm11dCBBbnlPYmplY3QgPSBtc2dfc2VuZCFbZ2Vu"
    "LCBpbml0XTsKICAgICAgICBpZiBnZW4uaXNfbnVsbCgpIHsKICAgICAgICAgICAgcmV0dXJuIGZh"
    "bHNlOwogICAgICAgIH0KICAgICAgICBsZXQgXzogKCkgPSBtc2dfc2VuZCFbZ2VuLCBwcmVwYXJl"
    "XTsKICAgICAgICBsZXQgXzogKCkgPSBtc2dfc2VuZCFbZ2VuLCBzZWxlY3Rpb25DaGFuZ2VkXTsK"
    "ICAgICAgICBsZXQgXzogKCkgPSBtc2dfc2VuZCFbZ2VuLCByZWxlYXNlXTsKICAgIH0KICAgIHRy"
    "dWUKfQoKLy8vIGBVSU5vdGlmaWNhdGlvbkZlZWRiYWNrVHlwZWDvvJpTdWNjZXNzID0gMO+8jFdh"
    "cm5pbmcgPSAx77yMRXJyb3IgPSAy44CCCmZuIG5vdGlmaWNhdGlvbihraW5kOiBpNjQpIC0+IGJv"
    "b2wgewogICAgdW5zYWZlIHsKICAgICAgICBsZXQgZ2VuOiAqbXV0IEFueU9iamVjdCA9IG1zZ19z"
    "ZW5kIVtjbGFzcyEoVUlOb3RpZmljYXRpb25GZWVkYmFja0dlbmVyYXRvciksIGFsbG9jXTsKICAg"
    "ICAgICBpZiBnZW4uaXNfbnVsbCgpIHsKICAgICAgICAgICAgcmV0dXJuIGZhbHNlOwogICAgICAg"
    "IH0KICAgICAgICBsZXQgZ2VuOiAqbXV0IEFueU9iamVjdCA9IG1zZ19zZW5kIVtnZW4sIGluaXRd"
    "OwogICAgICAgIGlmIGdlbi5pc19udWxsKCkgewogICAgICAgICAgICByZXR1cm4gZmFsc2U7CiAg"
    "ICAgICAgfQogICAgICAgIGxldCBfOiAoKSA9IG1zZ19zZW5kIVtnZW4sIHByZXBhcmVdOwogICAg"
    "ICAgIGxldCBfOiAoKSA9IG1zZ19zZW5kIVtnZW4sIG5vdGlmaWNhdGlvbk9jY3VycmVkOiBraW5k"
    "XTsKICAgICAgICBsZXQgXzogKCkgPSBtc2dfc2VuZCFbZ2VuLCByZWxlYXNlXTsKICAgIH0KICAg"
    "IHRydWUKfQoKLy8vIOinpuWPkeS4gOasoeinpuaEn++8m+acquefpeaho+S9jeaMiSBgbGlnaHRg"
    "IOWkhOeQhu+8jOS/neivgeiwg+eUqOaWueS4jeS8muWboOS4uuaLvOmUmeWtl+espuS4suiAjOmd"
    "mem7mOS4ouWPjemmiOOAggpwdWIgZm4gcGxheShraW5kOiAmc3RyKSAtPiBib29sIHsKICAgIGF1"
    "dG9yZWxlYXNlcG9vbCh8X3wgbWF0Y2gga2luZCB7CiAgICAgICAgInNlbGVjdGlvbiIgPT4gc2Vs"
    "ZWN0aW9uKCksCiAgICAgICAgImxpZ2h0IiA9PiBpbXBhY3QoMCksCiAgICAgICAgIm1lZGl1bSIg"
    "PT4gaW1wYWN0KDEpLAogICAgICAgICJoZWF2eSIgPT4gaW1wYWN0KDIpLAogICAgICAgICJzdWNj"
    "ZXNzIiA9PiBub3RpZmljYXRpb24oMCksCiAgICAgICAgIndhcm5pbmciID0+IG5vdGlmaWNhdGlv"
    "bigxKSwKICAgICAgICAiZXJyb3IiID0+IG5vdGlmaWNhdGlvbigyKSwKICAgICAgICBfID0+IGlt"
    "cGFjdCgwKSwKICAgIH0pCn0K"
    ),
]

for rel, b64 in NEW_FILES:
    p = path(rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if os.path.exists(p):
        ok.append('%s :: already exists, left untouched' % rel)
        continue
    with open(p, 'wb') as fh:
        fh.write(base64.b64decode(b64))
    ok.append('%s :: written from embedded copy' % rel)

# ── 2. api/platform.rs：注册 haptic 命令 ──────────────────────────
REP = 'src-tauri/src/api/platform.rs'
if 'pub fn haptic' not in read(REP):
    anchor = """    #[cfg(not(target_os = "ios"))]
    {
        let _ = (&app, enabled);
    }
    Ok(())
}
"""
    addition = anchor + """
/* ───────────────────── 触感反馈 ───────────────────── */

/// 触发一次原生触感。iOS 走 `UIImpactFeedbackGenerator` / `UISelectionFeedbackGenerator`，
/// 其余平台直接返回 false，由前端回退到 `navigator.vibrate`。
#[tauri::command]
pub fn haptic(app: tauri::AppHandle, kind: String) -> Result<bool, String> {
    #[cfg(target_os = "ios")]
    {
        use tauri::Manager;
        let _ = app;
        let queued = app
            .run_on_main_thread(move || {
                crate::ios_haptic::play(&kind);
            })
            .is_ok();
        Ok(queued)
    }
    #[cfg(not(target_os = "ios"))]
    {
        let _ = (&app, kind);
        Ok(false)
    }
}
"""
    rep(REP, anchor, addition, 'register haptic command')
else:
    ok.append('%s :: haptic already present' % REP)

# ── 3. lib.rs：mod 声明 + handler 注册 ──────────────────────────
LIB = 'src-tauri/src/lib.rs'
rep(LIB,
    '#[cfg(target_os = "ios")]\nmod ios_layout;',
    '#[cfg(target_os = "ios")]\nmod ios_haptic;\n#[cfg(target_os = "ios")]\nmod ios_layout;',
    'declare ios_haptic module')
rep(LIB,
    '        api::platform::set_text_interaction,',
    '        api::platform::set_text_interaction,\n        api::platform::haptic,',
    'register haptic in generate_handler!')

# ── 4. ui.tsx：Toggle 触感 ─────────────────────────────────────
UI = 'src/shared/ui/ui.tsx'
rep(UI,
    'import { tr } from "../i18n";',
    'import { tr } from "../i18n";\nimport { hapticToggle } from "../lib/haptics";',
    'import hapticToggle')
rep(UI,
    'onClick={() => onChange(!on)}',
    'onClick={() => { hapticToggle(!on); onChange(!on); }}',
    'Toggle onClick haptics')

# ── 5. ios/controls.tsx：Input(range) 与 SegmentedControl 触感 ──
CTL = 'src/shared/ui/ios/controls.tsx'
rep(CTL,
    'import { tr } from "../../i18n";',
    'import { tr } from "../../i18n";\nimport { hapticSelect, hapticSlide } from "../../lib/haptics";',
    'import haptics in controls')
rep(CTL,
    'type ButtonHTMLAttributes, import type',
    'type ButtonHTMLAttributes, import type', 'noop-guard', 0) if False else None
rep(CTL,
    'import { Children, forwardRef, type ButtonHTMLAttributes, type CSSProperties, type FormHTMLAttributes, type HTMLAttributes, type ImgHTMLAttributes, type InputHTMLAttributes, type TextareaHTMLAttributes } from "react";',
    'import { Children, forwardRef, type ButtonHTMLAttributes, type CSSProperties, type FormHTMLAttributes, type HTMLAttributes, type ImgHTMLAttributes, type InputHTMLAttributes, type PointerEvent as ReactPointerEvent, type TextareaHTMLAttributes } from "react";',
    'import ReactPointerEvent type')
rep(CTL,
    '''export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(function Input({ className, ...props }, ref) {
  return <input {...props} ref={ref} aria-label={props["aria-label"] ?? props.placeholder}''',
    '''export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(function Input({ className, ...props }, ref) {
  /* 滑块每次按下给一次选中触感；键盘操作与普通输入框不触发。 */
  const onDown: InputHTMLAttributes<HTMLInputElement>["onPointerDown"] = props.type === "range"
    ? (e: ReactPointerEvent<HTMLInputElement>) => { hapticSlide(); props.onPointerDown?.(e); }
    : props.onPointerDown;
  return <input {...props} onPointerDown={onDown} ref={ref} aria-label={props["aria-label"] ?? props.placeholder}''',
    'Input range pointer haptic')
rep(CTL,
    '''  const segmentStyle = { ...style, "--segment-count": count, "--segment-index": index } as SegmentedStyle;
  return <div {...props} style={segmentStyle} className={cn("ios-segmented", className)} role={props.role ?? "group"} aria-label={props["aria-label"] ?? tr("切换内容")}>''',
    '''  const segmentStyle = { ...style, "--segment-count": count, "--segment-index": index } as SegmentedStyle;
  /* 只在这一击真的落到另一个分段时给触感；点当前分段、点空白都不震。 */
  const onItemsDown = (e: ReactPointerEvent<HTMLSpanElement>) => {
    const hit = (e.target as HTMLElement | null)?.closest(".ios-segmented-items > *");
    if (!hit) return;
    const tapped = Array.prototype.indexOf.call(e.currentTarget.children, hit);
    if (tapped >= 0 && tapped !== index) hapticSelect();
  };
  return <div {...props} style={segmentStyle} className={cn("ios-segmented", className)} role={props.role ?? "group"} aria-label={props["aria-label"] ?? tr("切换内容")}>''',
    'SegmentedControl pointer haptic')
rep(CTL,
    '    <span className="ios-segmented-items">{segments}</span>',
    '    <span className="ios-segmented-items" onPointerDownCapture={onItemsDown}>{segments}</span>',
    'attach onPointerDownCapture')

# ── 6. PlayerControls.tsx：主播放按钮 ──────────────────────────
PC = 'src/features/playback/PlayerControls.tsx'
rep(PC, 'import { tr } from "../../shared/i18n";',
    'import { tr } from "../../shared/i18n";\nimport { haptic } from "../../shared/lib/haptics";',
    'import haptic')
rep(PC,
    'onClick={onToggle}>',
    'onClick={() => { haptic(paused ? "medium" : "light"); onToggle(); }}>',
    'play button haptic')

# ── 7. FeedPlayerShellChrome.tsx：移动端播放按钮 ────────────────
FS = 'src/features/feed/FeedPlayerShellChrome.tsx'
rep(FS,
    '<Button onClick={() => videoRef.current?.toggle()} aria-label={paused ? tr("播放") : tr("暂停")}',
    '<Button onClick={() => { haptic(paused ? "medium" : "light"); videoRef.current?.toggle(); }} aria-label={paused ? tr("播放") : tr("暂停")}',
    'mobile play button haptic')
# 该文件的 import 段：找 tr 的导入行插入
_txt = read(FS)
_import_anchor = 'import { tr } from "../../shared/i18n";'
if _import_anchor in _txt:
    rep(FS, _import_anchor, _import_anchor + '\nimport { haptic } from "../../shared/lib/haptics";', 'import haptic (FS)')
else:
    fail.append('%s :: import anchor for tr not found' % FS)

# ── 8. useFeedTouchGestures.ts：核心改成单击暂停 ───────────────
G = 'src/features/feed/useFeedTouchGestures.ts'
rep(G,
    'import { tr } from "../../shared/i18n";',
    'import { tr } from "../../shared/i18n";\nimport { haptic } from "../../shared/lib/haptics";',
    'import haptic')
rep(G,
    '''  /* 单击 / 双击判定：单击净屏，双击暂停 */
  const lastTapRef = useRef<{ timer: number | null; clean?: boolean; idle?: boolean }>({ timer: null });
''', '', 'drop lastTapRef')
rep(G, '/* —— 长按加速/减速 / 横拖定位 / 单击净屏、双击暂停 —— */',
       '/* —— 长按加速/减速 / 横拖定位 / 单击暂停或继续 —— */', 'update section comment')
rep(G, "try { navigator.vibrate?.(25); } catch { /* ignore */ }",
       'haptic("medium");', 'hold speed-in vibrate -> haptic')
rep(G, "try { navigator.vibrate?.(12); } catch { /* ignore */ }",
       'haptic("selection");', 'episode switch vibrate -> haptic', count=2)
rep(G,
    '''    if (!cancelled && g.mode === "idle" && Date.now() - g.t < 260) {
      // 首击立即反馈；第二击恢复首击前的界面，再切换播放。
      if (lastTapRef.current.timer) {
        window.clearTimeout(lastTapRef.current.timer);
        lastTapRef.current.timer = null;
        setClean(lastTapRef.current.clean ?? false);
        if (!isDesktop && fs) setIdle(lastTapRef.current.idle ?? false);
        if (!isDesktop && fs && !lastTapRef.current.idle) arm();
        videoRef.current?.toggle();
      } else {
        lastTapRef.current.clean = clean;
        lastTapRef.current.idle = idle;
        setClean(!clean);
        if (!isDesktop && fs) setIdle(!idle);
        /* Re-arm the auto-hide timer whenever fullscreen controls become visible. */
        if (!isDesktop && fs) arm();
        lastTapRef.current.timer = window.setTimeout(() => {
          lastTapRef.current.timer = null;
        }, 230) as unknown as number;
      }
    }''',
    '''    if (!cancelled && g.mode === "idle" && Date.now() - g.t < 320) {
      // 单击即暂停/继续。控件正隐藏（或已清屏）时，这一击只把它唤回来，不动播放状态。
      if (clean || (fs && idle)) {
        setClean(false);
        if (!isDesktop && fs) { setIdle(false); arm(); }
        haptic("selection");
        return;
      }
      const wasPlaying = videoRef.current?.isPlayWanted() ?? false;
      videoRef.current?.toggle();
      haptic(wasPlaying ? "light" : "medium");
      if (!isDesktop && fs) { setIdle(false); arm(); }
    }''',
    'single-tap play/pause')
rep(G,
    '''      if (lastTapRef.current.timer) window.clearTimeout(lastTapRef.current.timer);
      lastTapRef.current.timer = null;
''', '', 'drop stale timer cleanup (inactive)')
rep(G,
    '''    if (lastTapRef.current.timer) window.clearTimeout(lastTapRef.current.timer);
    lastTapRef.current.timer = null;
''', '', 'drop stale timer cleanup (unmount)')

# ── 9. mobileHold.ts ─────────────────────────────────────────
MH = 'src/features/feed/mobileHold.ts'
rep(MH,
    'export const HOLD_DELAY_MS = 260;',
    'import { haptic } from "../../shared/lib/haptics";\n\nexport const HOLD_DELAY_MS = 260;',
    'import haptic')
rep(MH, "try { navigator.vibrate?.(15); } catch { /* ignore */ }",
    'haptic("light");', 'hold shift vibrate -> haptic')

# ── 10. MobileHoldGuide.tsx 文案 ────────────────────────────
rep('src/features/feed/MobileHoldGuide.tsx',
    '<p>{tr("双击暂停播放")}</p>',
    '<p>{tr("单击暂停 / 继续播放")}</p>',
    'guide copy')

# ── 11. 文档 ────────────────────────────────────────────────
rep('docs/operations/playback-diagnostics.md',
    '| `gesture` | Feed 移动端首击在 230ms 内切换净屏，双击恢复界面并只切换一次播放状态 |',
    '| `gesture` | Feed 移动端单击画面即暂停/继续（320ms 内、无位移），控件正隐藏时这一击只唤出控件、不改变播放状态；播放按钮与开关点击有触感 |',
    'diagnostics gesture row')

rep('docs/subsystems/playback.md',
    '单击画面切换显隐、双击仍是暂停/播放；',
    '单击画面即暂停/继续（触感：继续用 `medium`、暂停用 `light`），控件正隐藏时这一击只唤出控件、不改变播放状态；',
    'playback.md tap semantics')

md_lessons = read('docs/lessons.md')
row = '| 2026-11-25 | iOS 端触感一直是空调用 | WKWebView 里没有 `navigator.vibrate`，旧代码 `navigator.vibrate?.()` 在 iOS 上是静默 no-op | 统一走 `src/shared/lib/haptics.ts`：原生 `haptic` 命令（`src-tauri/src/ios_haptic.rs`）优先，非 iOS / 调用失败回退 vibrate | 常驻回归待核实（本机无 iOS 真机与 cargo） |\n'
if 'iOS 端触感一直是空调用' in md_lessons:
    ok.append('docs/lessons.md :: already has row')
else:
    if not md_lessons.endswith('\n'):
        md_lessons += '\n'
    write('docs/lessons.md', md_lessons + row)
    ok.append('docs/lessons.md :: appended row')

# platform-shells.md：iOS 段落补一条
PS = 'docs/subsystems/platform-shells.md'
ps = read(PS)
if 'haptic' in ps:
    ok.append('%s :: already mentions haptic' % PS)
else:
    marker = None
    for cand in ('### iOS', '## iOS', 'iOS 壳'):
        if cand in ps:
            marker = cand
            break
    if marker:
        write(PS, ps + '\n- **触感**：`haptic(kind)` 由 iOS 原生 `UIImpactFeedbackGenerator` / `UISelectionFeedbackGenerator` 提供（`src-tauri/src/ios_haptic.rs`），非 iOS 平台返回 `false` 并由前端回退到 `navigator.vibrate`；档位字面量为 `light` / `medium` / `heavy` / `selection` / `success` / `warning` / `error`。\n')
        ok.append('%s :: appended haptic note' % PS)
    else:
        fail.append('%s :: no iOS section anchor found' % PS)

print('OK: %d' % len(ok))
for x in ok:
    print('  + ' + x)
print('FAIL: %d' % len(fail))
for x in fail:
    print('  - ' + x)
sys.exit(0 if not fail else 1)
