import React, { useEffect } from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import { Table } from '@tiptap/extension-table';
import { TableRow } from '@tiptap/extension-table-row';
import { TableHeader } from '@tiptap/extension-table-header';
import { TableCell } from '@tiptap/extension-table-cell';
import { Placeholder } from '@tiptap/extension-placeholder';
import { Markdown } from 'tiptap-markdown';
import { 
  Bold, Italic, List, ListOrdered, Table as TableIcon, 
  RotateCcw, Wand2, Type, Quote, Heading1, Heading2 
} from 'lucide-react';

interface TiptapEditorProps {
  content: string;
  onChange: (content: string) => void;
  onAIRewrite?: (text: string) => void;
  placeholder?: string;
  className?: string;
}

const TiptapEditor: React.FC<TiptapEditorProps> = ({ 
  content, 
  onChange, 
  onAIRewrite,
  placeholder = '开始起草标书正文...',
  className = ''
}) => {
  const editor = useEditor({
    extensions: [
      StarterKit,
      Markdown,
      Table.configure({
        resizable: true,
      }),
      TableRow,
      TableHeader,
      TableCell,
      Placeholder.configure({
        placeholder,
      }),
    ],
    content: content,
    onUpdate: ({ editor }) => {
      // Return markdown string to the parent
      onChange((editor.storage as any).markdown.getMarkdown());
    },
    editorProps: {
      attributes: {
        class: 'prose prose-sm dark:prose-invert max-w-none focus:outline-none min-h-[500px] px-6 py-5',
      },
    },
  });

  // Keep editor content in sync with external content (e.g. when changing chapters)
  useEffect(() => {
    if (editor && content !== (editor.storage as any).markdown.getMarkdown()) {
      editor.commands.setContent(content);
    }
  }, [content, editor]);

  if (!editor) {
    return null;
  }

  return (
    <div className={`flex flex-col border border-zinc-100 rounded-3xl bg-white overflow-hidden shadow-sm ${className}`}>
      {/* Toolbar */}
      <div className="flex items-center flex-wrap gap-1 px-4 py-2 border-b border-zinc-100 bg-zinc-50/50">
        <button
          onClick={() => editor.chain().focus().toggleBold().run()}
          className={`p-2 rounded-lg hover:bg-zinc-200 transition-colors ${editor.isActive('bold') ? 'bg-zinc-200 text-primary' : 'text-zinc-500'}`}
          title="加粗"
        >
          <Bold size={16} />
        </button>
        <button
          onClick={() => editor.chain().focus().toggleItalic().run()}
          className={`p-2 rounded-lg hover:bg-zinc-200 transition-colors ${editor.isActive('italic') ? 'bg-zinc-200 text-primary' : 'text-zinc-500'}`}
          title="斜体"
        >
          <Italic size={16} />
        </button>
        <div className="w-px h-4 bg-zinc-200 mx-1"></div>
        <button
          onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
          className={`p-2 rounded-lg hover:bg-zinc-200 transition-colors ${editor.isActive('heading', { level: 1 }) ? 'bg-zinc-200 text-primary' : 'text-zinc-500'}`}
          title="标题 1"
        >
          <Heading1 size={16} />
        </button>
        <button
          onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
          className={`p-2 rounded-lg hover:bg-zinc-200 transition-colors ${editor.isActive('heading', { level: 2 }) ? 'bg-zinc-200 text-primary' : 'text-zinc-500'}`}
          title="标题 2"
        >
          <Heading2 size={16} />
        </button>
        <div className="w-px h-4 bg-zinc-200 mx-1"></div>
        <button
          onClick={() => editor.chain().focus().toggleBulletList().run()}
          className={`p-2 rounded-lg hover:bg-zinc-200 transition-colors ${editor.isActive('bulletList') ? 'bg-zinc-200 text-primary' : 'text-zinc-500'}`}
          title="无序列表"
        >
          <List size={16} />
        </button>
        <button
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
          className={`p-2 rounded-lg hover:bg-zinc-200 transition-colors ${editor.isActive('orderedList') ? 'bg-zinc-200 text-primary' : 'text-zinc-500'}`}
          title="有序列表"
        >
          <ListOrdered size={16} />
        </button>
        <div className="w-px h-4 bg-zinc-200 mx-1"></div>
        <button
          onClick={() => editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run()}
          className="p-2 rounded-lg hover:bg-zinc-200 transition-colors text-zinc-500"
          title="插入表格"
        >
          <TableIcon size={16} />
        </button>
        {onAIRewrite && (
          <>
            <div className="w-px h-4 bg-zinc-200 mx-1"></div>
            <button
              onClick={() => {
                const selection = editor.state.selection;
                const text = editor.state.doc.textBetween(selection.from, selection.to);
                if (text.trim()) {
                  onAIRewrite(text);
                }
              }}
              className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-zinc-200 transition-colors text-zinc-600"
              title="AI 润色当前选区"
            >
              <Wand2 size={16} />
              <span className="text-xs font-bold">AI 润色选区</span>
            </button>
          </>
        )}
        <div className="flex-1"></div>
        <button
          onClick={() => editor.chain().focus().undo().run()}
          className="p-2 rounded-lg hover:bg-zinc-200 transition-colors text-zinc-500"
          title="注销"
        >
          <RotateCcw size={16} />
        </button>
      </div>

      {/* Editor Content */}
      <div className="relative">
        <EditorContent editor={editor} />
      </div>

      {/* Footer Info */}
      <div className="px-6 py-2 border-t border-zinc-100 bg-zinc-50/30 flex items-center justify-between text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
         <div className="flex items-center gap-2">
            <span className="flex items-center gap-1"><Type size={10} /> RICH TEXT ENABLED</span>
            <span className="w-1 h-1 rounded-full bg-zinc-300"></span>
            <span className="flex items-center gap-1"><Quote size={10} /> MARKDOWN NATIVE</span>
         </div>
         <div>SELECT TEXT TO TRIGGER AI REWRITE</div>
      </div>
    </div>
  );
};

export default TiptapEditor;
