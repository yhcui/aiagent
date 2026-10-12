package com.myidea.data;

import androidx.room.Entity;
import androidx.room.PrimaryKey;

@Entity(tableName = "ideas")
public class Idea {

    @PrimaryKey(autoGenerate = true)
    public long id;

    public String content;

    public long createTime;

    public int sortOrder;

    public Idea() {
    }

    public Idea(String content, long createTime, int sortOrder) {
        this.content = content;
        this.createTime = createTime;
        this.sortOrder = sortOrder;
    }
}
