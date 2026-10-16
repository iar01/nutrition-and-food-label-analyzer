'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Bot, User, Loader2, Sparkles } from 'lucide-react';
import { postChat } from '@/lib/api/client';
import { readSse } from '@/lib/api/sse';
import { FollowupChips } from '@/components/chat/followup-chips';
import { Button } from '@/components/ui/button';
import type { Profile } from '@/lib/api/types';

interface Message {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  isStreaming?: boolean;
}

interface ChatThreadProps {
  threadId: string;
  profile: Profile;
  productName: string;
}

export function ChatThread({ threadId, profile, productName }: ChatThreadProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [stepLabel, setStepLabel] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  const scrollToBottom = useCallback(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, stepLabel, scrollToBottom]);

  const handleSend = async (questionText?: string) => {
    const textToSend = (questionText ?? input).trim();
    if (!textToSend || loading) return;

    setInput('');
    const userMsgId = `user-${Date.now()}`;
    const assistantMsgId = `assistant-${Date.now()}`;

    setMessages((prev) => [
      ...prev,
      { id: userMsgId, sender: 'user', text: textToSend },
      { id: assistantMsgId, sender: 'assistant', text: '', isStreaming: true },
    ]);

    setLoading(true);
    setStepLabel('Understanding question…');

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const response = await postChat(
        {
          message: textToSend,
          thread_id: threadId,
          profile,
        },
        controller.signal,
      );

      let accumulated = '';
      for await (const { event, data } of readSse(response)) {
        if (event === 'step') {
          const stepData = data as { label?: string; node?: string };
          if (stepData.label) {
            setStepLabel(stepData.label);
          }
        } else if (event === 'answer_chunk') {
          const chunkData = data as { text?: string };
          if (chunkData.text) {
            accumulated += chunkData.text;
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMsgId ? { ...msg, text: accumulated } : msg,
              ),
            );
          }
        } else if (event === 'final') {
          const finalData = data as { answer_markdown?: string };
          if (finalData.answer_markdown && !accumulated) {
            accumulated = finalData.answer_markdown;
          }
        } else if (event === 'error') {
          const errData = data as { message?: string };
          accumulated += `\n\n*(Error: ${errData.message ?? 'Failed to complete response.'})*`;
        }
      }

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMsgId
            ? { ...msg, text: accumulated || 'No response generated.', isStreaming: false }
            : msg,
        ),
      );
    } catch {
      if (!controller.signal.aborted) {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId
              ? {
                  ...msg,
                  text: 'Sorry, I encountered an error while answering your question. Please try again.',
                  isStreaming: false,
                }
              : msg,
          ),
        );
      }
    } finally {
      setLoading(false);
      setStepLabel(null);
    }
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <section
      aria-label="Interactive Product Conversation"
      className="space-y-4 rounded-2xl border border-border/80 bg-card p-5 shadow-xs transition-all sm:p-6"
    >
      <header className="flex flex-wrap items-center justify-between gap-2 border-b border-border/60 pb-3">
        <div className="flex items-center gap-2">
          <div className="flex size-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <Bot aria-hidden className="size-4.5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-foreground">Ask LabelLens Copilot</h2>
            <p className="text-xs text-muted-foreground">
              Conversational nutrition assistant for <strong>{productName}</strong>
            </p>
          </div>
        </div>
        <span className="rounded-full bg-secondary px-2.5 py-0.5 text-[11px] font-semibold text-muted-foreground">
          Active Thread
        </span>
      </header>

      {/* Message Stream */}
      <div className="space-y-4 max-h-[500px] overflow-y-auto pr-1">
        {messages.length === 0 ? (
          <div className="rounded-xl border border-dashed border-border/80 bg-secondary/20 p-4 text-center sm:p-6">
            <Sparkles aria-hidden className="mx-auto size-6 text-primary/70 mb-2" />
            <p className="text-xs font-semibold text-foreground sm:text-sm">
              Have questions about {productName}?
            </p>
            <p className="mt-1 text-xs text-muted-foreground max-w-md mx-auto">
              Ask about specific ingredients, suitability for family members, hidden sugars, or additive safety.
            </p>
            <div className="mt-4 flex justify-center">
              <FollowupChips onSelect={(prompt) => handleSend(prompt)} disabled={loading} />
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex items-start gap-3 ${
                msg.sender === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              {msg.sender === 'assistant' && (
                <div className="flex size-7 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary mt-1">
                  <Bot className="size-4" />
                </div>
              )}
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-3 text-xs sm:text-sm leading-relaxed shadow-2xs ${
                  msg.sender === 'user'
                    ? 'bg-primary text-primary-foreground rounded-tr-xs'
                    : 'bg-muted/70 text-foreground border border-border/70 rounded-tl-xs whitespace-pre-wrap'
                }`}
              >
                {msg.text || (msg.isStreaming ? (
                  <span className="inline-flex items-center gap-1.5 text-muted-foreground italic">
                    <Loader2 className="size-3.5 animate-spin" />
                    {stepLabel ?? 'Thinking…'}
                  </span>
                ) : '')}
              </div>
              {msg.sender === 'user' && (
                <div className="flex size-7 shrink-0 items-center justify-center rounded-lg bg-secondary text-secondary-foreground mt-1">
                  <User className="size-4" />
                </div>
              )}
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>

      {messages.length > 0 && !loading && (
        <FollowupChips onSelect={(prompt) => handleSend(prompt)} disabled={loading} />
      )}

      {/* Input Bar */}
      <div className="relative flex items-end gap-2 pt-2">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder={`Ask anything about ${productName}… (Press Enter to send)`}
          rows={1}
          disabled={loading}
          className="flex-1 resize-none rounded-xl border border-border/80 bg-background px-3.5 py-2.5 text-xs sm:text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-hidden focus:ring-1 focus:ring-primary disabled:opacity-50"
        />
        <Button
          type="button"
          onClick={() => handleSend()}
          disabled={!input.trim() || loading}
          size="sm"
          className="h-10 px-4 rounded-xl font-medium gap-1.5 cursor-pointer"
        >
          {loading ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <>
              <Send className="size-3.5" />
              <span>Send</span>
            </>
          )}
        </Button>
      </div>

      <footer className="flex items-center justify-between text-[11px] text-muted-foreground pt-1">
        <span>⚠️ Learning project: Not health advice.</span>
        <span>Always check package labels.</span>
      </footer>
    </section>
  );
}
