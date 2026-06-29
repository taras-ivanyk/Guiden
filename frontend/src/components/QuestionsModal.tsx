import { useState } from 'react';

interface Props {
  questions: string[];
  open: boolean;
  onClose: () => void;
  onSubmit: (answers: Record<string, string>) => void;
  loading: boolean;
}

export default function QuestionsModal({ questions, open, onClose, onSubmit, loading }: Props) {
  const [answers, setAnswers] = useState<Record<string, string>>(() =>
    Object.fromEntries(questions.map(q => [q, '']))
  );

  if (!open) return null;

  function setAnswer(q: string, val: string) {
    setAnswers(prev => ({ ...prev, [q]: val }));
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-panel" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Coach's Questions</h3>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        <p className="modal-subtitle">Your answers help personalise the coaching feedback.</p>

        <div className="modal-body">
          {questions.map((q, i) => (
            <div key={i} className="modal-question">
              <p className="modal-q-text">{i + 1}. {q}</p>
              <textarea
                className="modal-answer"
                rows={2}
                placeholder="Your answer…"
                value={answers[q]}
                onChange={e => setAnswer(q, e.target.value)}
              />
            </div>
          ))}
        </div>

        <div className="modal-footer">
          <button className="btn-ghost" onClick={onClose}>Skip</button>
          <button
            className="btn-primary"
            onClick={() => onSubmit(answers)}
            disabled={loading}
          >
            {loading ? 'Refining…' : 'Refine Analysis →'}
          </button>
        </div>
      </div>
    </div>
  );
}
