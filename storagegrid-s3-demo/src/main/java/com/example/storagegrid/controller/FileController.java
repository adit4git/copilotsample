package com.example.storagegrid.controller;

import com.example.storagegrid.dto.FileInfo;
import com.example.storagegrid.service.S3StorageService;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.List;

@RestController
@RequestMapping("/api/files")
public class FileController {

    private final S3StorageService storage;

    public FileController(S3StorageService storage) {
        this.storage = storage;
    }

    /**
     * Upload a file to the configured bucket.
     *
     * Example:
     *   curl -F "file=@./hello.txt" "http://localhost:8080/api/files/upload?prefix=demo/"
     */
    @PostMapping(value = "/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<FileInfo> upload(
            @RequestPart("file") MultipartFile file,
            @RequestParam(value = "key", required = false) String key,
            @RequestParam(value = "prefix", required = false) String prefix
    ) throws IOException {
        String finalKey = buildKey(prefix, (StringUtils.hasText(key) ? key : file.getOriginalFilename()));
        if (!StringUtils.hasText(finalKey)) {
            return ResponseEntity.badRequest().build();
        }

        byte[] bytes = file.getBytes();
        String contentType = (file.getContentType() != null ? file.getContentType() : "application/octet-stream");

        FileInfo info = storage.upload(finalKey, bytes, contentType);
        return ResponseEntity.ok(info);
    }

    /**
     * List objects in the configured bucket.
     *
     * Example:
     *   curl "http://localhost:8080/api/files?prefix=demo/&maxKeys=100"
     */
    @GetMapping
    public ResponseEntity<List<FileInfo>> list(
            @RequestParam(value = "prefix", required = false) String prefix,
            @RequestParam(value = "maxKeys", required = false) @Min(1) @Max(1000) Integer maxKeys
    ) {
        return ResponseEntity.ok(storage.list(prefix, maxKeys));
    }

    private static String buildKey(String prefix, String name) {
        String p = (prefix == null ? "" : prefix.trim());
        String n = (name == null ? "" : name.trim());

        if (p.isEmpty()) return n;
        if (n.isEmpty()) return p;

        // Ensure prefix ends with "/" (S3 has keys, not folders, but this is a common convention)
        if (!p.endsWith("/")) p = p + "/";
        // Avoid accidental leading "/"
        while (p.startsWith("/")) p = p.substring(1);

        // Avoid accidental leading "/"
        while (n.startsWith("/")) n = n.substring(1);

        return p + n;
    }
}
