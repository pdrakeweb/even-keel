/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const N = globalThis, I = N.ShadowRoot && (N.ShadyCSS === void 0 || N.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, Z = Symbol(), q = /* @__PURE__ */ new WeakMap();
let nt = class {
  constructor(t, e, s) {
    if (this._$cssResult$ = !0, s !== Z) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = t, this.t = e;
  }
  get styleSheet() {
    let t = this.o;
    const e = this.t;
    if (I && t === void 0) {
      const s = e !== void 0 && e.length === 1;
      s && (t = q.get(e)), t === void 0 && ((this.o = t = new CSSStyleSheet()).replaceSync(this.cssText), s && q.set(e, t));
    }
    return t;
  }
  toString() {
    return this.cssText;
  }
};
const _t = (i) => new nt(typeof i == "string" ? i : i + "", void 0, Z), $t = (i, ...t) => {
  const e = i.length === 1 ? i[0] : t.reduce((s, r, o) => s + ((n) => {
    if (n._$cssResult$ === !0) return n.cssText;
    if (typeof n == "number") return n;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + n + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(r) + i[o + 1], i[0]);
  return new nt(e, i, Z);
}, gt = (i, t) => {
  if (I) i.adoptedStyleSheets = t.map((e) => e instanceof CSSStyleSheet ? e : e.styleSheet);
  else for (const e of t) {
    const s = document.createElement("style"), r = N.litNonce;
    r !== void 0 && s.setAttribute("nonce", r), s.textContent = e.cssText, i.appendChild(s);
  }
}, J = I ? (i) => i : (i) => i instanceof CSSStyleSheet ? ((t) => {
  let e = "";
  for (const s of t.cssRules) e += s.cssText;
  return _t(e);
})(i) : i;
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const { is: yt, defineProperty: vt, getOwnPropertyDescriptor: mt, getOwnPropertyNames: wt, getOwnPropertySymbols: bt, getPrototypeOf: At } = Object, H = globalThis, G = H.trustedTypes, Et = G ? G.emptyScript : "", xt = H.reactiveElementPolyfillSupport, S = (i, t) => i, T = { toAttribute(i, t) {
  switch (t) {
    case Boolean:
      i = i ? Et : null;
      break;
    case Object:
    case Array:
      i = i == null ? i : JSON.stringify(i);
  }
  return i;
}, fromAttribute(i, t) {
  let e = i;
  switch (t) {
    case Boolean:
      e = i !== null;
      break;
    case Number:
      e = i === null ? null : Number(i);
      break;
    case Object:
    case Array:
      try {
        e = JSON.parse(i);
      } catch {
        e = null;
      }
  }
  return e;
} }, V = (i, t) => !yt(i, t), Y = { attribute: !0, type: String, converter: T, reflect: !1, useDefault: !1, hasChanged: V };
Symbol.metadata ??= Symbol("metadata"), H.litPropertyMetadata ??= /* @__PURE__ */ new WeakMap();
let b = class extends HTMLElement {
  static addInitializer(t) {
    this._$Ei(), (this.l ??= []).push(t);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(t, e = Y) {
    if (e.state && (e.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(t) && ((e = Object.create(e)).wrapped = !0), this.elementProperties.set(t, e), !e.noAccessor) {
      const s = Symbol(), r = this.getPropertyDescriptor(t, s, e);
      r !== void 0 && vt(this.prototype, t, r);
    }
  }
  static getPropertyDescriptor(t, e, s) {
    const { get: r, set: o } = mt(this.prototype, t) ?? { get() {
      return this[e];
    }, set(n) {
      this[e] = n;
    } };
    return { get: r, set(n) {
      const a = r?.call(this);
      o?.call(this, n), this.requestUpdate(t, a, s);
    }, configurable: !0, enumerable: !0 };
  }
  static getPropertyOptions(t) {
    return this.elementProperties.get(t) ?? Y;
  }
  static _$Ei() {
    if (this.hasOwnProperty(S("elementProperties"))) return;
    const t = At(this);
    t.finalize(), t.l !== void 0 && (this.l = [...t.l]), this.elementProperties = new Map(t.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(S("finalized"))) return;
    if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(S("properties"))) {
      const e = this.properties, s = [...wt(e), ...bt(e)];
      for (const r of s) this.createProperty(r, e[r]);
    }
    const t = this[Symbol.metadata];
    if (t !== null) {
      const e = litPropertyMetadata.get(t);
      if (e !== void 0) for (const [s, r] of e) this.elementProperties.set(s, r);
    }
    this._$Eh = /* @__PURE__ */ new Map();
    for (const [e, s] of this.elementProperties) {
      const r = this._$Eu(e, s);
      r !== void 0 && this._$Eh.set(r, e);
    }
    this.elementStyles = this.finalizeStyles(this.styles);
  }
  static finalizeStyles(t) {
    const e = [];
    if (Array.isArray(t)) {
      const s = new Set(t.flat(1 / 0).reverse());
      for (const r of s) e.unshift(J(r));
    } else t !== void 0 && e.push(J(t));
    return e;
  }
  static _$Eu(t, e) {
    const s = e.attribute;
    return s === !1 ? void 0 : typeof s == "string" ? s : typeof t == "string" ? t.toLowerCase() : void 0;
  }
  constructor() {
    super(), this._$Ep = void 0, this.isUpdatePending = !1, this.hasUpdated = !1, this._$Em = null, this._$Ev();
  }
  _$Ev() {
    this._$ES = new Promise((t) => this.enableUpdating = t), this._$AL = /* @__PURE__ */ new Map(), this._$E_(), this.requestUpdate(), this.constructor.l?.forEach((t) => t(this));
  }
  addController(t) {
    (this._$EO ??= /* @__PURE__ */ new Set()).add(t), this.renderRoot !== void 0 && this.isConnected && t.hostConnected?.();
  }
  removeController(t) {
    this._$EO?.delete(t);
  }
  _$E_() {
    const t = /* @__PURE__ */ new Map(), e = this.constructor.elementProperties;
    for (const s of e.keys()) this.hasOwnProperty(s) && (t.set(s, this[s]), delete this[s]);
    t.size > 0 && (this._$Ep = t);
  }
  createRenderRoot() {
    const t = this.shadowRoot ?? this.attachShadow(this.constructor.shadowRootOptions);
    return gt(t, this.constructor.elementStyles), t;
  }
  connectedCallback() {
    this.renderRoot ??= this.createRenderRoot(), this.enableUpdating(!0), this._$EO?.forEach((t) => t.hostConnected?.());
  }
  enableUpdating(t) {
  }
  disconnectedCallback() {
    this._$EO?.forEach((t) => t.hostDisconnected?.());
  }
  attributeChangedCallback(t, e, s) {
    this._$AK(t, s);
  }
  _$ET(t, e) {
    const s = this.constructor.elementProperties.get(t), r = this.constructor._$Eu(t, s);
    if (r !== void 0 && s.reflect === !0) {
      const o = (s.converter?.toAttribute !== void 0 ? s.converter : T).toAttribute(e, s.type);
      this._$Em = t, o == null ? this.removeAttribute(r) : this.setAttribute(r, o), this._$Em = null;
    }
  }
  _$AK(t, e) {
    const s = this.constructor, r = s._$Eh.get(t);
    if (r !== void 0 && this._$Em !== r) {
      const o = s.getPropertyOptions(r), n = typeof o.converter == "function" ? { fromAttribute: o.converter } : o.converter?.fromAttribute !== void 0 ? o.converter : T;
      this._$Em = r;
      const a = n.fromAttribute(e, o.type);
      this[r] = a ?? this._$Ej?.get(r) ?? a, this._$Em = null;
    }
  }
  requestUpdate(t, e, s, r = !1, o) {
    if (t !== void 0) {
      const n = this.constructor;
      if (r === !1 && (o = this[t]), s ??= n.getPropertyOptions(t), !((s.hasChanged ?? V)(o, e) || s.useDefault && s.reflect && o === this._$Ej?.get(t) && !this.hasAttribute(n._$Eu(t, s)))) return;
      this.C(t, e, s);
    }
    this.isUpdatePending === !1 && (this._$ES = this._$EP());
  }
  C(t, e, { useDefault: s, reflect: r, wrapped: o }, n) {
    s && !(this._$Ej ??= /* @__PURE__ */ new Map()).has(t) && (this._$Ej.set(t, n ?? e ?? this[t]), o !== !0 || n !== void 0) || (this._$AL.has(t) || (this.hasUpdated || s || (e = void 0), this._$AL.set(t, e)), r === !0 && this._$Em !== t && (this._$Eq ??= /* @__PURE__ */ new Set()).add(t));
  }
  async _$EP() {
    this.isUpdatePending = !0;
    try {
      await this._$ES;
    } catch (e) {
      Promise.reject(e);
    }
    const t = this.scheduleUpdate();
    return t != null && await t, !this.isUpdatePending;
  }
  scheduleUpdate() {
    return this.performUpdate();
  }
  performUpdate() {
    if (!this.isUpdatePending) return;
    if (!this.hasUpdated) {
      if (this.renderRoot ??= this.createRenderRoot(), this._$Ep) {
        for (const [r, o] of this._$Ep) this[r] = o;
        this._$Ep = void 0;
      }
      const s = this.constructor.elementProperties;
      if (s.size > 0) for (const [r, o] of s) {
        const { wrapped: n } = o, a = this[r];
        n !== !0 || this._$AL.has(r) || a === void 0 || this.C(r, void 0, o, a);
      }
    }
    let t = !1;
    const e = this._$AL;
    try {
      t = this.shouldUpdate(e), t ? (this.willUpdate(e), this._$EO?.forEach((s) => s.hostUpdate?.()), this.update(e)) : this._$EM();
    } catch (s) {
      throw t = !1, this._$EM(), s;
    }
    t && this._$AE(e);
  }
  willUpdate(t) {
  }
  _$AE(t) {
    this._$EO?.forEach((e) => e.hostUpdated?.()), this.hasUpdated || (this.hasUpdated = !0, this.firstUpdated(t)), this.updated(t);
  }
  _$EM() {
    this._$AL = /* @__PURE__ */ new Map(), this.isUpdatePending = !1;
  }
  get updateComplete() {
    return this.getUpdateComplete();
  }
  getUpdateComplete() {
    return this._$ES;
  }
  shouldUpdate(t) {
    return !0;
  }
  update(t) {
    this._$Eq &&= this._$Eq.forEach((e) => this._$ET(e, this[e])), this._$EM();
  }
  updated(t) {
  }
  firstUpdated(t) {
  }
};
b.elementStyles = [], b.shadowRootOptions = { mode: "open" }, b[S("elementProperties")] = /* @__PURE__ */ new Map(), b[S("finalized")] = /* @__PURE__ */ new Map(), xt?.({ ReactiveElement: b }), (H.reactiveElementVersions ??= []).push("2.1.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const Q = globalThis, X = (i) => i, U = Q.trustedTypes, tt = U ? U.createPolicy("lit-html", { createHTML: (i) => i }) : void 0, at = "$lit$", y = `lit$${Math.random().toFixed(9).slice(2)}$`, lt = "?" + y, St = `<${lt}>`, w = document, C = () => w.createComment(""), O = (i) => i === null || typeof i != "object" && typeof i != "function", F = Array.isArray, kt = (i) => F(i) || typeof i?.[Symbol.iterator] == "function", B = `[ 	
\f\r]`, x = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, et = /-->/g, st = />/g, v = RegExp(`>|${B}(?:([^\\s"'>=/]+)(${B}*=${B}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g"), rt = /'/g, it = /"/g, ct = /^(?:script|style|textarea|title)$/i, ht = (i) => (t, ...e) => ({ _$litType$: i, strings: t, values: e }), g = ht(1), u = ht(2), A = Symbol.for("lit-noChange"), d = Symbol.for("lit-nothing"), ot = /* @__PURE__ */ new WeakMap(), m = w.createTreeWalker(w, 129);
function dt(i, t) {
  if (!F(i) || !i.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return tt !== void 0 ? tt.createHTML(t) : t;
}
const Ct = (i, t) => {
  const e = i.length - 1, s = [];
  let r, o = t === 2 ? "<svg>" : t === 3 ? "<math>" : "", n = x;
  for (let a = 0; a < e; a++) {
    const l = i[a];
    let h, p, c = -1, _ = 0;
    for (; _ < l.length && (n.lastIndex = _, p = n.exec(l), p !== null); ) _ = n.lastIndex, n === x ? p[1] === "!--" ? n = et : p[1] !== void 0 ? n = st : p[2] !== void 0 ? (ct.test(p[2]) && (r = RegExp("</" + p[2], "g")), n = v) : p[3] !== void 0 && (n = v) : n === v ? p[0] === ">" ? (n = r ?? x, c = -1) : p[1] === void 0 ? c = -2 : (c = n.lastIndex - p[2].length, h = p[1], n = p[3] === void 0 ? v : p[3] === '"' ? it : rt) : n === it || n === rt ? n = v : n === et || n === st ? n = x : (n = v, r = void 0);
    const $ = n === v && i[a + 1].startsWith("/>") ? " " : "";
    o += n === x ? l + St : c >= 0 ? (s.push(h), l.slice(0, c) + at + l.slice(c) + y + $) : l + y + (c === -2 ? a : $);
  }
  return [dt(i, o + (i[e] || "<?>") + (t === 2 ? "</svg>" : t === 3 ? "</math>" : "")), s];
};
class P {
  constructor({ strings: t, _$litType$: e }, s) {
    let r;
    this.parts = [];
    let o = 0, n = 0;
    const a = t.length - 1, l = this.parts, [h, p] = Ct(t, e);
    if (this.el = P.createElement(h, s), m.currentNode = this.el.content, e === 2 || e === 3) {
      const c = this.el.content.firstChild;
      c.replaceWith(...c.childNodes);
    }
    for (; (r = m.nextNode()) !== null && l.length < a; ) {
      if (r.nodeType === 1) {
        if (r.hasAttributes()) for (const c of r.getAttributeNames()) if (c.endsWith(at)) {
          const _ = p[n++], $ = r.getAttribute(c).split(y), M = /([.?@])?(.*)/.exec(_);
          l.push({ type: 1, index: o, name: M[2], strings: $, ctor: M[1] === "." ? Pt : M[1] === "?" ? Lt : M[1] === "@" ? Mt : R }), r.removeAttribute(c);
        } else c.startsWith(y) && (l.push({ type: 6, index: o }), r.removeAttribute(c));
        if (ct.test(r.tagName)) {
          const c = r.textContent.split(y), _ = c.length - 1;
          if (_ > 0) {
            r.textContent = U ? U.emptyScript : "";
            for (let $ = 0; $ < _; $++) r.append(c[$], C()), m.nextNode(), l.push({ type: 2, index: ++o });
            r.append(c[_], C());
          }
        }
      } else if (r.nodeType === 8) if (r.data === lt) l.push({ type: 2, index: o });
      else {
        let c = -1;
        for (; (c = r.data.indexOf(y, c + 1)) !== -1; ) l.push({ type: 7, index: o }), c += y.length - 1;
      }
      o++;
    }
  }
  static createElement(t, e) {
    const s = w.createElement("template");
    return s.innerHTML = t, s;
  }
}
function E(i, t, e = i, s) {
  if (t === A) return t;
  let r = s !== void 0 ? e._$Co?.[s] : e._$Cl;
  const o = O(t) ? void 0 : t._$litDirective$;
  return r?.constructor !== o && (r?._$AO?.(!1), o === void 0 ? r = void 0 : (r = new o(i), r._$AT(i, e, s)), s !== void 0 ? (e._$Co ??= [])[s] = r : e._$Cl = r), r !== void 0 && (t = E(i, r._$AS(i, t.values), r, s)), t;
}
class Ot {
  constructor(t, e) {
    this._$AV = [], this._$AN = void 0, this._$AD = t, this._$AM = e;
  }
  get parentNode() {
    return this._$AM.parentNode;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  u(t) {
    const { el: { content: e }, parts: s } = this._$AD, r = (t?.creationScope ?? w).importNode(e, !0);
    m.currentNode = r;
    let o = m.nextNode(), n = 0, a = 0, l = s[0];
    for (; l !== void 0; ) {
      if (n === l.index) {
        let h;
        l.type === 2 ? h = new L(o, o.nextSibling, this, t) : l.type === 1 ? h = new l.ctor(o, l.name, l.strings, this, t) : l.type === 6 && (h = new zt(o, this, t)), this._$AV.push(h), l = s[++a];
      }
      n !== l?.index && (o = m.nextNode(), n++);
    }
    return m.currentNode = w, r;
  }
  p(t) {
    let e = 0;
    for (const s of this._$AV) s !== void 0 && (s.strings !== void 0 ? (s._$AI(t, s, e), e += s.strings.length - 2) : s._$AI(t[e])), e++;
  }
}
class L {
  get _$AU() {
    return this._$AM?._$AU ?? this._$Cv;
  }
  constructor(t, e, s, r) {
    this.type = 2, this._$AH = d, this._$AN = void 0, this._$AA = t, this._$AB = e, this._$AM = s, this.options = r, this._$Cv = r?.isConnected ?? !0;
  }
  get parentNode() {
    let t = this._$AA.parentNode;
    const e = this._$AM;
    return e !== void 0 && t?.nodeType === 11 && (t = e.parentNode), t;
  }
  get startNode() {
    return this._$AA;
  }
  get endNode() {
    return this._$AB;
  }
  _$AI(t, e = this) {
    t = E(this, t, e), O(t) ? t === d || t == null || t === "" ? (this._$AH !== d && this._$AR(), this._$AH = d) : t !== this._$AH && t !== A && this._(t) : t._$litType$ !== void 0 ? this.$(t) : t.nodeType !== void 0 ? this.T(t) : kt(t) ? this.k(t) : this._(t);
  }
  O(t) {
    return this._$AA.parentNode.insertBefore(t, this._$AB);
  }
  T(t) {
    this._$AH !== t && (this._$AR(), this._$AH = this.O(t));
  }
  _(t) {
    this._$AH !== d && O(this._$AH) ? this._$AA.nextSibling.data = t : this.T(w.createTextNode(t)), this._$AH = t;
  }
  $(t) {
    const { values: e, _$litType$: s } = t, r = typeof s == "number" ? this._$AC(t) : (s.el === void 0 && (s.el = P.createElement(dt(s.h, s.h[0]), this.options)), s);
    if (this._$AH?._$AD === r) this._$AH.p(e);
    else {
      const o = new Ot(r, this), n = o.u(this.options);
      o.p(e), this.T(n), this._$AH = o;
    }
  }
  _$AC(t) {
    let e = ot.get(t.strings);
    return e === void 0 && ot.set(t.strings, e = new P(t)), e;
  }
  k(t) {
    F(this._$AH) || (this._$AH = [], this._$AR());
    const e = this._$AH;
    let s, r = 0;
    for (const o of t) r === e.length ? e.push(s = new L(this.O(C()), this.O(C()), this, this.options)) : s = e[r], s._$AI(o), r++;
    r < e.length && (this._$AR(s && s._$AB.nextSibling, r), e.length = r);
  }
  _$AR(t = this._$AA.nextSibling, e) {
    for (this._$AP?.(!1, !0, e); t !== this._$AB; ) {
      const s = X(t).nextSibling;
      X(t).remove(), t = s;
    }
  }
  setConnected(t) {
    this._$AM === void 0 && (this._$Cv = t, this._$AP?.(t));
  }
}
class R {
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  constructor(t, e, s, r, o) {
    this.type = 1, this._$AH = d, this._$AN = void 0, this.element = t, this.name = e, this._$AM = r, this.options = o, s.length > 2 || s[0] !== "" || s[1] !== "" ? (this._$AH = Array(s.length - 1).fill(new String()), this.strings = s) : this._$AH = d;
  }
  _$AI(t, e = this, s, r) {
    const o = this.strings;
    let n = !1;
    if (o === void 0) t = E(this, t, e, 0), n = !O(t) || t !== this._$AH && t !== A, n && (this._$AH = t);
    else {
      const a = t;
      let l, h;
      for (t = o[0], l = 0; l < o.length - 1; l++) h = E(this, a[s + l], e, l), h === A && (h = this._$AH[l]), n ||= !O(h) || h !== this._$AH[l], h === d ? t = d : t !== d && (t += (h ?? "") + o[l + 1]), this._$AH[l] = h;
    }
    n && !r && this.j(t);
  }
  j(t) {
    t === d ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, t ?? "");
  }
}
class Pt extends R {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(t) {
    this.element[this.name] = t === d ? void 0 : t;
  }
}
class Lt extends R {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(t) {
    this.element.toggleAttribute(this.name, !!t && t !== d);
  }
}
class Mt extends R {
  constructor(t, e, s, r, o) {
    super(t, e, s, r, o), this.type = 5;
  }
  _$AI(t, e = this) {
    if ((t = E(this, t, e, 0) ?? d) === A) return;
    const s = this._$AH, r = t === d && s !== d || t.capture !== s.capture || t.once !== s.once || t.passive !== s.passive, o = t !== d && (s === d || r);
    r && this.element.removeEventListener(this.name, this, s), o && this.element.addEventListener(this.name, this, t), this._$AH = t;
  }
  handleEvent(t) {
    typeof this._$AH == "function" ? this._$AH.call(this.options?.host ?? this.element, t) : this._$AH.handleEvent(t);
  }
}
class zt {
  constructor(t, e, s) {
    this.element = t, this.type = 6, this._$AN = void 0, this._$AM = e, this.options = s;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(t) {
    E(this, t);
  }
}
const Nt = Q.litHtmlPolyfillSupport;
Nt?.(P, L), (Q.litHtmlVersions ??= []).push("3.3.2");
const Tt = (i, t, e) => {
  const s = e?.renderBefore ?? t;
  let r = s._$litPart$;
  if (r === void 0) {
    const o = e?.renderBefore ?? null;
    s._$litPart$ = r = new L(t.insertBefore(C(), o), o, void 0, e ?? {});
  }
  return r._$AI(i), r;
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const W = globalThis;
class k extends b {
  constructor() {
    super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
  }
  createRenderRoot() {
    const t = super.createRenderRoot();
    return this.renderOptions.renderBefore ??= t.firstChild, t;
  }
  update(t) {
    const e = this.render();
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(t), this._$Do = Tt(e, this.renderRoot, this.renderOptions);
  }
  connectedCallback() {
    super.connectedCallback(), this._$Do?.setConnected(!0);
  }
  disconnectedCallback() {
    super.disconnectedCallback(), this._$Do?.setConnected(!1);
  }
  render() {
    return A;
  }
}
k._$litElement$ = !0, k.finalized = !0, W.litElementHydrateSupport?.({ LitElement: k });
const Ut = W.litElementPolyfillSupport;
Ut?.({ LitElement: k });
(W.litElementVersions ??= []).push("4.2.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const Ht = { attribute: !0, type: String, converter: T, reflect: !1, hasChanged: V }, Rt = (i = Ht, t, e) => {
  const { kind: s, metadata: r } = e;
  let o = globalThis.litPropertyMetadata.get(r);
  if (o === void 0 && globalThis.litPropertyMetadata.set(r, o = /* @__PURE__ */ new Map()), s === "setter" && ((i = Object.create(i)).wrapped = !0), o.set(e.name, i), s === "accessor") {
    const { name: n } = e;
    return { set(a) {
      const l = t.get.call(this);
      t.set.call(this, a), this.requestUpdate(n, l, i, !0, a);
    }, init(a) {
      return a !== void 0 && this.C(n, void 0, i, a), a;
    } };
  }
  if (s === "setter") {
    const { name: n } = e;
    return function(a) {
      const l = this[n];
      t.call(this, a), this.requestUpdate(n, l, i, !0, a);
    };
  }
  throw Error("Unsupported decorator location: " + s);
};
function pt(i) {
  return (t, e) => typeof e == "object" ? Rt(i, t, e) : ((s, r, o) => {
    const n = r.hasOwnProperty(o);
    return r.constructor.createProperty(o, s), n ? Object.getOwnPropertyDescriptor(r, o) : void 0;
  })(i, t, e);
}
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
function ft(i) {
  return pt({ ...i, state: !0, attribute: !1 });
}
class f extends Error {
  constructor(t) {
    super(t), this.name = "ConfigError";
  }
}
const z = /^[a-z_][a-z0-9_]*\.[a-z0-9_]+$/;
function jt(i) {
  if (!i || typeof i != "object")
    throw new f("Card config must be an object.");
  const t = i;
  if (typeof t.type != "string" || !t.type.includes("evenkeel-boat-card"))
    throw new f(`Bad or missing 'type' (got ${JSON.stringify(t.type)}).`);
  if (t.boat_name !== void 0 && typeof t.boat_name != "string")
    throw new f("'boat_name' must be a string.");
  if (t.overall_status !== void 0 && (typeof t.overall_status != "string" || !z.test(t.overall_status)))
    throw new f(`'overall_status' must be a valid entity_id, got ${JSON.stringify(t.overall_status)}.`);
  const e = {};
  if (t.zones !== void 0) {
    if (!t.zones || typeof t.zones != "object" || Array.isArray(t.zones))
      throw new f("'zones' must be a mapping of zone-name → zone config.");
    for (const [o, n] of Object.entries(t.zones)) {
      if (!n || typeof n != "object")
        throw new f(`Zone '${o}' must be an object.`);
      const a = n;
      if (typeof a.rollup != "string" || !z.test(a.rollup))
        throw new f(`Zone '${o}': 'rollup' must be a valid entity_id, got ${JSON.stringify(a.rollup)}.`);
      if (a.navigate !== void 0 && typeof a.navigate != "string")
        throw new f(`Zone '${o}': 'navigate' must be a string path.`);
      if (a.headline !== void 0 && typeof a.headline != "string")
        throw new f(`Zone '${o}': 'headline' must be a string.`);
      e[o] = {
        rollup: a.rollup,
        headline: a.headline,
        navigate: a.navigate
      };
    }
  }
  let s;
  if (t.power_flow !== void 0) {
    if (!t.power_flow || typeof t.power_flow != "object")
      throw new f("'power_flow' must be an object.");
    const o = t.power_flow;
    s = {};
    for (const n of ["shore", "generator", "solar", "battery_v", "battery_a"]) {
      const a = o[n];
      if (a !== void 0) {
        if (typeof a != "string" || !z.test(a))
          throw new f(`'power_flow.${n}' must be a valid entity_id.`);
        s[n] = a;
      }
    }
  }
  let r;
  if (t.footer_vitals !== void 0) {
    if (!Array.isArray(t.footer_vitals))
      throw new f("'footer_vitals' must be a list of entity_ids.");
    if (t.footer_vitals.length > 6)
      throw new f("'footer_vitals' supports at most 6 entries.");
    r = [];
    for (const o of t.footer_vitals) {
      if (typeof o != "string" || !z.test(o))
        throw new f(`'footer_vitals' entry ${JSON.stringify(o)} is not a valid entity_id.`);
      r.push(o);
    }
  }
  return {
    type: t.type,
    boat_name: t.boat_name,
    overall_status: t.overall_status,
    zones: Object.keys(e).length > 0 ? e : void 0,
    power_flow: s,
    footer_vitals: r
  };
}
const Bt = "0 0 800 320", Dt = u`
  <path
    d="M 30 90
       Q 25 70, 60 65
       Q 220 50, 380 60
       Q 560 60, 700 100
       Q 760 130, 780 160
       Q 760 190, 700 220
       Q 560 260, 380 260
       Q 220 270, 60 255
       Q 25 250, 30 230
       Z"
    fill="var(--card-background-color, #ffffff)"
    stroke="var(--primary-text-color, #1c1c1e)"
    stroke-width="2"
    stroke-linejoin="round"
  />`, It = u`
  <path
    d="M 50 95
       Q 220 75, 380 80
       Q 560 80, 690 115
       Q 740 140, 760 160
       Q 740 180, 690 205
       Q 560 240, 380 240
       Q 220 245, 50 225"
    fill="none"
    stroke="var(--primary-text-color, #1c1c1e)"
    stroke-width="1"
    stroke-opacity="0.25"
  />`, Zt = [
  // Stern → bow.
  {
    key: "lazarette",
    label: "LAZ",
    // Just inside the transom — shallow, full-beam.
    d: "M 45 95 L 110 90 L 110 230 L 45 225 Z",
    lx: 78,
    ly: 165
  },
  {
    key: "cockpit",
    label: "COCKPIT",
    // Slightly trapezoidal — narrower at the companionway end.
    d: "M 115 90 L 115 230 L 235 220 L 235 100 Z",
    lx: 175,
    ly: 165
  },
  {
    key: "engine_bay",
    label: "ENGINE",
    // Under the cockpit sole — narrower, centerline-biased.
    d: "M 240 110 L 240 210 L 320 205 L 320 115 Z",
    lx: 280,
    ly: 165
  },
  {
    key: "galley",
    label: "GALLEY",
    // Port side, just forward of the engine.
    d: "M 325 80 L 325 155 L 410 155 L 410 78 Z",
    lx: 367,
    ly: 122
  },
  {
    key: "nav_station",
    label: "NAV",
    // Starboard, mirror of galley.
    d: "M 325 165 L 325 240 L 410 242 L 410 165 Z",
    lx: 367,
    ly: 207
  },
  {
    key: "salon",
    label: "SALON",
    // Centerline mid — large, slightly tapered toward the bow.
    d: "M 415 90 L 415 230 L 555 220 L 555 100 Z",
    lx: 485,
    ly: 165
  },
  {
    key: "head",
    label: "HEAD",
    // Port-side mid-forward, between salon and V-berth.
    d: "M 560 95 L 560 155 L 640 145 L 640 100 Z",
    lx: 600,
    ly: 127
  },
  {
    key: "v_berth",
    label: "V-BERTH",
    // Forward — tapering toward the bow.
    d: "M 560 165 L 560 220 L 640 210 L 645 165 Z",
    lx: 600,
    ly: 192
  },
  {
    key: "forepeak",
    label: "FOREPEAK",
    // The pointy bow itself.
    d: "M 650 110 L 745 158 L 745 162 L 650 210 Z",
    lx: 690,
    ly: 165
  }
];
function Vt(i) {
  const t = `zone bilge-strip severity-${i}`;
  return u`
    <g class=${t} data-zone="bilge">
      <rect x="120" y="155" width="430" height="10"
            rx="4" ry="4"
            class="zone-bg"/>
    </g>`;
}
const Qt = u`
  <g aria-label="Mast" opacity="0.85">
    <circle cx="530" cy="160" r="6"
            fill="var(--card-background-color, #fff)"
            stroke="var(--primary-text-color, #1c1c1e)"
            stroke-width="1.5"/>
    <circle cx="530" cy="160" r="2.5"
            fill="var(--primary-text-color, #1c1c1e)"
            opacity="0.7"/>
  </g>`, Ft = u`
  <g aria-label="Helm" opacity="0.7">
    <circle cx="170" cy="160" r="9"
            fill="none"
            stroke="var(--primary-text-color, #1c1c1e)"
            stroke-width="1.2"/>
    <line x1="161" y1="160" x2="179" y2="160"
          stroke="var(--primary-text-color, #1c1c1e)"
          stroke-width="1.2"/>
    <line x1="170" y1="151" x2="170" y2="169"
          stroke="var(--primary-text-color, #1c1c1e)"
          stroke-width="1.2"/>
  </g>`, Wt = u`
  <path d="M 720 145 L 770 160 L 720 175"
        fill="none"
        stroke="var(--primary-text-color, #1c1c1e)"
        stroke-width="1.2"
        opacity="0.55"/>`, Kt = u`
  <g opacity="0.55">
    <path d="M 35 78 L 50 92"
          stroke="var(--primary-text-color, #1c1c1e)"
          stroke-width="1.2" fill="none"/>
    <path d="M 35 242 L 50 228"
          stroke="var(--primary-text-color, #1c1c1e)"
          stroke-width="1.2" fill="none"/>
  </g>`, qt = u`
  <g aria-label="Nav lights" opacity="0.85">
    <circle cx="745" cy="155" r="2.5" fill="#22c55e"/>   <!-- starboard green -->
    <circle cx="745" cy="165" r="2.5" fill="#ef4444"/>   <!-- port red -->
    <circle cx="40"  cy="160" r="2.5" fill="#f8fafc"
            stroke="var(--primary-text-color, #1c1c1e)"
            stroke-width="0.8"/>                          <!-- stern white -->
  </g>`;
function Jt(i) {
  return u`
    ${Dt}
    ${It}
    ${Zt.map((t) => {
    const s = `zone severity-${i[t.key] ?? "ok"}`;
    return u`
        <g class=${s} data-zone=${t.key}>
          <path d=${t.d} class="zone-bg"/>
          <text x=${t.lx} y=${t.ly + 4}
                text-anchor="middle"
                class="zone-label"
                font-size="11"
                fill="var(--primary-text-color, #1c1c1e)"
                opacity="0.8">
            ${t.label}
          </text>
        </g>
      `;
  })}
    ${Vt(i.bilge ?? "ok")}
    ${Ft}
    ${Qt}
    ${Wt}
    ${Kt}
    ${qt}
  `;
}
function ut(i) {
  return i === "warning" ? "warning" : i === "critical" ? "critical" : "ok";
}
function Gt(i) {
  return i.includes("critical") ? "critical" : i.includes("warning") ? "warning" : "ok";
}
function Yt(i, t) {
  if (i == null || i === "") return "—";
  const e = typeof i == "string" ? parseFloat(i) : i;
  if (Number.isNaN(e)) return String(i);
  const s = Math.abs(e) >= 100 ? Math.round(e) : Math.round(e * 10) / 10;
  return t ? `${s} ${t}` : `${s}`;
}
function Xt(i) {
  return i === void 0 || Number.isNaN(i) || Math.abs(i) < 0.5 ? 0 : i > 0 ? 1 : -1;
}
function te(i, t) {
  const e = {};
  if (!i) return e;
  for (const [s, r] of Object.entries(i)) {
    const o = t?.[r.rollup];
    e[s] = o ? ut(o.state) : "ok";
  }
  return e;
}
function ee(i, t, e) {
  if (i && t) {
    const s = t[i];
    if (s) {
      const r = s.attributes?.headline;
      if (typeof r == "string" && r.length > 0) return r;
    }
  }
  return e === "critical" ? "Action needed." : e === "warning" ? "Heads up." : "All good.";
}
var se = Object.defineProperty, K = (i, t, e, s) => {
  for (var r = void 0, o = i.length - 1, n; o >= 0; o--)
    (n = i[o]) && (r = n(t, e, r) || r);
  return r && se(t, e, r), r;
};
class j extends k {
  static {
    this.styles = $t`
    :host {
      display: block;
    }
    ha-card,
    .card {
      box-sizing: border-box;
      padding: 16px;
      border-radius: var(--ha-card-border-radius, 16px);
      background: var(--ha-card-background, var(--card-background-color, #fff));
      color: var(--primary-text-color, #1c1c1e);
      font-family: var(--paper-font-body1_-_font-family, sans-serif);
    }
    .header {
      display: flex;
      align-items: baseline;
      gap: 12px;
      margin-bottom: 8px;
    }
    .header h2 {
      margin: 0;
      font-size: 1.1rem;
      font-weight: 600;
      letter-spacing: -0.01em;
    }
    .glance {
      flex: 1 1 auto;
      font-size: 0.95rem;
      color: var(--primary-text-color);
    }
    .glance.severity-warning {
      color: var(--evenkeel-warn, #f59e0b);
      font-weight: 600;
    }
    .glance.severity-critical {
      color: var(--evenkeel-crit, #ef4444);
      font-weight: 700;
    }
    svg.boat {
      display: block;
      width: 100%;
      height: auto;
      max-height: 360px;
    }
    .zone {
      cursor: pointer;
      transition: transform 0.2s ease;
    }
    .zone:hover {
      transform: scale(1.02);
      transform-origin: center;
    }
    .zone .zone-bg {
      fill: var(--evenkeel-ok, #22c55e);
      fill-opacity: 0.18;
      stroke: var(--primary-text-color, #1c1c1e);
      stroke-opacity: 0.35;
      stroke-width: 1;
    }
    .zone.severity-warning .zone-bg {
      fill: var(--evenkeel-warn, #f59e0b);
      fill-opacity: 0.45;
      animation: pulse-warn 1.5s ease-in-out infinite;
    }
    .zone.severity-critical .zone-bg {
      fill: var(--evenkeel-crit, #ef4444);
      fill-opacity: 0.65;
      animation: pulse-crit 1.0s ease-in-out infinite;
    }
    @keyframes pulse-warn {
      50% { fill-opacity: 0.65; }
    }
    @keyframes pulse-crit {
      50% { fill-opacity: 0.95; }
    }
    .powerflow {
      margin-top: 8px;
      font-size: 0.85rem;
      color: var(--secondary-text-color, #5a5a5e);
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }
    .powerflow svg {
      flex: 1 1 200px;
      height: 24px;
    }
    .powerflow .ant-line {
      stroke: var(--evenkeel-ok, #22c55e);
      stroke-width: 2;
      stroke-dasharray: 4 4;
      fill: none;
    }
    .powerflow.flow-charging .ant-line {
      animation: ants-fwd 0.8s linear infinite;
    }
    .powerflow.flow-discharging .ant-line {
      animation: ants-rev 0.8s linear infinite;
      stroke: var(--evenkeel-warn, #f59e0b);
    }
    @keyframes ants-fwd {
      to { stroke-dashoffset: -8; }
    }
    @keyframes ants-rev {
      to { stroke-dashoffset: 8; }
    }
    .vitals {
      display: flex;
      gap: 18px;
      margin-top: 12px;
      padding-top: 12px;
      border-top: 1px solid var(--divider-color, rgba(0, 0, 0, 0.08));
      font-size: 0.85rem;
      color: var(--secondary-text-color, #5a5a5e);
      flex-wrap: wrap;
    }
    .vital {
      display: inline-flex;
      gap: 6px;
      align-items: baseline;
    }
    .vital .key {
      font-size: 0.7rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .vital .val {
      font-variant-numeric: tabular-nums;
      font-weight: 600;
      color: var(--primary-text-color, #1c1c1e);
    }
    .error {
      color: var(--evenkeel-crit, #ef4444);
      padding: 12px;
      font-family: monospace;
      font-size: 0.85rem;
    }
  `;
  }
  // Lovelace calls this when the user changes config in the GUI editor;
  // we use it for validation on the YAML-config path too.
  setConfig(t) {
    try {
      this._config = jt(t), this._configError = void 0;
    } catch (e) {
      e instanceof f ? this._configError = e.message : e instanceof Error ? this._configError = `Unexpected: ${e.message}` : this._configError = String(e);
    }
  }
  // Lovelace asks for a row size estimate. Card is roughly 5 rows tall.
  getCardSize() {
    return 5;
  }
  render() {
    if (this._configError)
      return g`<div class="card error">EvenKeel boat card config error: ${this._configError}</div>`;
    if (!this._config)
      return g`<div class="card">Loading…</div>`;
    const t = this._config, e = this.hass, s = te(t.zones, e?.states), r = t.overall_status && e?.states[t.overall_status] ? ut(e.states[t.overall_status].state) : Gt(Object.values(s)), o = ee(t.overall_status, e?.states, r), n = this._numericState(e, t.power_flow?.battery_a), a = Xt(n);
    return g`
      <ha-card class="card">
        <div class="header">
          <h2>${t.boat_name ?? "Boat"}</h2>
          <span class="glance severity-${r}">${o}</span>
        </div>
        <svg class="boat" viewBox="${Bt}" role="img" aria-label="Boat overview"
             @click=${this._onSvgClick.bind(this)}>
          ${Jt(s)}
        </svg>
        ${this._renderPowerFlow(t, a)}
        ${this._renderVitals(t, e)}
      </ha-card>
    `;
  }
  _numericState(t, e) {
    if (!t || !e) return;
    const s = t.states[e];
    if (!s) return;
    const r = parseFloat(s.state);
    return Number.isNaN(r) ? void 0 : r;
  }
  _onSvgClick(t) {
    const e = t.target;
    if (!e) return;
    const s = e.closest(".zone");
    if (!s) return;
    const r = s.dataset.zone;
    if (!r) return;
    const o = this._config?.zones?.[r]?.navigate;
    o && (history.pushState(null, "", o), window.dispatchEvent(new CustomEvent("location-changed", { composed: !0 })));
  }
  _renderPowerFlow(t, e) {
    if (!t.power_flow) return g``;
    const s = e === 1 ? "flow-charging" : e === -1 ? "flow-discharging" : "", r = t.power_flow.shore && this._isOn(t.power_flow.shore) ? "SHORE" : t.power_flow.generator && this._isOn(t.power_flow.generator) ? "GEN" : t.power_flow.solar && (this._numericState(this.hass, t.power_flow.solar) ?? 0) > 5 ? "SOLAR" : "BATTERY", o = this._numericState(this.hass, t.power_flow.battery_v), n = o !== void 0 ? `${o.toFixed(1)} V` : "—";
    return g`
      <div class="powerflow ${s}" aria-label="Power flow ${r} to battery">
        <span>${r}</span>
        <svg viewBox="0 0 200 24" preserveAspectRatio="none" aria-hidden="true">
          <path class="ant-line" d="M 5 12 L 195 12"/>
        </svg>
        <span>BATT ${n}</span>
      </div>
    `;
  }
  _isOn(t) {
    return this.hass?.states[t]?.state === "on";
  }
  _renderVitals(t, e) {
    return !t.footer_vitals || t.footer_vitals.length === 0 ? g`` : g`
      <div class="vitals">
        ${t.footer_vitals.map((s) => {
      const r = e?.states[s], o = r?.attributes?.friendly_name ?? s, n = r?.attributes?.unit_of_measurement, a = r ? Yt(r.state, n) : "—", l = o.split(" ").slice(-2).join(" ");
      return g`<span class="vital"><span class="key">${l}</span><span class="val">${a}</span></span>`;
    })}
      </div>
    `;
  }
}
K([
  pt({ attribute: !1 })
], j.prototype, "hass");
K([
  ft()
], j.prototype, "_config");
K([
  ft()
], j.prototype, "_configError");
customElements.get("evenkeel-boat-card") || customElements.define("evenkeel-boat-card", j);
const D = window;
D.customCards = D.customCards || [];
D.customCards.push({
  type: "evenkeel-boat-card",
  name: "EvenKeel Boat Card",
  description: "Top-down sailboat diagram with severity overlays + animated power flow",
  preview: !1
});
export {
  j as EvenKeelBoatCard,
  j as default
};
//# sourceMappingURL=evenkeel-boat-card.js.map
