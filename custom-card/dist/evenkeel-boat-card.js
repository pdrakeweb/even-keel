/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const U = globalThis, I = U.ShadowRoot && (U.ShadyCSS === void 0 || U.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, V = Symbol(), J = /* @__PURE__ */ new WeakMap();
let nt = class {
  constructor(t, e, s) {
    if (this._$cssResult$ = !0, s !== V) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = t, this.t = e;
  }
  get styleSheet() {
    let t = this.o;
    const e = this.t;
    if (I && t === void 0) {
      const s = e !== void 0 && e.length === 1;
      s && (t = J.get(e)), t === void 0 && ((this.o = t = new CSSStyleSheet()).replaceSync(this.cssText), s && J.set(e, t));
    }
    return t;
  }
  toString() {
    return this.cssText;
  }
};
const $t = (i) => new nt(typeof i == "string" ? i : i + "", void 0, V), _t = (i, ...t) => {
  const e = i.length === 1 ? i[0] : t.reduce((s, r, o) => s + ((n) => {
    if (n._$cssResult$ === !0) return n.cssText;
    if (typeof n == "number") return n;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + n + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(r) + i[o + 1], i[0]);
  return new nt(e, i, V);
}, gt = (i, t) => {
  if (I) i.adoptedStyleSheets = t.map((e) => e instanceof CSSStyleSheet ? e : e.styleSheet);
  else for (const e of t) {
    const s = document.createElement("style"), r = U.litNonce;
    r !== void 0 && s.setAttribute("nonce", r), s.textContent = e.cssText, i.appendChild(s);
  }
}, Q = I ? (i) => i : (i) => i instanceof CSSStyleSheet ? ((t) => {
  let e = "";
  for (const s of t.cssRules) e += s.cssText;
  return $t(e);
})(i) : i;
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const { is: vt, defineProperty: yt, getOwnPropertyDescriptor: mt, getOwnPropertyNames: wt, getOwnPropertySymbols: bt, getPrototypeOf: At } = Object, R = globalThis, G = R.trustedTypes, Et = G ? G.emptyScript : "", xt = R.reactiveElementPolyfillSupport, S = (i, t) => i, M = { toAttribute(i, t) {
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
} }, Z = (i, t) => !vt(i, t), Y = { attribute: !0, type: String, converter: M, reflect: !1, useDefault: !1, hasChanged: Z };
Symbol.metadata ??= Symbol("metadata"), R.litPropertyMetadata ??= /* @__PURE__ */ new WeakMap();
let w = class extends HTMLElement {
  static addInitializer(t) {
    this._$Ei(), (this.l ??= []).push(t);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(t, e = Y) {
    if (e.state && (e.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(t) && ((e = Object.create(e)).wrapped = !0), this.elementProperties.set(t, e), !e.noAccessor) {
      const s = Symbol(), r = this.getPropertyDescriptor(t, s, e);
      r !== void 0 && yt(this.prototype, t, r);
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
      for (const r of s) e.unshift(Q(r));
    } else t !== void 0 && e.push(Q(t));
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
      const o = (s.converter?.toAttribute !== void 0 ? s.converter : M).toAttribute(e, s.type);
      this._$Em = t, o == null ? this.removeAttribute(r) : this.setAttribute(r, o), this._$Em = null;
    }
  }
  _$AK(t, e) {
    const s = this.constructor, r = s._$Eh.get(t);
    if (r !== void 0 && this._$Em !== r) {
      const o = s.getPropertyOptions(r), n = typeof o.converter == "function" ? { fromAttribute: o.converter } : o.converter?.fromAttribute !== void 0 ? o.converter : M;
      this._$Em = r;
      const a = n.fromAttribute(e, o.type);
      this[r] = a ?? this._$Ej?.get(r) ?? a, this._$Em = null;
    }
  }
  requestUpdate(t, e, s, r = !1, o) {
    if (t !== void 0) {
      const n = this.constructor;
      if (r === !1 && (o = this[t]), s ??= n.getPropertyOptions(t), !((s.hasChanged ?? Z)(o, e) || s.useDefault && s.reflect && o === this._$Ej?.get(t) && !this.hasAttribute(n._$Eu(t, s)))) return;
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
w.elementStyles = [], w.shadowRootOptions = { mode: "open" }, w[S("elementProperties")] = /* @__PURE__ */ new Map(), w[S("finalized")] = /* @__PURE__ */ new Map(), xt?.({ ReactiveElement: w }), (R.reactiveElementVersions ??= []).push("2.1.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const F = globalThis, X = (i) => i, H = F.trustedTypes, tt = H ? H.createPolicy("lit-html", { createHTML: (i) => i }) : void 0, at = "$lit$", g = `lit$${Math.random().toFixed(9).slice(2)}$`, lt = "?" + g, St = `<${lt}>`, m = document, C = () => m.createComment(""), O = (i) => i === null || typeof i != "object" && typeof i != "function", K = Array.isArray, kt = (i) => K(i) || typeof i?.[Symbol.iterator] == "function", B = `[ 	
\f\r]`, x = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, et = /-->/g, st = />/g, v = RegExp(`>|${B}(?:([^\\s"'>=/]+)(${B}*=${B}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g"), rt = /'/g, it = /"/g, ct = /^(?:script|style|textarea|title)$/i, ht = (i) => (t, ...e) => ({ _$litType$: i, strings: t, values: e }), _ = ht(1), b = ht(2), A = Symbol.for("lit-noChange"), d = Symbol.for("lit-nothing"), ot = /* @__PURE__ */ new WeakMap(), y = m.createTreeWalker(m, 129);
function dt(i, t) {
  if (!K(i) || !i.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return tt !== void 0 ? tt.createHTML(t) : t;
}
const Ct = (i, t) => {
  const e = i.length - 1, s = [];
  let r, o = t === 2 ? "<svg>" : t === 3 ? "<math>" : "", n = x;
  for (let a = 0; a < e; a++) {
    const l = i[a];
    let h, p, c = -1, u = 0;
    for (; u < l.length && (n.lastIndex = u, p = n.exec(l), p !== null); ) u = n.lastIndex, n === x ? p[1] === "!--" ? n = et : p[1] !== void 0 ? n = st : p[2] !== void 0 ? (ct.test(p[2]) && (r = RegExp("</" + p[2], "g")), n = v) : p[3] !== void 0 && (n = v) : n === v ? p[0] === ">" ? (n = r ?? x, c = -1) : p[1] === void 0 ? c = -2 : (c = n.lastIndex - p[2].length, h = p[1], n = p[3] === void 0 ? v : p[3] === '"' ? it : rt) : n === it || n === rt ? n = v : n === et || n === st ? n = x : (n = v, r = void 0);
    const $ = n === v && i[a + 1].startsWith("/>") ? " " : "";
    o += n === x ? l + St : c >= 0 ? (s.push(h), l.slice(0, c) + at + l.slice(c) + g + $) : l + g + (c === -2 ? a : $);
  }
  return [dt(i, o + (i[e] || "<?>") + (t === 2 ? "</svg>" : t === 3 ? "</math>" : "")), s];
};
class P {
  constructor({ strings: t, _$litType$: e }, s) {
    let r;
    this.parts = [];
    let o = 0, n = 0;
    const a = t.length - 1, l = this.parts, [h, p] = Ct(t, e);
    if (this.el = P.createElement(h, s), y.currentNode = this.el.content, e === 2 || e === 3) {
      const c = this.el.content.firstChild;
      c.replaceWith(...c.childNodes);
    }
    for (; (r = y.nextNode()) !== null && l.length < a; ) {
      if (r.nodeType === 1) {
        if (r.hasAttributes()) for (const c of r.getAttributeNames()) if (c.endsWith(at)) {
          const u = p[n++], $ = r.getAttribute(c).split(g), z = /([.?@])?(.*)/.exec(u);
          l.push({ type: 1, index: o, name: z[2], strings: $, ctor: z[1] === "." ? Pt : z[1] === "?" ? Nt : z[1] === "@" ? zt : j }), r.removeAttribute(c);
        } else c.startsWith(g) && (l.push({ type: 6, index: o }), r.removeAttribute(c));
        if (ct.test(r.tagName)) {
          const c = r.textContent.split(g), u = c.length - 1;
          if (u > 0) {
            r.textContent = H ? H.emptyScript : "";
            for (let $ = 0; $ < u; $++) r.append(c[$], C()), y.nextNode(), l.push({ type: 2, index: ++o });
            r.append(c[u], C());
          }
        }
      } else if (r.nodeType === 8) if (r.data === lt) l.push({ type: 2, index: o });
      else {
        let c = -1;
        for (; (c = r.data.indexOf(g, c + 1)) !== -1; ) l.push({ type: 7, index: o }), c += g.length - 1;
      }
      o++;
    }
  }
  static createElement(t, e) {
    const s = m.createElement("template");
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
    const { el: { content: e }, parts: s } = this._$AD, r = (t?.creationScope ?? m).importNode(e, !0);
    y.currentNode = r;
    let o = y.nextNode(), n = 0, a = 0, l = s[0];
    for (; l !== void 0; ) {
      if (n === l.index) {
        let h;
        l.type === 2 ? h = new N(o, o.nextSibling, this, t) : l.type === 1 ? h = new l.ctor(o, l.name, l.strings, this, t) : l.type === 6 && (h = new Tt(o, this, t)), this._$AV.push(h), l = s[++a];
      }
      n !== l?.index && (o = y.nextNode(), n++);
    }
    return y.currentNode = m, r;
  }
  p(t) {
    let e = 0;
    for (const s of this._$AV) s !== void 0 && (s.strings !== void 0 ? (s._$AI(t, s, e), e += s.strings.length - 2) : s._$AI(t[e])), e++;
  }
}
class N {
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
    this._$AH !== d && O(this._$AH) ? this._$AA.nextSibling.data = t : this.T(m.createTextNode(t)), this._$AH = t;
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
    K(this._$AH) || (this._$AH = [], this._$AR());
    const e = this._$AH;
    let s, r = 0;
    for (const o of t) r === e.length ? e.push(s = new N(this.O(C()), this.O(C()), this, this.options)) : s = e[r], s._$AI(o), r++;
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
class j {
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
class Pt extends j {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(t) {
    this.element[this.name] = t === d ? void 0 : t;
  }
}
class Nt extends j {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(t) {
    this.element.toggleAttribute(this.name, !!t && t !== d);
  }
}
class zt extends j {
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
class Tt {
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
const Ut = F.litHtmlPolyfillSupport;
Ut?.(P, N), (F.litHtmlVersions ??= []).push("3.3.2");
const Mt = (i, t, e) => {
  const s = e?.renderBefore ?? t;
  let r = s._$litPart$;
  if (r === void 0) {
    const o = e?.renderBefore ?? null;
    s._$litPart$ = r = new N(t.insertBefore(C(), o), o, void 0, e ?? {});
  }
  return r._$AI(i), r;
};
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const W = globalThis;
class k extends w {
  constructor() {
    super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
  }
  createRenderRoot() {
    const t = super.createRenderRoot();
    return this.renderOptions.renderBefore ??= t.firstChild, t;
  }
  update(t) {
    const e = this.render();
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(t), this._$Do = Mt(e, this.renderRoot, this.renderOptions);
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
const Ht = W.litElementPolyfillSupport;
Ht?.({ LitElement: k });
(W.litElementVersions ??= []).push("4.2.2");
/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const Rt = { attribute: !0, type: String, converter: M, reflect: !1, hasChanged: Z }, jt = (i = Rt, t, e) => {
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
  return (t, e) => typeof e == "object" ? jt(i, t, e) : ((s, r, o) => {
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
const T = /^[a-z_][a-z0-9_]*\.[a-z0-9_]+$/;
function Lt(i) {
  if (!i || typeof i != "object")
    throw new f("Card config must be an object.");
  const t = i;
  if (typeof t.type != "string" || !t.type.includes("evenkeel-boat-card"))
    throw new f(`Bad or missing 'type' (got ${JSON.stringify(t.type)}).`);
  if (t.boat_name !== void 0 && typeof t.boat_name != "string")
    throw new f("'boat_name' must be a string.");
  if (t.overall_status !== void 0 && (typeof t.overall_status != "string" || !T.test(t.overall_status)))
    throw new f(`'overall_status' must be a valid entity_id, got ${JSON.stringify(t.overall_status)}.`);
  const e = {};
  if (t.zones !== void 0) {
    if (!t.zones || typeof t.zones != "object" || Array.isArray(t.zones))
      throw new f("'zones' must be a mapping of zone-name → zone config.");
    for (const [o, n] of Object.entries(t.zones)) {
      if (!n || typeof n != "object")
        throw new f(`Zone '${o}' must be an object.`);
      const a = n;
      if (typeof a.rollup != "string" || !T.test(a.rollup))
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
        if (typeof a != "string" || !T.test(a))
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
      if (typeof o != "string" || !T.test(o))
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
const Bt = "0 0 800 320", Dt = b`
  <path
    d="M 30 160
       Q 30 100, 90 80
       L 700 80
       Q 770 80, 770 160
       Q 770 240, 700 260
       L 90 260
       Q 30 220, 30 160 Z"
    fill="var(--card-background-color, #ffffff)"
    stroke="var(--primary-text-color, #1c1c1e)"
    stroke-width="2"
  />`, It = [
  { key: "lazarette", label: "LAZ", x: 50, y: 100, w: 90, h: 120, r: 12 },
  { key: "cockpit", label: "COCKPIT", x: 145, y: 95, w: 110, h: 130, r: 10 },
  { key: "engine_bay", label: "ENGINE", x: 260, y: 110, w: 90, h: 100, r: 8 },
  { key: "galley", label: "GALLEY", x: 355, y: 95, w: 80, h: 60, r: 6 },
  { key: "nav_station", label: "NAV", x: 355, y: 165, w: 80, h: 60, r: 6 },
  { key: "head", label: "HEAD", x: 440, y: 95, w: 60, h: 60, r: 6 },
  { key: "salon", label: "SALON", x: 440, y: 165, w: 110, h: 60, r: 6 },
  { key: "v_berth", label: "V-BERTH", x: 555, y: 95, w: 130, h: 130, r: 12 },
  { key: "forepeak", label: "FOREPEAK", x: 690, y: 110, w: 70, h: 100, r: 14 }
];
function Vt(i) {
  const t = `zone bilge-strip severity-${i}`;
  return b`
    <g class=${t} data-zone="bilge">
      <rect x="100" y="220" width="600" height="20"
            rx="6" ry="6"
            class="zone-bg"/>
    </g>`;
}
const Zt = b`
  <path d="M 350 260 Q 400 285, 450 260" fill="none"
        stroke="var(--secondary-text-color, #5a5a5e)"
        stroke-width="2" stroke-linecap="round" opacity="0.4"/>`, Ft = b`<circle cx="495" cy="195" r="4"
  fill="var(--secondary-text-color, #5a5a5e)" opacity="0.6"/>`;
function Kt(i) {
  return b`
    ${Dt}
    ${It.map((t) => {
    const s = `zone severity-${i[t.key] ?? "ok"}`;
    return b`
        <g class=${s} data-zone=${t.key}>
          <rect x=${t.x} y=${t.y} width=${t.w} height=${t.h}
                rx=${t.r ?? 6} ry=${t.r ?? 6}
                class="zone-bg"/>
          <text x=${t.x + t.w / 2} y=${t.y + t.h / 2 + 4}
                text-anchor="middle"
                class="zone-label"
                font-size="11"
                fill="var(--primary-text-color, #1c1c1e)"
                opacity="0.75">
            ${t.label}
          </text>
        </g>
      `;
  })}
    ${Vt(i.bilge ?? "ok")}
    ${Zt}
    ${Ft}
  `;
}
function ut(i) {
  return i === "warning" ? "warning" : i === "critical" ? "critical" : "ok";
}
function Wt(i) {
  return i.includes("critical") ? "critical" : i.includes("warning") ? "warning" : "ok";
}
function qt(i, t) {
  if (i == null || i === "") return "—";
  const e = typeof i == "string" ? parseFloat(i) : i;
  if (Number.isNaN(e)) return String(i);
  const s = Math.abs(e) >= 100 ? Math.round(e) : Math.round(e * 10) / 10;
  return t ? `${s} ${t}` : `${s}`;
}
function Jt(i) {
  return i === void 0 || Number.isNaN(i) || Math.abs(i) < 0.5 ? 0 : i > 0 ? 1 : -1;
}
function Qt(i, t) {
  const e = {};
  if (!i) return e;
  for (const [s, r] of Object.entries(i)) {
    const o = t?.[r.rollup];
    e[s] = o ? ut(o.state) : "ok";
  }
  return e;
}
function Gt(i, t, e) {
  if (i && t) {
    const s = t[i];
    if (s) {
      const r = s.attributes?.headline;
      if (typeof r == "string" && r.length > 0) return r;
    }
  }
  return e === "critical" ? "Action needed." : e === "warning" ? "Heads up." : "All good.";
}
var Yt = Object.defineProperty, q = (i, t, e, s) => {
  for (var r = void 0, o = i.length - 1, n; o >= 0; o--)
    (n = i[o]) && (r = n(t, e, r) || r);
  return r && Yt(t, e, r), r;
};
class L extends k {
  static {
    this.styles = _t`
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
      this._config = Lt(t), this._configError = void 0;
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
      return _`<div class="card error">EvenKeel boat card config error: ${this._configError}</div>`;
    if (!this._config)
      return _`<div class="card">Loading…</div>`;
    const t = this._config, e = this.hass, s = Qt(t.zones, e?.states), r = t.overall_status && e?.states[t.overall_status] ? ut(e.states[t.overall_status].state) : Wt(Object.values(s)), o = Gt(t.overall_status, e?.states, r), n = this._numericState(e, t.power_flow?.battery_a), a = Jt(n);
    return _`
      <ha-card class="card">
        <div class="header">
          <h2>${t.boat_name ?? "Boat"}</h2>
          <span class="glance severity-${r}">${o}</span>
        </div>
        <svg class="boat" viewBox="${Bt}" role="img" aria-label="Boat overview"
             @click=${this._onSvgClick.bind(this)}>
          ${Kt(s)}
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
    if (!t.power_flow) return _``;
    const s = e === 1 ? "flow-charging" : e === -1 ? "flow-discharging" : "", r = t.power_flow.shore && this._isOn(t.power_flow.shore) ? "SHORE" : t.power_flow.generator && this._isOn(t.power_flow.generator) ? "GEN" : t.power_flow.solar && (this._numericState(this.hass, t.power_flow.solar) ?? 0) > 5 ? "SOLAR" : "BATTERY", o = this._numericState(this.hass, t.power_flow.battery_v), n = o !== void 0 ? `${o.toFixed(1)} V` : "—";
    return _`
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
    return !t.footer_vitals || t.footer_vitals.length === 0 ? _`` : _`
      <div class="vitals">
        ${t.footer_vitals.map((s) => {
      const r = e?.states[s], o = r?.attributes?.friendly_name ?? s, n = r?.attributes?.unit_of_measurement, a = r ? qt(r.state, n) : "—", l = o.split(" ").slice(-2).join(" ");
      return _`<span class="vital"><span class="key">${l}</span><span class="val">${a}</span></span>`;
    })}
      </div>
    `;
  }
}
q([
  pt({ attribute: !1 })
], L.prototype, "hass");
q([
  ft()
], L.prototype, "_config");
q([
  ft()
], L.prototype, "_configError");
customElements.get("evenkeel-boat-card") || customElements.define("evenkeel-boat-card", L);
const D = window;
D.customCards = D.customCards || [];
D.customCards.push({
  type: "evenkeel-boat-card",
  name: "EvenKeel Boat Card",
  description: "Top-down sailboat diagram with severity overlays + animated power flow",
  preview: !1
});
export {
  L as EvenKeelBoatCard,
  L as default
};
//# sourceMappingURL=evenkeel-boat-card.js.map
