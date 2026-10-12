package com.myidea;

import com.myidea.utils.DateUtils;

import org.junit.Test;

import java.util.Calendar;
import java.util.GregorianCalendar;
import java.util.Locale;

import static org.junit.Assert.assertEquals;

public class DateUtilsTest {

    @Test
    public void formatsChineseDate() {
        Calendar c = new GregorianCalendar(2026, Calendar.OCTOBER, 12, 14, 30);
        assertEquals("10月12日 14:30", DateUtils.format(c.getTimeInMillis(), Locale.CHINA));
    }

    @Test
    public void noLeadingZeroOnMonthAndDay() {
        Calendar c = new GregorianCalendar(2026, Calendar.SEPTEMBER, 5, 8, 5);
        assertEquals("9月5日 08:05", DateUtils.format(c.getTimeInMillis(), Locale.CHINA));
    }

    @Test
    public void midnightTime() {
        Calendar c = new GregorianCalendar(2026, Calendar.JANUARY, 1, 0, 0);
        assertEquals("1月1日 00:00", DateUtils.format(c.getTimeInMillis(), Locale.CHINA));
    }
}
