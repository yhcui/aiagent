package com.myidea;

import androidx.test.core.app.ActivityScenario;
import androidx.test.ext.junit.runners.AndroidJUnit4;

import org.junit.Test;
import org.junit.runner.RunWith;

import static androidx.test.espresso.Espresso.onView;
import static androidx.test.espresso.assertion.ViewAssertions.matches;
import static androidx.test.espresso.matcher.ViewMatchers.isDisplayed;
import static androidx.test.espresso.matcher.ViewMatchers.withId;

@RunWith(AndroidJUnit4.class)
public class MainActivitySmokeTest {

    @Test
    public void launchesWithCoreViewsVisible() {
        ActivityScenario<MainActivity> scenario = ActivityScenario.launch(MainActivity.class);
        try {
            onView(withId(R.id.fab)).check(matches(isDisplayed()));
            onView(withId(R.id.recycler)).check(matches(isDisplayed()));
            onView(withId(R.id.title)).check(matches(isDisplayed()));
        } finally {
            scenario.close();
        }
    }
}
