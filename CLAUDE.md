# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a WhatsApp Bridge application written in Go that provides a REST API for sending and receiving WhatsApp messages. It uses the whatsmeow library to connect to WhatsApp Web API and stores message history in SQLite databases.

## Development Commands

### Running the Application
```bash
cd whatsapp-bridge && go run main.go
```

### Building
```bash
cd whatsapp-bridge && go build
```

### Dependencies
Dependencies are managed via Go modules. To update dependencies:
```bash
cd whatsapp-bridge && go mod tidy
```

## Architecture

### Core Components

1. **Main Application** (`whatsapp-bridge/main.go`): 
   - Handles WhatsApp authentication via QR code
   - Manages WebSocket connection to WhatsApp
   - Provides REST API endpoints on port 8080
   - Stores messages in SQLite databases

2. **Database Structure**:
   - `store/whatsapp.db`: WhatsApp session data
   - `store/messages.db`: Chat history with two tables:
     - `chats`: Chat metadata
     - `messages`: Individual messages with indexes for searching

3. **REST API Endpoints**:
   - `POST /api/send`: Send text or media messages
   - `POST /api/download`: Download media files

### Key Implementation Details

- Uses Go channels and goroutines for concurrent operations
- Event-driven architecture for handling WhatsApp events
- Media files stored in `store/{chat_id}/` directories
- Supports images, videos, audio (with optional FFmpeg conversion), and documents
- Session persistence lasts approximately 20 days before re-authentication is needed

### Media Handling

- **Sending**: Supports text, images, videos, documents, and voice messages
- **Voice Messages**: Require .ogg Opus format (automatic conversion with FFmpeg)
- **Downloading**: Media metadata stored in DB, actual files downloaded on demand

## Important Notes

- First run requires QR code scanning with WhatsApp mobile app
- The `linkedin-worker/` directory exists but is not yet implemented
- All API requests should be sent to `http://localhost:8080`
- To reset the connection, delete both database files in the `store/` directory