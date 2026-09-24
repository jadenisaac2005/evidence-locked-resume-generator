// Résumé template. All content arrives as JSON in sys.inputs.data; this file adds none.
// ATS rules (docs/research.md): single column, plain text flow, no tables, icons,
// graphics or page header/footer; URLs are visible text; ligatures off.
#let d = json(bytes(sys.inputs.data))

#set document(title: d.name + " – Résumé", author: d.name, date: none)  // reproducible bytes
#set page(paper: d.paper, margin: (x: 14mm, y: 11mm))
#set text(font: "Libertinus Serif", size: d.font_size * 1pt, ligatures: false,
          hyphenate: false, lang: "en")
#set par(justify: false, leading: 0.45em, spacing: 0.45em)

#let sep = [ #h(0.2em)|#h(0.2em) ]
// URLs are boxed so they never wrap mid-address (a split URL breaks parsers).

// Hyphenated/slashed tokens (ROC-AUC, 60/20/20, TF-IDF, 7.83/10, ...) are boxed so
// they never wrap mid-token: a line break there can drop the separator on extraction.
#let no-break(t) = if type(t) != str { t } else {
  t.split(" ").map(p => if p.contains("-") or p.contains("/") { box(p) } else { p }).join(" ")
}

#let section-title(t) = block(width: 100%, above: 0.8em, below: 0.5em,
  stroke: (bottom: 0.5pt), inset: (bottom: 2pt), text(size: 1.1em, weight: "bold", t))

// Bullet: a hanging-indent paragraph. Its rendered line count is measured and
// exported as metadata so the Python lint can enforce max_lines.
#let bullet(b) = layout(size => {
  let indent = 1.1em
  let body(t) = par(hanging-indent: indent)[•#h(indent - 0.45em)#no-break(t)]
  let h = measure(block(width: size.width, body(b.text))).height
  let one = measure(block(width: size.width, body("X"))).height
  let two = measure(block(width: size.width, body[X \ X])).height
  let lines = calc.round((h - one) / (two - one)) + 1
  [#metadata((id: b.id, lines: lines))<bullet>]
  body(b.text)
})

#align(center)[
  #text(size: 1.9em, weight: "bold", d.name) \
  #v(-0.2em)
  #d.contact.map(c => if c.url == none { c.text } else { box(link(c.url, c.text)) }).join(sep)
]

#for s in d.sections {
  section-title(s.title)
  if s.kind == "education" {
    for e in s.entries [
      *#no-break(e.institution)* #h(1fr) #e.date \
      #no-break(e.degree)#if e.cgpa != none [#sep CGPA: #no-break(e.cgpa)]
    ]
  } else if s.kind == "projects" {
    for p in s.projects {
      v(0.15em)
      let left = [*#no-break(p.name)*#if p.context != none [ #h(0.2em)– #emph(no-break(p.context))]#if p.stack.len() > 0 [#sep#emph(p.stack.map(no-break).join(", "))]]
      let right = [#text(size: 0.92em, p.links.map(l => box(link(l.url, l.text))).join(sep))#if p.date != none [#sep#p.date]]
      // Right-align links only when they fit on the header line; otherwise give them their
      // own line, so extraction never glues the last stack item onto a URL.
      block(breakable: false, below: 0.4em, layout(size => {
        if measure(left).width + measure(right).width + 1.5em.to-absolute() <= size.width [#left #h(1fr) #right]
        else if p.links.len() == 0 and p.date == none [#left]
        else [#left \ #right]
      }))
      for b in p.bullets { bullet(b) }
    }
  } else if s.kind == "skills" {
    for g in s.groups [
      *#g.label:* #g.items.map(no-break).join(", ") \
    ]
  }
}
