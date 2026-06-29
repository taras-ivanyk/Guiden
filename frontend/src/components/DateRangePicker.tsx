import { useState } from 'react';

const WEEKDAYS = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'];
const MONTHS = ['January','February','March','April','May','June',
  'July','August','September','October','November','December'];

function daysInMonth(y: number, m: number) { return new Date(y, m + 1, 0).getDate(); }
function firstWeekday(y: number, m: number) { return (new Date(y, m, 1).getDay() + 6) % 7; }
function toStr(y: number, m: number, d: number) {
  return `${y}-${String(m + 1).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
}
const todayStr = () => new Date().toISOString().slice(0, 10);
function daysAgoStr(n: number) {
  const d = new Date(); d.setDate(d.getDate() - n); return d.toISOString().slice(0, 10);
}

interface Props { onRangeChange: (start: string, end: string) => void; }

export default function DateRangePicker({ onRangeChange }: Props) {
  const now = new Date();
  const [vy, setVy] = useState(now.getFullYear());
  const [vm, setVm] = useState(now.getMonth());
  const [start, setStart] = useState<string | null>(null);
  const [end, setEnd] = useState<string | null>(null);
  const [hover, setHover] = useState<string | null>(null);
  const [activePreset, setActivePreset] = useState<string | null>(null);

  const today = todayStr();

  function applyPreset(label: string, days: number) {
    const s = daysAgoStr(days), e = today;
    setStart(s); setEnd(e); setActivePreset(label);
    onRangeChange(s, e);
  }

  function clickDay(ds: string) {
    if (ds > today) return;
    setActivePreset(null);
    if (!start || (start && end)) {
      setStart(ds); setEnd(null);
    } else {
      const [s, e] = ds < start ? [ds, start] : [start, ds];
      setStart(s); setEnd(e); onRangeChange(s, e);
    }
  }

  function prevMonth() {
    if (vm === 0) { setVy(y => y - 1); setVm(11); } else setVm(m => m - 1);
  }
  function nextMonth() {
    if (vm === 11) { setVy(y => y + 1); setVm(0); } else setVm(m => m + 1);
  }

  const blanks = firstWeekday(vy, vm);
  const total = daysInMonth(vy, vm);
  const cells: Array<{ ds: string; d: number } | null> = [
    ...Array(blanks).fill(null),
    ...Array.from({ length: total }, (_, i) => ({ ds: toStr(vy, vm, i + 1), d: i + 1 })),
  ];

  function dayClass(ds: string) {
    const ref = hover || end;
    if (ds === start) return 'drp-day drp-day--start';
    if (ds === end)   return 'drp-day drp-day--end';
    if (start && ref && ds > start && ds < ref) return 'drp-day drp-day--range';
    if (ds === today) return 'drp-day drp-day--today';
    return 'drp-day';
  }

  const presets = [
    { label: '7d', days: 7 }, { label: '30d', days: 30 },
    { label: '90d', days: 90 }, { label: '6mo', days: 180 },
  ];

  return (
    <div className="drp">
      <div className="drp-presets">
        {presets.map(p => (
          <button key={p.label}
            className={`drp-preset${activePreset === p.label ? ' drp-preset--active' : ''}`}
            onClick={() => applyPreset(p.label, p.days)}>
            Last {p.label}
          </button>
        ))}
      </div>

      <div className="drp-cal">
        <div className="drp-header">
          <button className="drp-nav" onClick={prevMonth}>‹</button>
          <span className="drp-month-label">{MONTHS[vm]} {vy}</span>
          <button className="drp-nav" onClick={nextMonth}>›</button>
        </div>

        <div className="drp-weekdays">
          {WEEKDAYS.map(w => <span key={w} className="drp-wd">{w}</span>)}
        </div>

        <div className="drp-grid">
          {cells.map((cell, i) =>
            cell === null
              ? <span key={`e${i}`} className="drp-day drp-day--empty" />
              : (
                <button key={cell.ds}
                  className={dayClass(cell.ds)}
                  onClick={() => clickDay(cell.ds)}
                  onMouseEnter={() => start && !end && setHover(cell.ds)}
                  onMouseLeave={() => setHover(null)}
                  disabled={cell.ds > today}>
                  {cell.d}
                </button>
              )
          )}
        </div>

        {(start || end) && (
          <div className="drp-selection">
            {start && <span className="drp-tag">{start}</span>}
            {start && !end && <span className="drp-hint">pick end date</span>}
            {end && <><span style={{ color: 'var(--text-subtle)', fontSize: '0.85rem' }}>→</span><span className="drp-tag">{end}</span></>}
          </div>
        )}
      </div>
    </div>
  );
}
