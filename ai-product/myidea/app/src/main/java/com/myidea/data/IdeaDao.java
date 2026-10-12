package com.myidea.data;

import androidx.lifecycle.LiveData;
import androidx.room.Dao;
import androidx.room.Delete;
import androidx.room.Insert;
import androidx.room.Query;

import java.util.List;

@Dao
public interface IdeaDao {

    @Query("SELECT * FROM ideas ORDER BY createTime DESC")
    LiveData<List<Idea>> observeByTimeDesc();

    @Query("SELECT * FROM ideas ORDER BY createTime ASC")
    LiveData<List<Idea>> observeByTimeAsc();

    @Query("SELECT * FROM ideas ORDER BY sortOrder ASC")
    LiveData<List<Idea>> observeByCustomOrder();

    @Query("SELECT * FROM ideas ORDER BY sortOrder ASC")
    List<Idea> listByCustomOrder();

    @Query("SELECT * FROM ideas ORDER BY createTime DESC")
    List<Idea> listByTimeDesc();

    @Query("SELECT COUNT(*) FROM ideas")
    int count();

    @Insert
    long insert(Idea idea);

    @Delete
    void delete(Idea idea);

    @Query("DELETE FROM ideas WHERE id = :id")
    void deleteById(long id);

    @Query("UPDATE ideas SET sortOrder = :sortOrder WHERE id = :id")
    void updateSortOrder(long id, int sortOrder);
}
