package com.myidea.viewmodel;

import android.app.Application;
import android.content.Context;
import android.content.SharedPreferences;

import androidx.annotation.NonNull;
import androidx.lifecycle.AndroidViewModel;
import androidx.lifecycle.LiveData;
import androidx.lifecycle.MutableLiveData;
import androidx.lifecycle.Transformations;

import com.myidea.data.Idea;
import com.myidea.data.IdeaRepository;

import java.util.List;

public class IdeaViewModel extends AndroidViewModel {

    private static final String PREFS_NAME = "myidea_prefs";
    private static final String KEY_SORT_MODE = "sort_mode";

    private final IdeaRepository repository;
    private final SharedPreferences prefs;
    private final MutableLiveData<Integer> sortMode = new MutableLiveData<>();
    private final LiveData<List<Idea>> ideas;

    public IdeaViewModel(@NonNull Application application) {
        super(application);
        repository = IdeaRepository.getInstance(application);
        prefs = application.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        sortMode.setValue(prefs.getInt(KEY_SORT_MODE, IdeaRepository.SORT_NEWEST));
        ideas = Transformations.switchMap(sortMode, repository::observe);
    }

    public LiveData<List<Idea>> getIdeas() {
        return ideas;
    }

    public LiveData<Integer> getSortMode() {
        return sortMode;
    }

    public void setSortMode(int mode) {
        prefs.edit().putInt(KEY_SORT_MODE, mode).apply();
        sortMode.setValue(mode);
    }

    public void insert(String content) {
        repository.insert(content);
    }

    public void delete(Idea idea) {
        repository.delete(idea);
    }

    public void saveCustomOrder(List<Idea> ordered) {
        repository.saveCustomOrder(ordered);
        Integer current = sortMode.getValue();
        if (current == null || current != IdeaRepository.SORT_CUSTOM) {
            setSortMode(IdeaRepository.SORT_CUSTOM);
        }
    }
}
