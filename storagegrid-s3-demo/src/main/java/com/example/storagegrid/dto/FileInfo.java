package com.example.storagegrid.dto;

import java.time.Instant;

public record FileInfo(
        String key,
        long size,
        Instant lastModified
) {
}
