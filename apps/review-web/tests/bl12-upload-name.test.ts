// BL12: the page sends a cleaned copy of the file name, so the clerk is never asked to rename a file, while the
// service refuses the names the task card forbids (400 BAD_NAME) to any other caller.
import { describe, expect, it } from 'vitest'
import { uploadName } from '../src/lib/api'

describe('uploadName', () => {
  it('keeps a good name as it is', () => {
    expect(uploadName('Wniosek o przyznanie stypendium.pdf')).toBe('Wniosek o przyznanie stypendium.pdf')
  })
  it('removes every character the task card forbids', () => {
    expect(uploadName("a;b:c>d<e/f|g'h*i%j$k.pdf")).toBe('abcdefghijk.pdf')
    expect(uploadName('wniosek%20o%20dowod.pdf')).toBe('wniosek20o20dowod.pdf')
    expect(uploadName('a' + String.fromCharCode(92) + 'b.pdf')).toBe('ab.pdf')
  })
  it('removes control and direction characters', () => {
    expect(uploadName('a' + String.fromCharCode(0x202e) + 'b' + String.fromCharCode(7) + '.pdf')).toBe('ab.pdf')
  })
  it('cuts a long name to 250 characters and keeps the extension', () => {
    const out = uploadName('a'.repeat(400) + '.pdf')
    expect(out.length).toBe(250)
    expect(out.endsWith('.pdf')).toBe(true)
  })
  it('gives a name to a name that is left empty', () => {
    expect(uploadName('%%%.pdf')).toBe('.pdf')   // the extension stays; the service reads it as PDF
    expect(uploadName('%%%')).toBe('plik')
    expect(uploadName('')).toBe('plik')
  })
})
