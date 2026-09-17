import os
import io
import asyncio
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from fastapi import UploadFile

from main import app
from utils.file import save_upload_file, cleanup_file, cleanup_files

async def test_extract_and_discard_lifecycle():
    print("\n🎯 ===============================================================")
    print("   TESTING EXTRACT & DISCARD FILE LIFECYCLE")
    print("=================================================================\n")

    # -----------------------------------------------------------------
    # TEST 1: Unique UUID Prefixing in save_upload_file
    # -----------------------------------------------------------------
    print("👉 Test 1: Testing Unique UUID Collision Prevention...")
    content1 = b"Sample File 1 content"
    content2 = b"Sample File 2 content"
    
    file1 = UploadFile(filename="lecture_notes.pdf", file=io.BytesIO(content1))
    file2 = UploadFile(filename="lecture_notes.pdf", file=io.BytesIO(content2))

    path1 = await save_upload_file(file1, "uploads")
    path2 = await save_upload_file(file2, "uploads")

    assert os.path.exists(path1), f"Path {path1} was not created"
    assert os.path.exists(path2), f"Path {path2} was not created"
    assert path1 != path2, "Paths should be unique even with identical original filenames!"
    assert "lecture_notes.pdf" in path1
    assert "lecture_notes.pdf" in path2
    print(f"  ✅ Distinct unique paths generated without collision:")
    print(f"     File 1: {path1}")
    print(f"     File 2: {path2}")

    # -----------------------------------------------------------------
    # TEST 2: Cleanup Utility Functions
    # -----------------------------------------------------------------
    print("\n👉 Test 2: Testing Cleanup Utility Functions...")
    assert cleanup_file(path1) is True
    assert not os.path.exists(path1), "Path 1 should have been unlinked"
    assert cleanup_file(path1) is False  # Safe idempotent call

    cleanup_files([path2, "non_existent_file.pdf"])
    assert not os.path.exists(path2), "Path 2 should have been unlinked"
    print("  ✅ cleanup_file and cleanup_files cleanly and safely unlinked files")

    # -----------------------------------------------------------------
    # TEST 3: End-to-End Successful Generation Discards Uploaded File
    # -----------------------------------------------------------------
    print("\n👉 Test 3: Testing End-to-End Extraction & Automatic Discard...")
    saved_paths_seen = []
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Mock OCR and Question generation
        with patch("routers.upload_and_generate.process_image") as mock_img, \
             patch("routers.upload_and_generate.generate_questions_from_content") as mock_qgen:

            def capture_file(fpath):
                saved_paths_seen.append(fpath)
                assert os.path.exists(fpath), f"File {fpath} must exist while OCR is reading it!"
                return {"text": "Cell biology and ATP energy cycle.", "description": "", "file_path": fpath}

            mock_img.side_effect = capture_file
            mock_qgen.return_value = '[{"question": "What produces ATP?", "answer": "Mitochondria", "choices": ["Mitochondria", "Ribosome", "Nucleus", "Vacuole"], "rationale": "Mitochondria are powerhouse of cell.", "qtype": "mcq", "blooms_level": "Understand"}]'

            dummy_img = io.BytesIO(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82")
            files = [("files", ("bio_diagram.png", dummy_img, "image/png"))]

            resp = await client.post(
                "/api/generate/upload-and-generate?qtype=mcq&difficulty=medium&num_questions=1",
                files=files
            )
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
            data = resp.json()
            assert len(data["questions"]) == 1
            # Verify source_file displays original clean filename, not temporary UUID path
            assert data["questions"][0]["source_file"] == "bio_diagram.png"
            
            # Verify that the physical file was discarded
            assert len(saved_paths_seen) == 1
            temp_path = saved_paths_seen[0]
            assert not os.path.exists(temp_path), f"Temporary file {temp_path} MUST be deleted after request completes!"
            print(f"  ✅ Uploaded file existed during OCR extraction and was deleted immediately afterwards: {temp_path}")

    # -----------------------------------------------------------------
    # TEST 4: Guaranteed Discard Even on Error / Exception
    # -----------------------------------------------------------------
    print("\n👉 Test 4: Testing Guaranteed Discard Even When Generation Fails...")
    error_paths_seen = []
    
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with patch("routers.upload_and_generate.process_image") as mock_img_fail:
            def fail_file(fpath):
                error_paths_seen.append(fpath)
                assert os.path.exists(fpath), f"File {fpath} must exist before failure"
                raise RuntimeError("Simulated OCR failure or corrupted image!")

            mock_img_fail.side_effect = fail_file

            dummy_img2 = io.BytesIO(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82")
            files = [("files", ("corrupted_diagram.png", dummy_img2, "image/png"))]

            resp = await client.post(
                "/api/generate/upload-and-generate?qtype=mcq&difficulty=medium&num_questions=1",
                files=files
            )
            assert resp.status_code != 200, "Request should fail"
            
            # Verify that the physical file was discarded despite error
            assert len(error_paths_seen) == 1
            error_temp_path = error_paths_seen[0]
            assert not os.path.exists(error_temp_path), f"Temporary file {error_temp_path} MUST be deleted even when OCR fails!"
            print(f"  ✅ Temporary file was cleanly discarded despite simulated failure: {error_temp_path}")

    print("\n🎉 ALL EXTRACT & DISCARD TESTS PASSED PERFECTLY!\n")

if __name__ == "__main__":
    asyncio.run(test_extract_and_discard_lifecycle())
