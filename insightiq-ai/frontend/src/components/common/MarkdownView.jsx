import React from "react";

/**
 * Lightweight, robust markdown renderer for ChatGPT-like rich text presentation.
 * Supports:
 * - Headers: ###, ##, #
 * - Bold: **text**
 * - Italic: *text* or _text_
 * - Inline Code/Pills: `code`
 * - Bullet lists: •, -, *
 * - Numbered lists: 1., 2.
 * - Tables: | col1 | col2 |
 * - Blockquotes: > quote
 * - Clean paragraph separation
 */
export const MarkdownView = ({ content = "", className = "" }) => {
  if (!content) return null;

  // Inline formatting helper
  const renderInline = (text) => {
    if (!text) return null;

    // Tokenize bold, italic, code
    const parts = [];
    let remaining = text;
    let keyIdx = 0;

    // Pattern for bold, code, italic
    const regex = /(\*\*.*?\*\*|`.*?`|\*.*?\*)/;

    while (remaining) {
      const match = remaining.match(regex);
      if (!match) {
        parts.push(remaining);
        break;
      }

      const matchIdx = match.index;
      if (matchIdx > 0) {
        parts.push(remaining.substring(0, matchIdx));
      }

      const token = match[0];
      if (token.startsWith("**") && token.endsWith("**")) {
        parts.push(
          <strong key={keyIdx++} className="font-semibold text-navy-950">
            {token.slice(2, -2)}
          </strong>
        );
      } else if (token.startsWith("`") && token.endsWith("`")) {
        parts.push(
          <code
            key={keyIdx++}
            className="px-1.5 py-0.5 rounded bg-surface-muted text-brand-700 font-mono text-[11px] border border-surface-border font-medium"
          >
            {token.slice(1, -1)}
          </code>
        );
      } else if (token.startsWith("*") && token.endsWith("*")) {
        parts.push(
          <em key={keyIdx++} className="text-navy-700 italic">
            {token.slice(1, -1)}
          </em>
        );
      } else {
        parts.push(token);
      }

      remaining = remaining.substring(matchIdx + token.length);
    }

    return parts;
  };

  const lines = content.split("\n");
  const elements = [];
  let currentList = null;
  let currentTable = null;

  const flushList = () => {
    if (currentList) {
      elements.push(
        <ul
          key={`ul-${elements.length}`}
          className="space-y-1.5 my-2.5 pl-1 list-none"
        >
          {currentList.map((item, idx) => (
            <li key={idx} className="flex items-start gap-2 text-xs text-navy-800 leading-relaxed">
              <span className="w-1.5 h-1.5 rounded-full bg-brand-500 mt-1.5 shrink-0" />
              <div className="flex-1">{renderInline(item)}</div>
            </li>
          ))}
        </ul>
      );
      currentList = null;
    }
  };

  const flushTable = () => {
    if (currentTable) {
      const { headers, rows } = currentTable;
      elements.push(
        <div
          key={`table-${elements.length}`}
          className="my-3 overflow-x-auto rounded-xl border border-surface-border shadow-2xs"
        >
          <table className="w-full text-xs text-left text-navy-800">
            {headers && headers.length > 0 && (
              <thead className="bg-surface-subtle border-b border-surface-border text-navy-900 font-semibold text-[11px] uppercase tracking-wider">
                <tr>
                  {headers.map((h, idx) => (
                    <th key={idx} className="px-3 py-2">
                      {renderInline(h.trim())}
                    </th>
                  ))}
                </tr>
              </thead>
            )}
            <tbody className="divide-y divide-surface-border bg-surface">
              {rows.map((row, rIdx) => (
                <tr key={rIdx} className="hover:bg-surface-subtle/50 transition-colors">
                  {row.map((cell, cIdx) => (
                    <td key={cIdx} className="px-3 py-2 font-normal">
                      {renderInline(cell.trim())}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
      currentTable = null;
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i];
    const line = rawLine.trim();

    // Table line: starts and ends with |
    if (line.startsWith("|") && line.endsWith("|")) {
      flushList();
      const cells = line
        .split("|")
        .slice(1, -1)
        .map((c) => c.trim());

      // If separator line e.g. |---|---|
      if (cells.every((c) => /^:?-+:?$/.test(c))) {
        continue;
      }

      if (!currentTable) {
        currentTable = { headers: cells, rows: [] };
      } else {
        currentTable.rows.push(cells);
      }
      continue;
    } else {
      flushTable();
    }

    // Heading 3
    if (line.startsWith("### ")) {
      flushList();
      elements.push(
        <h3
          key={`h3-${i}`}
          className="text-xs font-bold text-navy-900 mt-3.5 mb-1.5 flex items-center gap-1.5 tracking-tight"
        >
          {renderInline(line.substring(4))}
        </h3>
      );
      continue;
    }

    // Heading 2
    if (line.startsWith("## ")) {
      flushList();
      elements.push(
        <h2
          key={`h2-${i}`}
          className="text-sm font-bold text-navy-900 mt-4 mb-2 tracking-tight"
        >
          {renderInline(line.substring(3))}
        </h2>
      );
      continue;
    }

    // Heading 1
    if (line.startsWith("# ")) {
      flushList();
      elements.push(
        <h1
          key={`h1-${i}`}
          className="text-base font-bold text-navy-900 mt-4 mb-2 tracking-tight"
        >
          {renderInline(line.substring(2))}
        </h1>
      );
      continue;
    }

    // Bullet points: • or - or *
    if (line.startsWith("• ") || line.startsWith("- ") || line.startsWith("* ")) {
      const itemText = line.substring(2);
      if (!currentList) currentList = [];
      currentList.push(itemText);
      continue;
    }

    // Blockquote
    if (line.startsWith("> ")) {
      flushList();
      elements.push(
        <blockquote
          key={`quote-${i}`}
          className="border-l-2 border-brand-500 pl-3 py-1.5 my-2.5 text-xs text-navy-700 bg-brand-50/40 rounded-r-lg italic"
        >
          {renderInline(line.substring(2))}
        </blockquote>
      );
      continue;
    }

    // Non-list line
    flushList();

    // Empty line
    if (!line) {
      continue;
    }

    // Standard paragraph
    elements.push(
      <p
        key={`p-${i}`}
        className="text-xs leading-relaxed text-navy-800 my-1.5 font-normal"
      >
        {renderInline(line)}
      </p>
    );
  }

  flushList();
  flushTable();

  return <div className={`space-y-1 text-xs leading-relaxed ${className}`}>{elements}</div>;
};

export default MarkdownView;
