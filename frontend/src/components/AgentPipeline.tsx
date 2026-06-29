interface Step {
  label: string;
  status: 'pending' | 'running' | 'done' | 'error';
}

export default function AgentPipeline({ steps }: { steps: Step[] }) {
  return (
    <div className="pipeline">
      {steps.map((step, i) => (
        <div key={i} className={`pipeline-step pipeline-step--${step.status}`}>
          <span className="pipeline-icon">
            {step.status === 'done' && '✓'}
            {step.status === 'running' && '⟳'}
            {step.status === 'error' && '✕'}
            {step.status === 'pending' && '○'}
          </span>
          <span className="pipeline-label">{step.label}</span>
        </div>
      ))}
    </div>
  );
}
