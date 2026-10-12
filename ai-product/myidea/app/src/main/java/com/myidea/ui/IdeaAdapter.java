package com.myidea.ui;

import android.annotation.SuppressLint;
import android.content.Context;
import android.graphics.drawable.Drawable;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.InsetDrawable;
import android.graphics.drawable.LayerDrawable;
import android.view.LayoutInflater;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.myidea.R;
import com.myidea.data.Idea;
import com.myidea.utils.DateUtils;

import java.util.ArrayList;
import java.util.List;

public class IdeaAdapter extends RecyclerView.Adapter<IdeaAdapter.Holder> {

    public interface Listener {
        void onDelete(Idea idea);

        void onStartDrag(Holder holder);
    }

    private final List<Idea> items = new ArrayList<>();
    private final Listener listener;
    private Holder draggingHolder;

    public IdeaAdapter(Listener listener) {
        this.listener = listener;
    }

    public void submit(List<Idea> list) {
        items.clear();
        items.addAll(list);
        draggingHolder = null;
        notifyDataSetChanged();
    }

    public void move(int from, int to) {
        if (from < 0 || to < 0 || from >= items.size() || to >= items.size()) {
            return;
        }
        items.add(to, items.remove(from));
        notifyItemMoved(from, to);
    }

    public List<Idea> getItems() {
        return new ArrayList<>(items);
    }

    public void setDragging(Holder holder, boolean dragging) {
        draggingHolder = dragging ? holder : null;
        holder.setDragAppearance(dragging);
    }

    @NonNull
    @Override
    public Holder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_idea, parent, false);
        return new Holder(view, listener);
    }

    @Override
    public void onBindViewHolder(@NonNull Holder holder, int position) {
        holder.bind(items.get(position), holder == draggingHolder);
    }

    @Override
    public int getItemCount() {
        return items.size();
    }

    public static class Holder extends RecyclerView.ViewHolder {

        private final TextView content;
        private final TextView time;
        private final TextView delete;
        private final View handle;
        private Idea idea;

        Holder(@NonNull View itemView, final Listener listener) {
            super(itemView);
            content = itemView.findViewById(R.id.content);
            time = itemView.findViewById(R.id.time);
            delete = itemView.findViewById(R.id.delete);
            handle = itemView.findViewById(R.id.handle);
            delete.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    if (idea != null) {
                        listener.onDelete(idea);
                    }
                }
            });
            handle.setOnTouchListener(new View.OnTouchListener() {
                @SuppressLint("ClickableViewAccessibility")
                @Override
                public boolean onTouch(View v, MotionEvent event) {
                    if (event.getActionMasked() == MotionEvent.ACTION_DOWN) {
                        listener.onStartDrag(Holder.this);
                    }
                    return false;
                }
            });
        }

        void bind(Idea idea, boolean dragging) {
            this.idea = idea;
            content.setText(idea.content);
            time.setText(DateUtils.format(idea.createTime));
            itemView.setBackground(
                    makeCardBackground(itemView.getContext(), idea.id, dragging));
            float scale = dragging ? 1.02f : 1f;
            itemView.setScaleX(scale);
            itemView.setScaleY(scale);
            itemView.setElevation(dragging ? dp(itemView, 12) : 0f);
        }

        void setDragAppearance(boolean dragging) {
            if (idea == null) {
                return;
            }
            itemView.setBackground(
                    makeCardBackground(itemView.getContext(), idea.id, dragging));
            float scale = dragging ? 1.02f : 1f;
            itemView.animate().scaleX(scale).scaleY(scale).setDuration(120).start();
            itemView.setElevation(dragging ? dp(itemView, 12) : 0f);
        }

        private static float dp(View view, int value) {
            return value * view.getResources().getDisplayMetrics().density;
        }
    }

    static Drawable makeCardBackground(Context context, long id, boolean bright) {
        float density = context.getResources().getDisplayMetrics().density;
        GradientDrawable.Orientation[] orientations = GradientDrawable.Orientation.values();
        GradientDrawable.Orientation orientation =
                orientations[(int) (id % orientations.length)];
        int c1 = bright ? 0xFFA78BFA : 0x80A78BFA;
        int c2 = bright ? 0xFF22D3EE : 0x6622D3EE;
        GradientDrawable border = new GradientDrawable(orientation, new int[]{c1, c2});
        border.setCornerRadius(14 * density);
        GradientDrawable fill = new GradientDrawable();
        fill.setCornerRadius(13 * density);
        fill.setColor(bright ? 0xF21A2038 : 0xF20D1322);
        int inset = (int) Math.ceil(1.2f * density);
        InsetDrawable insetFill = new InsetDrawable(fill, inset, inset, inset, inset);
        return new LayerDrawable(new Drawable[]{border, insetFill});
    }
}
