package com.myidea;

import android.animation.ObjectAnimator;
import android.animation.ValueAnimator;
import android.graphics.LinearGradient;
import android.graphics.Shader;
import android.os.Bundle;
import android.view.MenuItem;
import android.view.View;
import android.widget.ImageButton;
import android.widget.PopupMenu;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.lifecycle.Observer;
import androidx.lifecycle.ViewModelProvider;
import androidx.recyclerview.widget.ItemTouchHelper;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.myidea.data.Idea;
import com.myidea.data.IdeaRepository;
import com.myidea.ui.AddIdeaSheet;
import com.myidea.ui.IdeaAdapter;
import com.myidea.viewmodel.IdeaViewModel;

import java.util.List;

public class MainActivity extends AppCompatActivity {

    private IdeaViewModel viewModel;
    private IdeaAdapter adapter;
    private ItemTouchHelper itemTouchHelper;
    private TextView sortLabel;
    private View emptyState;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        sortLabel = findViewById(R.id.sort_label);
        emptyState = findViewById(R.id.empty_state);

        RecyclerView recycler = findViewById(R.id.recycler);
        recycler.setLayoutManager(new LinearLayoutManager(this));
        adapter = new IdeaAdapter(new IdeaAdapter.Listener() {
            @Override
            public void onDelete(Idea idea) {
                viewModel.delete(idea);
            }

            @Override
            public void onStartDrag(IdeaAdapter.Holder holder) {
                itemTouchHelper.startDrag(holder);
            }
        });
        recycler.setAdapter(adapter);

        itemTouchHelper = new ItemTouchHelper(new DragCallback());
        itemTouchHelper.attachToRecyclerView(recycler);

        viewModel = new ViewModelProvider(this).get(IdeaViewModel.class);
        viewModel.getIdeas().observe(this, new Observer<List<Idea>>() {
            @Override
            public void onChanged(List<Idea> ideas) {
                adapter.submit(ideas);
            }
        });
        viewModel.getSortMode().observe(this, new Observer<Integer>() {
            @Override
            public void onChanged(Integer mode) {
                updateSortLabel(mode);
            }
        });

        adapter.registerAdapterDataObserver(new RecyclerView.AdapterDataObserver() {
            @Override
            public void onChanged() {
                updateEmptyState();
            }
        });

