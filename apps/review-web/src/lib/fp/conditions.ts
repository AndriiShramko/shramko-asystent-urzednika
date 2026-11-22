// SHOW conditions of the partner's JSON, read in the one shape our composer writes (the same atom the service's
// own check reads, app/gate/conditions.py): "literal" in tabs['T' in title].questions['s' in field.techName]
// .field.repeatingSectionGrid['f' in field.techName].field.__userAnswer, joined by and, or, $not( ) and brackets.
// Anything else does not parse: the page then keeps the field visible and says the condition was not read.
import { refKey } from './form'

export type Cond =
  | { k: 'atom'; lit: string; key: string }
  | { k: 'not'; a: Cond }
  | { k: 'and' | 'or'; a: Cond; b: Cond }

const Q = String.raw`\s*'([^']*)'\s+in\s+`
const REF = new RegExp(String.raw`^tabs\[` + Q + String.raw`title\s*\]\s*\.\s*questions\[` + Q +
  String.raw`field\s*\.\s*techName\s*\]\s*\.\s*field\s*\.\s*repeatingSectionGrid\[` + Q +
  String.raw`field\s*\.\s*techName\s*\]\s*\.\s*field\s*\.\s*__userAnswer(?:\s*\[\s*\$repeatingSectionIndex\s*\])?`)
const STRING = /^"((?:[^"\\]|\\.)*)"/

type Tok = { t: 'str'; v: string } | { t: 'ref'; v: string } | { t: 'in' | 'and' | 'or' | 'not' | '(' | ')' }

function tokenize(src: string): Tok[] | null {
  const out: Tok[] = []
  let s = src
  while (true) {
    s = s.replace(/^\s+/, '')
    if (!s) return out
    let m: RegExpMatchArray | null
    if ((m = s.match(STRING))) { out.push({ t: 'str', v: JSON.parse('"' + m[1] + '"') as string }); s = s.slice(m[0].length); continue }
    if ((m = s.match(REF))) { out.push({ t: 'ref', v: refKey(m[1], m[2], m[3]) }); s = s.slice(m[0].length); continue }
    if ((m = s.match(/^\$not\s*(?=\()/))) { out.push({ t: 'not' }); s = s.slice(m[0].length); continue }
    if ((m = s.match(/^(in|and|or)\b/))) { out.push({ t: m[1] as 'in' | 'and' | 'or' }); s = s.slice(m[0].length); continue }
    if (s[0] === '(' || s[0] === ')') { out.push({ t: s[0] }); s = s.slice(1); continue }
    return null
  }
}

/** The condition as a tree, or null when it is not in the known shape. */
export function parseCondition(src: string): Cond | null {
  let toks: Tok[] | null
  try { toks = tokenize(src) } catch { return null }
  if (!toks || !toks.length) return null
  let i = 0
  const peek = (): Tok | undefined => toks![i]
  const or = (): Cond | null => {
    let a = and()
    while (a && peek()?.t === 'or') { i++; const b = and(); if (!b) return null; a = { k: 'or', a, b } }
    return a
  }
  const and = (): Cond | null => {
    let a = unary()
    while (a && peek()?.t === 'and') { i++; const b = unary(); if (!b) return null; a = { k: 'and', a, b } }
    return a
  }
  const unary = (): Cond | null => {
    const t = peek()
    if (!t) return null
    if (t.t === 'not') {
      i++
      if (peek()?.t !== '(') return null
      i++
      const a = or()
      if (!a || peek()?.t !== ')') return null
      i++
      return { k: 'not', a }
    }
    if (t.t === '(') {
      i++
      const a = or()
      if (!a || peek()?.t !== ')') return null
      i++
      return a
    }
    if (t.t === 'str') {
      const kw = toks![i + 1]
      const ref = toks![i + 2]
      if (kw?.t !== 'in' || ref?.t !== 'ref') return null
      i += 3
      return { k: 'atom', lit: t.v, key: ref.v }
    }
    return null
  }
  const tree = or()
  return tree && i === toks.length ? tree : null
}

export type Lookup = (key: string) => string[]

export function evaluate(c: Cond, look: Lookup): boolean {
  switch (c.k) {
    case 'atom': return look(c.key).includes(c.lit)
    case 'not': return !evaluate(c.a, look)
    case 'and': return evaluate(c.a, look) && evaluate(c.b, look)
    case 'or': return evaluate(c.a, look) || evaluate(c.b, look)
  }
}

/** The chosen answers that make a true condition true (positive atoms that hold), for "visible because". */
export function reasons(c: Cond, look: Lookup, negated = false): string[] {
  switch (c.k) {
    case 'atom': return !negated && look(c.key).includes(c.lit) ? [c.lit] : []
    case 'not': return reasons(c.a, look, !negated)
    default: return [...reasons(c.a, look, negated), ...reasons(c.b, look, negated)]
  }
}

/** Every answer key a condition reads. */
export function keysOf(c: Cond): string[] {
  if (c.k === 'atom') return [c.key]
  if (c.k === 'not') return keysOf(c.a)
  return [...keysOf(c.a), ...keysOf(c.b)]
}
