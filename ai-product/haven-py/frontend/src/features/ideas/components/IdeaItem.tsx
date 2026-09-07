import { motion } from 'framer-motion';
import { deleteIdea, toggleIdea, type Idea } from '../../../api/ideas';

interface Props {
  idea: Idea;
  index: number;
  onChanged: () => void;
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

function formatDate(iso: string): string {
  const d = new Date(iso);
  return `${MONTHS[d.getMonth()]} ${d.getDate()}`;
}

export default function IdeaItem({ idea, index, onChanged }: Props) {
  const handleToggle = async () => {
    try {
      await toggleIdea(idea.id);
      onChanged();
    } catch (e) {
      console.error('操作失败', e);
    }
  };

  const handleDelete = async () => {
    try {
      await deleteIdea(idea.id);
      onChanged();
    } catch (e) {
      console.error('删除失败', e);
    }
  };

  const rotate = ((index % 3) - 1) * 0.8;
  const colorClass = `c${index % 5}`;
  const done = Boolean(idea.is_completed);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20, rotate: rotate - 2 }}
      animate={{ opacity: 1, y: 0, rotate }}
      exit={{ opacity: 0, x: -60, rotate: -8 }}
      transition={{ duration: 0.3, type: 'spring', stiffness: 120 }}
      className={`idea-note ${colorClass} ${done ? 'done' : ''}`}
    >
      <div className="idea-pin" />

      <p className="idea-text">{idea.content}</p>

      <div className="idea-actions">
        <button onClick={handleToggle} className={`idea-check ${done ? 'done' : ''}`}>
          <span className="idea-check-box">
            {done && (
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none">
                <path
                  d="M5 13l4 4L19 7"
                  stroke="currentColor"
                  strokeWidth="3"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            )}
          </span>
          {done ? '已入夜' : '划掉'}
        </button>

        <span className="idea-date">{formatDate(idea.created_at)}</span>

        <button onClick={handleDelete} className="idea-delete" title="烧掉这张">
          ✕
        </button>
      </div>
    </motion.div>
  );
}
