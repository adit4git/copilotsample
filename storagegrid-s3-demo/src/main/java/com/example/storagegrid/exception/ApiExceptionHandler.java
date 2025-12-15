package com.example.storagegrid.exception;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import software.amazon.awssdk.services.s3.model.S3Exception;

import java.util.Map;

@RestControllerAdvice
public class ApiExceptionHandler {

    @ExceptionHandler(S3Exception.class)
    public ResponseEntity<Map<String, Object>> handleS3(S3Exception ex) {
        // Many S3-compatible systems sometimes return 404-ish errors when auth/policy/endpoint config is wrong.
        // Bubble up code + message so it’s easier to debug.
        int status = ex.statusCode();
        HttpStatus hs = HttpStatus.resolve(status);
        if (hs == null) hs = HttpStatus.BAD_GATEWAY;

        return ResponseEntity.status(hs).body(Map.of(
                "error", "S3Exception",
                "statusCode", status,
                "awsErrorCode", ex.awsErrorDetails() != null ? ex.awsErrorDetails().errorCode() : null,
                "message", ex.getMessage()
        ));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Map<String, Object>> handleValidation(MethodArgumentNotValidException ex) {
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of(
                "error", "ValidationError",
                "message", "Invalid request parameters"
        ));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<Map<String, Object>> handleGeneric(Exception ex) {
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of(
                "error", ex.getClass().getSimpleName(),
                "message", ex.getMessage()
        ));
    }
}
