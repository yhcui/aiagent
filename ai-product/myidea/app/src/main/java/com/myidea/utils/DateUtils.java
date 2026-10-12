package com.myidea.utils;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

public final class DateUtils {

    private DateUtils() {
    }

    public static String format(long timestamp) {
        return format(timestamp, Locale.getDefault());
    }

    public static String format(long timestamp, Locale locale) {
        SimpleDateFormat format = new SimpleDateFormat("M月d日 HH:mm", locale);
        return format.format(new Date(timestamp));
    }
}
