package com.myidea.data;

import android.content.Context;

import androidx.lifecycle.LiveData;

import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class IdeaRepository {

    public static final int SORT_NEWEST = 0;
    public static final int SORT_OLDEST = 1;
    public static final int SORT_CUSTOM = 2;

    private static volatile IdeaRepository INSTANCE;

    private final IdeaDatabase database;
    private final IdeaDao dao;
    private final ExecutorService executor = Executors.newSingleThreadExecutor();

    private IdeaRepository(Context context) {
        database = IdeaDatabase.getInstance(context);
        dao = database.ideaDao();
    }

    public static IdeaRepository getInstance(Context context) {
        if (INSTANCE == null) {
            synchronized (IdeaRepository.class) {
                if (INSTANCE == null) {
                    INSTANCE = new IdeaRepository(context.getApplicationContext());
                }
            }
        }
        return INSTANCE;
    }

    public LiveData<List<Idea>> observe(int sortMode) {
        if (sortMode == SORT_OLDEST) {
            return dao.observeByTimeAsc();
        }
        if (sortMode == SORT_CUSTOM) {
            return dao.observeByCustomOrder();
        }
        return dao.observeByTimeDesc();
    }

    public void insert(String content) {
        final String text = content == null ? "" : content.trim();
        if (text.isEmpty()) {
            return;
        }
        executor.execute(new Runnable() {
            @Override
            public void run() {
                List<Idea> all = dao.listByCustomOrder();
                int order = all.isEmpty() ? 0 : all.get(0).sortOrder - 1;
                dao.insert(new Idea(text, System.currentTimeMillis(), order));
            }
        });
    }

    public void delete(final Idea idea) {
        executor.execute(new Runnable() {
            @Override
            public void run() {
                dao.delete(idea);
            }
        });
    }

    public void saveCustomOrder(final List<Idea> ordered) {
        executor.execute(new Runnable() {
            @Override
            public void run() {
                database.runInTransaction(new Runnable() {
                    @Override
                    public void run() {
                        for (int i = 0; i < ordered.size(); i++) {
                            dao.updateSortOrder(ordered.get(i).id, i);
                        }
                    }
                });
            }
        });
    }
}
