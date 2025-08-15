// dom.js - DOM 工具
export const qs = (sel, ctx=document) => ctx.querySelector(sel);
export const qsa = (sel, ctx=document) => Array.from(ctx.querySelectorAll(sel));
export const createEl = (tag, opts={}) => Object.assign(document.createElement(tag), opts);
export const on = (el, ev, fn, opt) => el && el.addEventListener(ev, fn, opt);
export const off = (el, ev, fn, opt) => el && el.removeEventListener(ev, fn, opt);
export const addClass = (el, c) => el && el.classList.add(c);
export const removeClass = (el, c) => el && el.classList.remove(c);