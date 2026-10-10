#!/usr/bin/env python3
"""Turn theme.scss into nested CSS files.

Modifiers stay outside the component. `&` only reaches inward.
SCSS mixins, variables, and loops are expanded. Nesting is kept.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "theme.scss"
OUT = ROOT / "src" / "css"

FILES = [
    "tokens.css",
    "editor.css",
    "tasks.css",
    "blocks.css",
    "code.css",
    "tables.css",
    "tags.css",
    "workspace.css",
    "file-tree.css",
    "controls.css",
    "modes.css",
    "plugins.css",
    "style-settings.css",
]


class Parser:
    def __init__(self, text: str):
        self.s = text
        self.i = 0
        self.n = len(text)
        self.line = 1
        self.bumps = 0

    def peek(self, k: int = 0) -> str:
        j = self.i + k
        return self.s[j] if j < self.n else ""

    def starts(self, lit: str) -> bool:
        return self.s.startswith(lit, self.i)

    def bump(self, k: int = 1) -> None:
        for _ in range(k):
            if self.i < self.n and self.s[self.i] == "\n":
                self.line += 1
            self.i += 1

    def skip_ws(self) -> None:
        while self.i < self.n and self.peek() in " \t\r\n\f":
            self.bump()

    def skip_string(self) -> str:
        q = self.peek()
        start_line = self.line
        out = [q]
        self.bump()
        while self.i < self.n:
            if self.starts("#{"):
                out.append(self.skip_interpolation_raw())
                continue
            c = self.peek()
            out.append(c)
            self.bump()
            if c == "\\":
                if self.i < self.n:
                    out.append(self.peek())
                    self.bump()
                continue
            if c == q:
                return "".join(out)
        raise SystemExit(f"unterminated string starting line {start_line}")

    def skip_interpolation_raw(self) -> str:
        assert self.starts("#{")
        self.bump(2)
        depth = 1
        out = ["#{"]
        while self.i < self.n and depth:
            if self.peek() in "\"'":
                out.append(self.skip_string())
                continue
            c = self.peek()
            out.append(c)
            self.bump()
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
        return "".join(out)

    def skip_comment_ws(self, keep_block: bool = False):
        """Skip whitespace and comments. Return a kept /* */ comment or None."""
        while True:
            self.skip_ws()
            if self.starts("//"):
                while self.i < self.n and self.peek() != "\n":
                    self.bump()
                continue
            if self.starts("/*"):
                start = self.i
                self.bump(2)
                while self.i < self.n and not self.starts("*/"):
                    self.bump()
                self.bump(2)
                comment = self.s[start : self.i]
                if keep_block and "@settings" in comment[:120]:
                    return comment
                if keep_block and "sourceMappingURL" not in comment and comment.startswith("/* QLEAN"):
                    return comment
                continue
            return None


def split_top(text: str, opener: str = ",", depth_chars: str = "()[]{}") -> list[str]:
    parts: list[str] = []
    buf: list[str] = []
    stack: list[str] = []
    pairs = {")": "(", "]": "[", "}": "{"}
    i = 0
    while i < len(text):
        if text.startswith("#{", i):
            j = i + 2
            depth = 1
            while j < len(text) and depth:
                if text[j] == "{":
                    depth += 1
                elif text[j] == "}":
                    depth -= 1
                j += 1
            buf.append(text[i:j])
            i = j
            continue
        c = text[i]
        if c in "\"'":
            j = i + 1
            while j < len(text):
                if text[j] == "\\":
                    j += 2
                    continue
                if text[j] == c:
                    j += 1
                    break
                j += 1
            buf.append(text[i:j])
            i = j
            continue
        if c in "([{":
            stack.append(c)
            buf.append(c)
        elif c in ")]}":
            if stack and stack[-1] == pairs[c]:
                stack.pop()
            buf.append(c)
        elif c == opener and not stack:
            parts.append("".join(buf).strip())
            buf = []
        else:
            buf.append(c)
        i += 1
    tail = "".join(buf).strip()
    if tail:
        parts.append(tail)
    return [p for p in parts if p != ""]


def parse_map_or_list(raw: str):
    raw = raw.strip()
    if raw.startswith("(") and raw.endswith(")"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        items = split_top(inner, ",")
        if any(re.match(r"^(['\"]).*?\1\s*:", item) or re.match(r"^[A-Za-z0-9_-]+\s*:", item) for item in items):
            mapping = {}
            for item in items:
                key, val = split_key(item)
                mapping[unquote(key)] = normalize_value(val)
            return mapping
        return [normalize_value(item) for item in items]
    if "," in raw and not raw.startswith(("url(", "hsl", "hsla", "rgb", "rgba", "color-mix", "linear-gradient", "calc")):
        items = split_top(raw, ",")
        if len(items) > 1:
            return [normalize_value(item) for item in items]
    return unquote(raw) if raw[:1] in "\"'" else raw


def parse_string_concat(item: str) -> str | None:
    """Sass concatenates adjacent quoted strings. Return None if anything else is present."""
    i = 0
    n = len(item)
    chunks: list[str] = []
    while i < n:
        if item[i] in " \t\n":
            i += 1
            continue
        if item[i] not in "\"'":
            return None
        quote = item[i]
        j = i + 1
        while j < n:
            if item[j] == "\\" and j + 1 < n:
                j += 2
                continue
            if item[j] == quote:
                j += 1
                break
            j += 1
        else:
            return None
        chunks.append(unescape_sass_string(item[i + 1 : j - 1]))
        i = j
    if not chunks:
        return None
    return "".join(chunks)


def normalize_value(item: str):
    item = item.strip()
    if looks_nested(item):
        return parse_map_or_list(item)
    concatenated = parse_string_concat(item)
    if concatenated is not None:
        return concatenated
    return item


def looks_nested(val: str) -> bool:
    val = val.strip()
    return val.startswith("(") and val.endswith(")")


def split_key(item: str) -> tuple[str, str]:
    parts = split_top(item, ":")
    if len(parts) < 2:
        raise SystemExit(f"bad map item: {item[:80]}")
    return parts[0], ":".join(parts[1:])


def unescape_sass_string(text: str) -> str:
    """CSS/Sass string escapes. `'\\"'` is a backslash followed by a quote."""
    out: list[str] = []
    i = 0
    while i < len(text):
        if text[i] != "\\" or i + 1 >= len(text):
            out.append(text[i])
            i += 1
            continue
        nxt = text[i + 1]
        if nxt == "\n":
            i += 2
            continue
        if nxt in "0123456789abcdefABCDEF":
            j = i + 1
            while j < len(text) and j < i + 7 and text[j] in "0123456789abcdefABCDEF":
                j += 1
            out.append(chr(int(text[i + 1 : j], 16)))
            if j < len(text) and text[j] == " ":
                j += 1
            i = j
            continue
        out.append(nxt)
        i += 2
    return "".join(out)


def unquote(text: str) -> str:
    text = text.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return unescape_sass_string(text[1:-1])
    return text


class Scope:
    def __init__(self, parent: Scope | None = None):
        self.parent = parent
        self.vars: dict[str, object] = {}
        self.mixins: dict[str, tuple[list[tuple[str, str | None]], list]] = {}

    def get(self, name: str):
        if name in self.vars:
            return self.vars[name]
        if self.parent:
            return self.parent.get(name)
        raise SystemExit(f"unknown ${name}")

    def mixin(self, name: str):
        if name in self.mixins:
            return self.mixins[name]
        if self.parent:
            return self.parent.mixin(name)
        raise SystemExit(f"unknown mixin {name}")


def eval_interp(expr: str, scope: Scope) -> str:
    expr = expr.strip()
    m = re.fullmatch(r"map-get\(\$([A-Za-z0-9_-]+)\s*,\s*(['\"])(.*?)\2\)", expr)
    if m:
        value = scope.get(m.group(1))
        if not isinstance(value, dict):
            raise SystemExit(f"map-get on non-map ${m.group(1)}")
        got = value[m.group(3)]
        return stringify(got)
    m = re.fullmatch(r"\$([A-Za-z0-9_-]+)", expr)
    if m:
        return stringify(scope.get(m.group(1)))
    return expr


def stringify(value: object) -> str:
    if isinstance(value, list):
        return ", ".join(stringify(v) for v in value)
    if isinstance(value, dict):
        raise SystemExit("cannot stringify map")
    return str(value)


def eval_text(text: str, scope: Scope) -> str:
    def repl_map(match: re.Match) -> str:
        return eval_interp(match.group(0), scope)

    text = re.sub(
        r"map-get\(\$([A-Za-z0-9_-]+)\s*,\s*(['\"])(.*?)\2\)",
        repl_map,
        text,
    )

    def repl_interp(match: re.Match) -> str:
        return eval_interp(match.group(1), scope)

    text = re.sub(r"#\{(.*?)\}", repl_interp, text, flags=re.S)

    def repl_var(match: re.Match) -> str:
        return stringify(scope.get(match.group(1)))

    return re.sub(r"\$([A-Za-z0-9_-]+)", repl_var, text)


class Decl:
    def __init__(self, text: str):
        self.text = text


class Rule:
    def __init__(self, selector: str, body: list, line: int):
        self.selector = selector
        self.body = body
        self.line = line


class Comment:
    def __init__(self, text: str, line: int):
        self.text = text
        self.line = line


def parse_block(p: Parser) -> list:
    nodes: list = []
    while p.i < p.n:
        comment = p.skip_comment_ws(keep_block=True)
        if comment:
            nodes.append(Comment(comment, p.line))
            continue
        if p.peek() == "" or p.peek() == "}":
            break
        if p.starts("@mixin"):
            nodes.append(parse_mixin(p))
            continue
        if p.starts("@include"):
            nodes.append(("include", parse_include(p), p.line))
            continue
        if p.starts("@for"):
            nodes.append(parse_for(p))
            continue
        if p.starts("@each"):
            nodes.append(parse_each(p))
            continue
        if p.starts("@if"):
            nodes.append(parse_if(p))
            continue
        if p.starts("@extend"):
            p.bump(len("@extend"))
            p.skip_ws()
            text, delim = read_until(p)
            if delim != ";":
                raise SystemExit(f"@extend at line {p.line}")
            nodes.append(("extend", text.strip(), p.line))
            continue
        if p.starts("@else"):
            break
        start_line = p.line
        text, delim = read_until(p)
        text = text.strip()
        if not text and delim == "eof":
            break
        if delim == "{":
            body = parse_block(p)
            if p.peek() == "}":
                p.bump()
            nodes.append(Rule(text, body, start_line))
            continue
        if delim == ";":
            if text.startswith("$"):
                name, raw = text.split(":", 1)
                nodes.append(("assign", name.strip()[1:], raw.strip(), start_line))
            else:
                nodes.append(Decl(text))
            continue
        raise SystemExit(f"parse error line {start_line}: {text[:80]!r} delim={delim}")
    return nodes


def read_until(p: Parser) -> tuple[str, str]:
    buf: list[str] = []
    paren = bracket = 0
    while p.i < p.n:
        if p.starts("//"):
            while p.i < p.n and p.peek() != "\n":
                p.bump()
            continue
        if p.starts("/*"):
            while p.i < p.n and not p.starts("*/"):
                p.bump()
            p.bump(2)
            continue
        if p.starts("#{"):
            buf.append(p.skip_interpolation_raw())
            continue
        c = p.peek()
        if c in "\"'":
            buf.append(p.skip_string())
            continue
        if c == "(":
            paren += 1
        elif c == ")":
            paren = max(0, paren - 1)
        elif c == "[":
            bracket += 1
        elif c == "]":
            bracket = max(0, bracket - 1)
        elif c == "{" and paren == 0 and bracket == 0:
            p.bump()
            return "".join(buf), "{"
        elif c == ";" and paren == 0 and bracket == 0:
            p.bump()
            return "".join(buf), ";"
        elif c == "}" and paren == 0 and bracket == 0:
            return "".join(buf), "eof"
        buf.append(c)
        p.bump()
    return "".join(buf), "eof"


def parse_mixin(p: Parser):
    p.bump(len("@mixin"))
    p.skip_ws()
    name = read_ident(p)
    p.skip_ws()
    params: list[tuple[str, str | None]] = []
    if p.peek() == "(":
        p.bump()
        depth = 1
        buf: list[str] = []
        while depth:
            if p.i >= p.n:
                raise SystemExit(f"unclosed mixin params for {name} near {''.join(buf)[-80:]!r}")
            c = p.peek()
            if c in "\"'":
                buf.append(p.skip_string())
                continue
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    p.bump()
                    break
            buf.append(c)
            p.bump()
        raw = "".join(buf).strip()
        if raw:
            for param in split_top(raw, ","):
                if ":" in param:
                    n, default = param.split(":", 1)
                    params.append((n.strip().lstrip("$"), default.strip()))
                else:
                    params.append((param.strip().lstrip("$"), None))
    p.skip_ws()
    if p.peek() != "{":
        raise SystemExit(f"mixin {name} missing body line {p.line}")
    p.bump()
    body = parse_block(p)
    if p.peek() == "}":
        p.bump()
    return ("mixin", name, params, body)


def parse_include(p: Parser) -> tuple[str, list[tuple[str | None, str]]]:
    p.bump(len("@include"))
    p.skip_ws()
    name = read_ident(p)
    p.skip_ws()
    args: list[tuple[str | None, str]] = []
    if p.peek() == "(":
        p.bump()
        depth = 1
        buf: list[str] = []
        while depth:
            if p.i >= p.n:
                raise SystemExit(f"unclosed include args for {name} line {p.line} near {''.join(buf)[-120:]!r}")
            c = p.peek()
            if c in "\"'":
                buf.append(p.skip_string())
                continue
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    p.bump()
                    break
            buf.append(c)
            p.bump()
        raw = "".join(buf).strip()
        if raw:
            for arg in split_top(raw, ","):
                if re.match(r"^\$[A-Za-z0-9_-]+\s*:", arg):
                    n, val = arg.split(":", 1)
                    args.append((n.strip()[1:], val.strip()))
                else:
                    args.append((None, arg.strip()))
    p.skip_ws()
    if p.peek() == ";":
        p.bump()
    return name, args


def parse_for(p: Parser):
    line = p.line
    p.bump(len("@for"))
    p.skip_ws()
    if p.peek() != "$":
        raise SystemExit(f"@for line {line}")
    p.bump()
    var = read_ident(p)
    p.skip_ws()
    if not p.starts("from"):
        raise SystemExit(f"@for from line {line}")
    p.bump(4)
    p.skip_ws()
    start = read_ident(p) if p.peek() != "$" else read_var_token(p)
    # numbers
    if start == "" or not start[0].isdigit():
        # read_ident may have failed on a number
        pass
    p.skip_ws()
    if not p.starts("through"):
        raise SystemExit(f"@for through line {p.line}: {p.s[p.i:p.i+20]!r}")
    p.bump(7)
    p.skip_ws()
    end = ""
    while p.peek() and p.peek() not in " \t\r\n{":
        end += p.peek()
        p.bump()
    p.skip_ws()
    if p.peek() != "{":
        raise SystemExit(f"@for body line {p.line}")
    p.bump()
    body = parse_block(p)
    if p.peek() == "}":
        p.bump()
    return ("for", var, start, end, body, line)


def parse_each(p: Parser):
    line = p.line
    p.bump(len("@each"))
    p.skip_ws()
    vars: list[str] = []
    while True:
        p.skip_ws()
        if p.peek() != "$":
            break
        p.bump()
        vars.append(read_ident(p))
        p.skip_ws()
        if p.peek() == ",":
            p.bump()
            continue
        break
    p.skip_ws()
    if not p.starts("in"):
        raise SystemExit(f"@each in line {p.line}")
    p.bump(2)
    p.skip_ws()
    if p.peek() != "$":
        raise SystemExit(f"@each collection line {p.line}")
    p.bump()
    coll = read_ident(p)
    p.skip_ws()
    if p.peek() != "{":
        raise SystemExit(f"@each body line {p.line}")
    p.bump()
    body = parse_block(p)
    if p.peek() == "}":
        p.bump()
    return ("each", vars, coll, body, line)


def parse_if(p: Parser):
    line = p.line
    p.bump(len("@if"))
    p.skip_ws()
    cond, _ = read_condition(p)
    if p.peek() != "{":
        raise SystemExit(f"@if body line {p.line} {p.s[p.i:p.i+30]!r}")
    p.bump()
    body = parse_block(p)
    if p.peek() == "}":
        p.bump()
    branches = [(cond, body)]
    while True:
        p.skip_ws()
        if not p.starts("@else"):
            break
        p.bump(len("@else"))
        p.skip_ws()
        if p.starts("if"):
            p.bump(2)
            p.skip_ws()
            cond, _ = read_condition(p)
        else:
            cond = None
        if p.peek() != "{":
            raise SystemExit(f"@else body line {p.line}")
        p.bump()
        else_body = parse_block(p)
        if p.peek() == "}":
            p.bump()
        branches.append((cond, else_body))
    return ("if", branches, line)


def read_condition(p: Parser) -> tuple[str, str]:
    buf: list[str] = []
    while p.i < p.n and p.peek() not in "{":
        if p.peek() in "\"'":
            buf.append(p.skip_string())
            continue
        buf.append(p.peek())
        p.bump()
    return "".join(buf).strip(), "{"


def read_ident(p: Parser) -> str:
    out = []
    while p.peek() and (p.peek().isalnum() or p.peek() in "_-"):
        out.append(p.peek())
        p.bump()
    return "".join(out)


def read_var_token(p: Parser) -> str:
    if p.peek() == "$":
        p.bump()
    return "$" + read_ident(p)


def expand(nodes: list, scope: Scope) -> list:
    out: list = []
    for node in nodes:
        if isinstance(node, Comment):
            out.append(node)
        elif isinstance(node, Decl):
            out.append(Decl(cleanup_decl(eval_text(node.text, scope))))
        elif isinstance(node, Rule):
            out.append(Rule(eval_text(node.selector, scope), expand(node.body, scope), node.line))
        elif isinstance(node, tuple) and node[0] == "assign":
            _, name, raw, _line = node
            scope.vars[name] = parse_map_or_list(eval_text(raw, scope))
        elif isinstance(node, tuple) and node[0] == "mixin":
            _, name, params, body = node
            scope.mixins[name] = (params, body)
        elif isinstance(node, tuple) and node[0] == "include":
            _, (name, args), _line = node
            out.extend(expand_include(name, args, scope))
        elif isinstance(node, tuple) and node[0] == "for":
            _, var, start, end, body, _line = node
            a = int(eval_text(start, scope))
            b = int(eval_text(end, scope))
            for i in range(a, b + 1):
                child = Scope(scope)
                child.vars[var] = str(i)
                out.extend(expand(body, child))
        elif isinstance(node, tuple) and node[0] == "each":
            _, vars_, coll, body, _line = node
            value = scope.get(coll)
            if isinstance(value, dict):
                seq = list(value.items())
            elif isinstance(value, list):
                seq = [(item, None) for item in value]
            else:
                seq = [(item, None) for item in split_top(str(value), ",")]
            for item in seq:
                child = Scope(scope)
                if len(vars_) == 2:
                    child.vars[vars_[0]] = item[0]
                    child.vars[vars_[1]] = item[1]
                else:
                    child.vars[vars_[0]] = item if not isinstance(value, dict) else item[0]
                    if not isinstance(value, dict) and isinstance(item, tuple):
                        child.vars[vars_[0]] = item[0]
                out.extend(expand(body, child))
        elif isinstance(node, tuple) and node[0] == "if":
            _, branches, _line = node
            for cond, body in branches:
                if cond is None or truthy(cond, scope):
                    out.extend(expand(body, scope))
                    break
        elif isinstance(node, tuple) and node[0] == "extend":
            continue
        else:
            raise SystemExit(f"bad node {node!r}"[:200])
    return out


def truthy(cond: str, scope: Scope) -> bool:
    cond = eval_text(cond, scope).replace(" ", "")
    if "==" in cond:
        left, right = cond.split("==", 1)
        return left == right
    return cond not in ("", "false", "null")


def expand_include(name: str, args: list[tuple[str | None, str]], scope: Scope) -> list:
    params, body = scope.mixin(name)
    child = Scope(scope)
    bound: dict[str, str] = {}
    positional = [val for key, val in args if key is None]
    named = {key: val for key, val in args if key}
    pi = 0
    for pname, default in params:
        if pname in named:
            raw = named[pname]
        elif pi < len(positional):
            raw = positional[pi]
            pi += 1
        elif default is not None:
            raw = default
        else:
            raise SystemExit(f"missing arg {pname} for {name}")
        bound[pname] = eval_text(raw, scope)
    child.vars.update(bound)
    return expand(body, child)


def cleanup_decl(text: str) -> str:
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n[ \t]*", " ", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip().rstrip(";")


def uses_outer_parent(selector: str) -> bool:
    """`body.modifier &` should wrap the component. `&` inside `:has(&)` stays put."""
    collapsed = " ".join(selector.split())
    idx = collapsed.find("&")
    if idx <= 0:
        return False
    return collapsed[idx - 1].isspace()


def attach(parent: str, suffix: str) -> str:
    if suffix.startswith((" ", ">", "+", "~")):
        return parent + suffix
    return parent + suffix


def split_selectors(selector: str) -> list[str]:
    return [part.strip() for part in split_top(selector, ",") if part.strip()]


def fully_resolve(selector: str, ancestors: list[str] | None) -> list[str]:
    if not ancestors:
        return split_selectors(selector)
    resolved: list[str] = []
    for sel in split_selectors(selector):
        if "&" not in sel:
            for ancestor in ancestors:
                resolved.append(f"{ancestor} {sel}".strip())
            continue
        idx = sel.find("&")
        prefix, suffix = sel[:idx], sel[idx + 1 :]
        for ancestor in ancestors:
            resolved.append((prefix + attach(ancestor, suffix)).strip())
    return resolved


def hoist_tree(nodes: list, ancestors: list[str] | None = None) -> tuple[list, list]:
    """Return kept nodes, plus modifier rules that must sit beside the component, not inside it."""
    out: list = []
    lifted: list = []
    for node in nodes:
        if not isinstance(node, Rule):
            out.append(node)
            continue
        resolved = fully_resolve(node.selector, ancestors)
        kept: list = []
        pending: list[Rule] = []
        for child in node.body:
            if isinstance(child, Rule) and uses_outer_parent(child.selector):
                pending.extend(make_hoisted(child, resolved))
            else:
                kept.append(child)
        inner, more = hoist_tree(kept, resolved)
        node.body = inner
        pending.extend(more)
        pending = merge_outers(pending)
        if ancestors is None:
            out.append(node)
            out.extend(pending)
        else:
            out.append(node)
            lifted.extend(pending)
    return out, lifted


def make_hoisted(rule: Rule, parent_resolved: list[str]) -> list[Rule]:
    selector = " ".join(rule.selector.split())
    idx = selector.find("&")
    outer = selector[:idx].strip()
    suffix = selector[idx + 1 :]
    inners: list[str] = []
    resolved: list[str] = []
    for parent in parent_resolved:
        target = attach(parent, suffix).strip()
        resolved.append(f"{outer} {target}".strip())
        inners.append("& " + target)
    inner_body, more = hoist_tree(rule.body, resolved)
    inner = Rule(",\n".join(inners), inner_body, rule.line)
    return [Rule(outer, [inner], rule.line), *more]


def split_body_descendant(selector: str) -> tuple[str, str] | None:
    """`body.modifier .component` → (`body.modifier`, `.component`)."""
    sel = " ".join(selector.split())
    if not sel.startswith("body"):
        return None
    depth = 0
    for i, char in enumerate(sel):
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)
        elif char == " " and depth == 0:
            rest = sel[i + 1 :].strip()
            if rest:
                return sel[:i], rest
            return None
    return None


def nest_flat_body(nodes: list) -> list:
    """Write `body.modifier { & .component }` instead of a flat descendant selector."""
    out: list = []
    for node in nodes:
        if not isinstance(node, Rule):
            out.append(node)
            continue
        parts = split_selectors(node.selector)
        splits = [split_body_descendant(part) for part in parts]
        if not splits or any(item is None for item in splits):
            out.append(node)
            continue
        outers = {item[0] for item in splits if item is not None}
        if len(outers) != 1:
            out.append(node)
            continue
        outer = next(iter(outers))
        inner_sel = ",\n".join("& " + rest for pair in splits if pair for rest in (pair[1],))
        inner = Rule(inner_sel, node.body, node.line)
        if (
            out
            and isinstance(out[-1], Rule)
            and out[-1].selector == outer
            and out[-1].body
            and all(isinstance(child, Rule) and child.selector.strip().startswith("&") for child in out[-1].body)
        ):
            out[-1].body.append(inner)
        else:
            out.append(Rule(outer, [inner], node.line))
    return out


def drop_empty(nodes: list) -> list:
    out: list = []
    for node in nodes:
        if isinstance(node, Rule):
            node.body = drop_empty(node.body)
            if not node.body:
                continue
        out.append(node)
    return out


def merge_outers(rules: list[Rule]) -> list[Rule]:
    merged: list[Rule] = []
    for rule in rules:
        if merged and merged[-1].selector == rule.selector:
            merged[-1].body.extend(rule.body)
        else:
            merged.append(rule)
    return merged


def emit(nodes: list, indent: int = 0) -> str:
    pad = "  " * indent
    chunks: list[str] = []
    for node in nodes:
        if isinstance(node, Comment):
            chunks.append(f"{pad}{node.text}\n")
        elif isinstance(node, Decl):
            chunks.append(f"{pad}{node.text};\n")
        elif isinstance(node, Rule):
            selector = node.selector.strip()
            if "\n" in selector:
                lines = [line.strip() for line in selector.split("\n") if line.strip()]
                head = f"{pad}{lines[0]}\n"
                for line in lines[1:]:
                    head += f"{pad}{line}\n"
                chunks.append(head + f"{pad}{{\n" + emit(node.body, indent + 1) + f"{pad}}}\n")
            else:
                chunks.append(f"{pad}{selector} {{\n" + emit(node.body, indent + 1) + f"{pad}}}\n")
    return "".join(chunks)


def file_for_line(line: int, anchors: list[tuple[int, str]]) -> str:
    current = "tokens.css"
    for start, name in anchors:
        if line >= start:
            current = name
    return current


def main() -> None:
    text = SRC.read_text()
    parser = Parser(text)
    nodes = parse_block(parser)
    if parser.i < parser.n and parser.s[parser.i :].strip():
        raise SystemExit(f"unparsed tail at line {parser.line}: {parser.s[parser.i:parser.i+80]!r}")
    scope = Scope()
    expanded = expand(nodes, scope)
    expanded = replace_extend(expanded)
    hoisted, lifted = hoist_tree(expanded)
    hoisted.extend(lifted)
    hoisted = drop_empty(hoisted)
    hoisted = nest_flat_body(hoisted)
    anchors = build_anchors(text)
    buckets: dict[str, list] = {name: [] for name in FILES}
    for node in hoisted:
        line = getattr(node, "line", 1)
        buckets[file_for_line(line, anchors)].append(node)
    OUT.mkdir(parents=True, exist_ok=True)
    note = (
        "/* Modifiers wrap the component. `&` only reaches inward.\n"
        " * Do not write `body.modifier &` inside a component. */\n"
    )
    for name in FILES:
        body = emit(buckets[name]).rstrip() + "\n"
        if name == "tokens.css":
            body = note + body
        (OUT / name).write_text(body)
        print(f"{name:24} {body.count(chr(10)):5} lines")


def replace_extend(nodes: list) -> list:
    out = []
    for node in nodes:
        if isinstance(node, Rule):
            node.selector = node.selector.replace(
                ".markdown-rendered",
                ":is(.markdown-rendered, .style-settings-container)",
            )
            node.body = replace_extend(node.body)
            out.append(node)
        else:
            out.append(node)
    return out


def build_anchors(text: str) -> list[tuple[int, str]]:
    wanted = [
        ("body:is(.theme-light, .theme-dark) {", "tokens.css"),
        ("// paragraphs basic", "editor.css"),
        ("body:not(.qlean-off-alternative-checkboxes)", "tasks.css"),
        ("// callout", "blocks.css"),
        ("// embed media", "code.css"),
        ("// table", "tables.css"),
        ("// tag\n.markdown-rendered a.tag", "tags.css"),
        ("// deal with the corner of the window", "workspace.css"),
        ("// file tree", "file-tree.css"),
        ("// setting panel", "controls.css"),
        ("// focus mode", "modes.css"),
        ("// plugins support", "plugins.css"),
        ("/* @settings", "style-settings.css"),
    ]
    anchors = []
    for needle, name in wanted:
        idx = text.find(needle)
        if idx < 0:
            raise SystemExit(f"anchor missing: {needle}")
        anchors.append((text.count("\n", 0, idx) + 1, name))
    anchors.sort()
    return anchors


if __name__ == "__main__":
    main()