        ImageButton fab = findViewById(R.id.fab);
        fab.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                new AddIdeaSheet().show(getSupportFragmentManager(), "add_idea");
            }
        });

        View sortButton = findViewById(R.id.sort_button);
        sortButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                showSortMenu(sortButton);
            }
        });

        applyGradient(findViewById(R.id.title),
                new int[]{0xFFF0F2F8, 0xFFA78BFA, 0xFF22D3EE},
                new float[]{0f, 0.55f, 1f});
        TextView spark = findViewById(R.id.spark);
        applyGradient(spark, new int[]{0xFFA78BFA, 0xFF22D3EE}, null);
        spark.setShadowLayer(14f, 0f, 0f, 0x66A78BFA);
        spark.setLayerType(View.LAYER_TYPE_SOFTWARE, null);

        startGlowAnimations();
        updateEmptyState();
    }

    private void updateSortLabel(Integer mode) {
        int m = mode == null ? IdeaRepository.SORT_NEWEST : mode;
        if (m == IdeaRepository.SORT_OLDEST) {
            sortLabel.setText(R.string.sort_oldest);
        } else if (m == IdeaRepository.SORT_CUSTOM) {
            sortLabel.setText(R.string.sort_custom);
        } else {
            sortLabel.setText(R.string.sort_newest);
        }
    }

    private void showSortMenu(View anchor) {
        PopupMenu popup = new PopupMenu(this, anchor);
        popup.getMenuInflater().inflate(R.menu.sort_menu, popup.getMenu());
        Integer current = viewModel.getSortMode().getValue();
        int m = current == null ? IdeaRepository.SORT_NEWEST : current;
        int idToCheck = m == IdeaRepository.SORT_OLDEST ? R.id.action_oldest
                : m == IdeaRepository.SORT_CUSTOM ? R.id.action_custom
                : R.id.action_newest;
        popup.getMenu().findItem(idToCheck).setChecked(true);
        popup.setOnMenuItemClickListener(new PopupMenu.OnMenuItemClickListener() {
            @Override
            public boolean onMenuItemClick(MenuItem item) {
                int id = item.getItemId();
                if (id == R.id.action_oldest) {
                    viewModel.setSortMode(IdeaRepository.SORT_OLDEST);
                } else if (id == R.id.action_custom) {
                    viewModel.setSortMode(IdeaRepository.SORT_CUSTOM);
                } else if (id == R.id.action_newest) {
                    viewModel.setSortMode(IdeaRepository.SORT_NEWEST);
                }
                return true;
            }
        });
        popup.show();
    }

    private void updateEmptyState() {
        boolean empty = adapter.getItemCount() == 0;
        emptyState.setVisibility(empty ? View.VISIBLE : View.GONE);
    }

    private void applyGradient(final TextView view, final int[] colors, final float[] positions) {
        view.post(new Runnable() {
            @Override
            public void run() {
                int width = (int) view.getPaint().measureText(view.getText().toString());
                if (width <= 0) {
                    width = view.getWidth();
                }
                if (width <= 0) {
                    return;
                }
                Shader shader = new LinearGradient(0, 0, width, 0,
                        colors, positions, Shader.TileMode.CLAMP);
                view.getPaint().setShader(shader);
                view.invalidate();
            }
        });
    }

    private void startGlowAnimations() {
        animateGlow(findViewById(R.id.glow_a), 90f, 120f, 26000, 32000);
        animateGlow(findViewById(R.id.glow_b), -100f, -110f, 30000, 24000);
    }

    private void animateGlow(View view, float dx, float dy, long durationX, long durationY) {
        if (view == null) {
            return;
        }
        float density = view.getResources().getDisplayMetrics().density;
        ObjectAnimator ax = ObjectAnimator.ofFloat(view, View.TRANSLATION_X, 0f, dx * density);
        ax.setDuration(durationX);
        ax.setRepeatCount(ValueAnimator.INFINITE);
        ax.setRepeatMode(ValueAnimator.REVERSE);
        ax.start();
        ObjectAnimator ay = ObjectAnimator.ofFloat(view, View.TRANSLATION_Y, 0f, dy * density);
        ay.setDuration(durationY);
        ay.setRepeatCount(ValueAnimator.INFINITE);
        ay.setRepeatMode(ValueAnimator.REVERSE);
        ay.start();
    }

    private class DragCallback extends ItemTouchHelper.Callback {

        private boolean moved = false;

        @Override
        public int getMovementFlags(@NonNull RecyclerView recyclerView,
                                    @NonNull RecyclerView.ViewHolder viewHolder) {
            return makeMovementFlags(ItemTouchHelper.UP | ItemTouchHelper.DOWN, 0);
        }

        @Override
        public boolean isLongPressDragEnabled() {
            return false;
        }

        @Override
        public boolean onMove(@NonNull RecyclerView recyclerView,
                              @NonNull RecyclerView.ViewHolder viewHolder,
                              @NonNull RecyclerView.ViewHolder target) {
            int from = viewHolder.getBindingAdapterPosition();
            int to = target.getBindingAdapterPosition();
            if (from == RecyclerView.NO_POSITION || to == RecyclerView.NO_POSITION) {
                return false;
            }
            adapter.move(from, to);
            moved = true;
            return true;
        }

        @Override
        public void onSwiped(@NonNull RecyclerView.ViewHolder viewHolder, int direction) {
        }

        @Override
        public void onSelectedChanged(RecyclerView.ViewHolder viewHolder, int actionState) {
            if (viewHolder != null && actionState == ItemTouchHelper.ACTION_STATE_DRAG
                    && viewHolder instanceof IdeaAdapter.Holder) {
                adapter.setDragging((IdeaAdapter.Holder) viewHolder, true);
            }
            super.onSelectedChanged(viewHolder, actionState);
        }

        @Override
        public void clearView(@NonNull RecyclerView recyclerView,
                              @NonNull RecyclerView.ViewHolder viewHolder) {
            super.clearView(recyclerView, viewHolder);
            if (viewHolder instanceof IdeaAdapter.Holder) {
                adapter.setDragging((IdeaAdapter.Holder) viewHolder, false);
            }
            if (moved) {
                moved = false;
                viewModel.saveCustomOrder(adapter.getItems());
            }
        }
    }
}
