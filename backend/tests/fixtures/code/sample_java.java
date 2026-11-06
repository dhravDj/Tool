package com.documind.intelligence;

import java.util.List;
import java.util.ArrayList;
import java.io.Serializable;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DocumentService implements Serializable {
    private static final Logger log = LoggerFactory.getLogger(DocumentService.class);
    private final String serviceId;

    public DocumentService(String serviceId) {
        this.serviceId = serviceId;
    }

    public List<String> processDocuments(List<String> docIds) {
        log.info("Processing {} documents", docIds.size());
        List<String> results = new ArrayList<>();
        for (String id : docIds) {
            results.add("PROCESSED_" + id);
        }
        return results;
    }
}
