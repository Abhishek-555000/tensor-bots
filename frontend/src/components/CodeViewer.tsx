import React, { useState, useMemo } from 'react';
import { Copy, Check, Download, AlignLeft, FileCode } from 'lucide-react';

interface CodeViewerProps {
  code: string;
  filePath: string;
  className?: string;
  maxHeight?: string;
}

// Token categories for syntax highlighting
type TokenType = 'keyword' | 'string' | 'comment' | 'number' | 'tag' | 'attr' | 'function' | 'text';

interface Token {
  type: TokenType;
  text: string;
}

// Lightweight, resilient, and fast syntax tokenizer
function tokenizeLine(line: string, ext: string): Token[] {
  if (!line) return [{ type: 'text', text: '' }];

  const tokens: Token[] = [];
  let remaining = line;

  // Extension normalization
  const isHtml = ext === 'html' || ext === 'htm' || ext === 'xml' || ext === 'svg';
  const isCss = ext === 'css' || ext === 'scss';
  const isJs = ext === 'js' || ext === 'jsx' || ext === 'ts' || ext === 'tsx';
  const isPy = ext === 'py';
  const isJson = ext === 'json';

  // Full-line or leading comments
  if ((isJs || isCss) && remaining.trim().startsWith('//')) {
    return [{ type: 'comment', text: remaining }];
  }
  if (isPy && remaining.trim().startsWith('#')) {
    return [{ type: 'comment', text: remaining }];
  }
  if (isHtml && remaining.trim().startsWith('<!--')) {
    return [{ type: 'comment', text: remaining }];
  }

  const jsKeywords = /^(const|let|var|function|return|if|else|for|while|import|export|from|default|class|new|async|await|try|catch|switch|case|break|typeof|instanceof|extends|super|this|true|false|null|undefined)\b/;
  const pyKeywords = /^(def|class|return|if|elif|else|for|while|try|except|finally|with|as|import|from|in|is|not|and|or|lambda|pass|break|continue|yield|async|await|True|False|None|self)\b/;

  while (remaining.length > 0) {
    // 1. Strings
    if (remaining.startsWith('"') || remaining.startsWith("'") || remaining.startsWith('`')) {
      const quote = remaining[0];
      let endIdx = 1;
      while (endIdx < remaining.length) {
        if (remaining[endIdx] === quote && remaining[endIdx - 1] !== '\\') {
          endIdx++;
          break;
        }
        endIdx++;
      }
      tokens.push({ type: 'string', text: remaining.slice(0, endIdx) });
      remaining = remaining.slice(endIdx);
      continue;
    }

    // 2. Comments (inline)
    if ((isJs || isCss) && remaining.startsWith('//')) {
      tokens.push({ type: 'comment', text: remaining });
      break;
    }
    if (isPy && remaining.startsWith('#')) {
      tokens.push({ type: 'comment', text: remaining });
      break;
    }

    // 3. HTML Tags & Attributes
    if (isHtml) {
      const tagMatch = remaining.match(/^<\/?[a-zA-Z0-9\-]+(\s|>|\/)/);
      if (tagMatch) {
        const text = tagMatch[0];
        tokens.push({ type: 'tag', text });
        remaining = remaining.slice(text.length);
        continue;
      }
      const attrMatch = remaining.match(/^[a-zA-Z0-9\-]+(?==)/);
      if (attrMatch) {
        tokens.push({ type: 'attr', text: attrMatch[0] });
        remaining = remaining.slice(attrMatch[0].length);
        continue;
      }
    }

    // 4. CSS properties
    if (isCss) {
      const propMatch = remaining.match(/^[a-zA-Z\-]+(?=\s*:)/);
      if (propMatch) {
        tokens.push({ type: 'attr', text: propMatch[0] });
        remaining = remaining.slice(propMatch[0].length);
        continue;
      }
    }

    // 5. Language Keywords
    if (isJs) {
      const kwMatch = remaining.match(jsKeywords);
      if (kwMatch) {
        tokens.push({ type: 'keyword', text: kwMatch[0] });
        remaining = remaining.slice(kwMatch[0].length);
        continue;
      }
    } else if (isPy) {
      const kwMatch = remaining.match(pyKeywords);
      if (kwMatch) {
        tokens.push({ type: 'keyword', text: kwMatch[0] });
        remaining = remaining.slice(kwMatch[0].length);
        continue;
      }
    } else if (isJson) {
      const jsonKey = remaining.match(/^"[^"]+"\s*(?=:)/);
      if (jsonKey) {
        tokens.push({ type: 'attr', text: jsonKey[0] });
        remaining = remaining.slice(jsonKey[0].length);
        continue;
      }
    }

    // 6. Function calls
    if (isJs || isPy) {
      const fnMatch = remaining.match(/^[a-zA-Z_$][a-zA-Z0-9_$]*(?=\s*\()/);
      if (fnMatch) {
        tokens.push({ type: 'function', text: fnMatch[0] });
        remaining = remaining.slice(fnMatch[0].length);
        continue;
      }
    }

    // 7. Numbers
    const numMatch = remaining.match(/^\b\d+(\.\d+)?\b/);
    if (numMatch) {
      tokens.push({ type: 'number', text: numMatch[0] });
      remaining = remaining.slice(numMatch[0].length);
      continue;
    }

    // 8. Next character / plain text
    tokens.push({ type: 'text', text: remaining[0] });
    remaining = remaining.slice(1);
  }

  return tokens;
}

export const CodeViewer: React.FC<CodeViewerProps> = ({
  code,
  filePath,
  className = '',
  maxHeight = '100%',
}) => {
  const [copied, setCopied] = useState(false);
  const [wrapLines, setWrapLines] = useState(false);

  const ext = useMemo(() => {
    const parts = filePath.split('.');
    return parts.length > 1 ? parts.pop()?.toLowerCase() || '' : '';
  }, [filePath]);

  const lines = useMemo(() => {
    return (code || '').split('\n');
  }, [code]);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([code], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filePath.split('/').pop() || 'file.txt';
    link.click();
    URL.revokeObjectURL(url);
  };

  const getTokenColor = (type: TokenType) => {
    switch (type) {
      case 'keyword':
        return 'text-[#C084FC] font-semibold'; // Light purple
      case 'string':
        return 'text-[#86EFAC]'; // Soft emerald
      case 'comment':
        return 'text-[#64748B] italic'; // Slate gray
      case 'number':
        return 'text-[#FDE047]'; // Amber yellow
      case 'tag':
        return 'text-[#F472B6] font-semibold'; // Soft pink
      case 'attr':
        return 'text-[#38BDF8]'; // Cyan
      case 'function':
        return 'text-[#60A5FA]'; // Sky blue
      case 'text':
      default:
        return 'text-[#E2E8F0]';
    }
  };

  return (
    <div className={`flex flex-col h-full bg-[#07040F] border border-border-subtle/60 rounded-xl overflow-hidden shadow-2xl ${className}`}>
      {/* Top File Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-[#0E081F] border-b border-border-subtle/50 text-xs font-mono select-none">
        <div className="flex items-center gap-2 text-text">
          <FileCode className="w-3.5 h-3.5 text-primary-light" />
          <span className="font-semibold text-primary-light">{filePath}</span>
          <span className="text-[10px] text-text-muted px-1.5 py-0.5 rounded bg-surface-elevated border border-border-subtle/40">
            {ext.toUpperCase() || 'TEXT'}
          </span>
          <span className="text-[10px] text-text-muted/80">
            {lines.length} line{lines.length !== 1 ? 's' : ''} · {new Blob([code]).size} B
          </span>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => setWrapLines(!wrapLines)}
            className={`p-1.5 rounded-lg transition-colors flex items-center gap-1 text-[11px] ${
              wrapLines ? 'bg-primary-deep/50 text-white' : 'text-text-muted hover:text-text hover:bg-white/5'
            }`}
            title="Toggle Line Wrap"
          >
            <AlignLeft className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Wrap</span>
          </button>

          <button
            onClick={handleDownload}
            className="p-1.5 rounded-lg text-text-muted hover:text-text hover:bg-white/5 transition-colors flex items-center gap-1 text-[11px]"
            title="Download file"
          >
            <Download className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Download</span>
          </button>

          <button
            onClick={handleCopy}
            className="p-1.5 rounded-lg text-text-muted hover:text-emerald-300 hover:bg-emerald-500/10 transition-colors flex items-center gap-1 text-[11px]"
            title="Copy code to clipboard"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-emerald-400 font-semibold">Copied</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5" />
                <span>Copy</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Code Editor Body */}
      <div
        className="flex-1 overflow-auto bg-[#07040F] font-mono text-[12px] leading-relaxed p-2"
        style={{ maxHeight }}
      >
        <table className={`w-full border-collapse ${wrapLines ? 'break-words' : 'whitespace-pre'}`}>
          <tbody>
            {lines.map((line, idx) => {
              const tokens = tokenizeLine(line, ext);
              const lineNum = idx + 1;
              return (
                <tr key={idx} className="hover:bg-white/[0.03] transition-colors group">
                  {/* Sticky Line Number */}
                  <td className="w-12 pr-4 text-right select-none text-text-faint/60 group-hover:text-text-muted align-top text-[11px] font-mono py-0.5">
                    {lineNum}
                  </td>
                  {/* Syntax Colored Line */}
                  <td className={`pl-2 select-text py-0.5 ${wrapLines ? 'whitespace-pre-wrap break-all' : 'whitespace-pre'}`}>
                    {tokens.map((tok, tIdx) => (
                      <span key={tIdx} className={getTokenColor(tok.type)}>
                        {tok.text}
                      </span>
                    ))}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
