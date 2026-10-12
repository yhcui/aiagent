package com.myidea;

import android.content.Context;

import androidx.room.Room;
import androidx.test.core.app.ApplicationProvider;
import androidx.test.ext.junit.runners.AndroidJUnit4;

import com.myidea.data.Idea;
import com.myidea.data.IdeaDao;
import com.myidea.data.IdeaDatabase;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;

import java.util.List;

import static org.junit.Assert.assertEquals;

@RunWith(AndroidJUnit4.class)
public class RoomDaoTest {

    private IdeaDatabase db;
    private IdeaDao dao;

    @Before
    public void setUp() {
        Context context = ApplicationProvider.getApplicationContext();
        db = Room.inMemoryDatabaseBuilder(context, IdeaDatabase.class)
                .allowMainThreadQueries()
                .build();
        dao = db.ideaDao();
    }

    @After
    public void tearDown() {
        db.close();
    }

    private long insert(String content, long createTime, int sortOrder) {
        return dao.insert(new Idea(content, createTime, sortOrder));
    }

    @Test
    public void insertAndCount() {
        insert("a", 1000L, 0);
        insert("b", 2000L, -1);
        assertEquals(2, dao.count());
    }

    @Test
    public void customOrderSorting() {
        insert("a", 1000L, 5);
        insert("b", 2000L, 1);
        insert("c", 3000L, 3);
        List<Idea> list = dao.listByCustomOrder();
        assertEquals(3, list.size());
        assertEquals("b", list.get(0).content);
        assertEquals("c", list.get(1).content);
        assertEquals("a", list.get(2).content);
    }

    @Test
    public void timeOrderSorting() {
        insert("a", 1000L, 0);
        insert("b", 3000L, 1);
        insert("c", 2000L, 2);
        List<Idea> list = dao.listByTimeDesc();
        assertEquals(3, list.size());
        assertEquals("b", list.get(0).content);
        assertEquals("c", list.get(1).content);
        assertEquals("a", list.get(2).content);
    }

    @Test
    public void deleteByIdRemovesRow() {
        long id = insert("x", 0L, 0);
        assertEquals(1, dao.count());
        dao.deleteById(id);
        assertEquals(0, dao.count());
    }

    @Test
    public void updateSortOrderPersists() {
        long id1 = insert("a", 0L, 0);
        long id2 = insert("b", 0L, 1);
        dao.updateSortOrder(id2, 0);
        dao.updateSortOrder(id1, 1);
        List<Idea> list = dao.listByCustomOrder();
        assertEquals("b", list.get(0).content);
        assertEquals("a", list.get(1).content);
    }
}
