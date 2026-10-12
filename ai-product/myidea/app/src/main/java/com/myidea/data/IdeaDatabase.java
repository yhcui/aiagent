package com.myidea.data;

import android.content.Context;

import androidx.room.Database;
import androidx.room.Room;
import androidx.room.RoomDatabase;

@Database(entities = {Idea.class}, version = 1, exportSchema = false)
public abstract class IdeaDatabase extends RoomDatabase {

    private static volatile IdeaDatabase INSTANCE;

    public abstract IdeaDao ideaDao();

    public static IdeaDatabase getInstance(Context context) {
        if (INSTANCE == null) {
            synchronized (IdeaDatabase.class) {
                if (INSTANCE == null) {
                    INSTANCE = Room.databaseBuilder(
                                    context.getApplicationContext(),
                                    IdeaDatabase.class,
                                    "ideas.db")
                            .build();
                }
            }
        }
        return INSTANCE;
    }
}
