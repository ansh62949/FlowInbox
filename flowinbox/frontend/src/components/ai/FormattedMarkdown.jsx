import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { motion } from 'framer-motion';

export default function FormattedMarkdown({ content, className = '' }) {
  if (!content) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: 'easeOut' }}
      className={`prose prose-sm max-w-none text-xs leading-relaxed text-[#172335] ${className}`}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => (
            <h1 className="text-sm font-extrabold text-[#172335] mt-2 mb-1.5 border-b border-[#d7e3ee] pb-1 tracking-tight">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-xs font-bold text-[#172335] mt-2 mb-1 tracking-tight">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-xs font-bold text-[#2d7ed0] mt-1.5 mb-1">
              {children}
            </h3>
          ),
          p: ({ children }) => (
            <p className="mb-2 text-[#31516e] leading-relaxed last:mb-0">
              {children}
            </p>
          ),
          strong: ({ children }) => (
            <strong className="font-bold text-[#172335]">{children}</strong>
          ),
          ul: ({ children }) => (
            <ul className="my-2 space-y-2 pl-3 list-none border-l-2 border-[#cce5fb]">
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className="my-2 space-y-2 pl-4 list-decimal text-[#536176]">
              {children}
            </ol>
          ),
          li: ({ children }) => (
            <li className="text-[11px] leading-relaxed text-[#23354d] relative pl-1">
              {children}
            </li>
          ),
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noreferrer"
              className="text-[#2d7ed0] hover:underline font-medium"
            >
              {children}
            </a>
          ),
          blockquote: ({ children }) => (
            <blockquote className="border-l-2 border-[#2d7ed0] pl-3 py-1 my-2 bg-[#f0f7ff] rounded-r-lg italic text-[#536176]">
              {children}
            </blockquote>
          ),
          code: ({ inline, children }) => (
            inline ? (
              <code className="px-1.5 py-0.5 bg-[#eaf3fb] border border-[#d7e3ee] rounded text-[10px] font-mono text-[#2d7ed0]">
                {children}
              </code>
            ) : (
              <pre className="p-3 bg-[#172335] text-white rounded-xl text-[11px] font-mono overflow-x-auto my-2">
                <code>{children}</code>
              </pre>
            )
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </motion.div>
  );
}
