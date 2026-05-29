/**
 * useSSE.js — Server-Sent Events hook for streaming chat responses.
 *
 * Manages the full SSE lifecycle:
 * - Opens EventSource connection to /api/chat/message
 * - Accumulates streamed delta tokens
 * - Surfaces tool_call / tool_result events
 * - Handles error and done events
 * - Cleans up on unmount
 *
 * Dependencies: apiClient.js (for token), endpoints.js (Tier 3)
 * Consumed by: ChatInterface component
 *
 * NOTE: EventSource does not support POST with body.
 * Backend must accept clientId + query as query params on a GET
 * endpoint, OR we use fetch() with ReadableStream (implemented below).
 */

import { useState, useRef, useCallback } from 'react';
import { authStorage } from '../api/apiClient.js';
import { ENDPOINTS } from '../api/endpoints.js';

// ─── Types ────────────────────────────────────────────────────────────────────

/**
 * @typedef {Object} SSEState
 * @property {string}   fullText      - Accumulated response text
 * @property {boolean}  isStreaming   - True while connection is open
 * @property {boolean}  isDone        - True after 'done' event
 * @property {string|null} error      - Error message if stream failed
 * @property {Array}    toolCalls     - List of tool_call events seen
 * @property {number}   confidence    - Final confidence score (from done event)
 */

// ─── Hook ─────────────────────────────────────────────────────────────────────

/**
 * useSSE — stream chat responses from the backend.
 *
 * @example
 * const { fullText, isStreaming, isDone, error, sendMessage, reset } = useSSE();
 * await sendMessage({ client_id: 'C001', query: 'What is my XIRR?' });
 */
export function useSSE() {
  const [fullText, setFullText]       = useState('');
  const [isStreaming, setIsStreaming]  = useState(false);
  const [isDone, setIsDone]           = useState(false);
  const [error, setError]             = useState(null);
  const [toolCalls, setToolCalls]     = useState([]);
  const [confidence, setConfidence]   = useState(null);

  const abortRef = useRef(null);

  const reset = useCallback(() => {
    setFullText('');
    setIsStreaming(false);
    setIsDone(false);
    setError(null);
    setToolCalls([]);
    setConfidence(null);
  }, []);

  const abort = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
    setIsStreaming(false);
  }, []);

  /**
   * Send a message and stream the response.
   * @param {{ client_id: string, query: string, message_history?: Array }} payload
   */
  const sendMessage = useCallback(async (payload) => {
    reset();

    const controller = new AbortController();
    abortRef.current = controller;

    const token = authStorage.getToken();
    const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

    setIsStreaming(true);

    try {
      const response = await fetch(`${API_BASE}${ENDPOINTS.CHAT.MESSAGE}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `HTTP ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // Keep incomplete last line

        for (const line of lines) {
          if (!line.startsWith('data:')) continue;
          const raw = line.slice(5).trim();
          if (!raw) continue;

          try {
            const event = JSON.parse(raw);
            handleSSEEvent(event);
          } catch {
            // Malformed JSON line — skip
          }
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        setError(err.message || 'Stream failed');
      }
    } finally {
      setIsStreaming(false);
      abortRef.current = null;
    }
  }, [reset]);

  // ─── Event Dispatcher ───────────────────────────────────────────────────────

  function handleSSEEvent(event) {
    switch (event.type) {
      case 'delta':
        setFullText((prev) => prev + (event.text || ''));
        break;

      case 'tool_call':
        setToolCalls((prev) => [...prev, {
          name: event.tool_name,
          input: event.tool_input,
          id: event.tool_use_id,
        }]);
        break;

      case 'tool_result':
        // Tool result received — can surface in UI if needed
        break;

      case 'done':
        setIsDone(true);
        if (event.confidence !== undefined) {
          setConfidence(event.confidence);
        }
        break;

      case 'error':
        setError(event.message || 'An error occurred');
        break;

      default:
        break;
    }
  }

  return {
    fullText,
    isStreaming,
    isDone,
    error,
    toolCalls,
    confidence,
    sendMessage,
    reset,
    abort,
  };
}
