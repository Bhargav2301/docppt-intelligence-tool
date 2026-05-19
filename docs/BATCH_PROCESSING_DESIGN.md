# Batch Processing Design

## Overview
Allows multiple documents or PowerPoint files to be processed in a single user action.

## API Endpoints

### `POST /api/doc/batch-process`
- **Request**: Multipart form data with multiple `files[]` or list of `urls[]`.
- **Logic**:
  1. For each input, generate a `session_id`.
  2. Queue tasks or process sequentially.
  3. Return a list of created session IDs.
- **Response**:
  ```json
  {
    "batch_id": "uuid",
    "sessions": [
      {"id": "uuid1", "filename": "doc1.docx", "status": "queued"},
      {"id": "uuid2", "filename": "doc2.docx", "status": "queued"}
    ]
  }
  ```

### `POST /api/ppt/batch-process`
- **Request**: Multipart form data with multiple `files[]`.
- **Logic**: Similar to doc batch processing.

## UI Flow
1. **Selection**: User selects multiple files in the upload area.
2. **Progress**: UI shows a progress bar or status list for the whole batch.
3. **Completion**: Each item links to its own session review page.

## Session Management
- Each file in a batch is treated as a separate session in the database.
- This maintains compatibility with existing detail views.
- Failures in one file do not halt the entire batch.
