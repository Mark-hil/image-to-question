"""
Test script for the questions API endpoints.
Run this script to test the new GET, DELETE, and UPDATE endpoints.
"""

import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_get_questions():
    """Test the GET /questions endpoint with various filters"""
    print("Testing GET /questions endpoint...")
    
    # Test 1: Get all questions
    response = requests.get(f"{BASE_URL}/questions")
    print(f"1. Get all questions: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Total questions: {data['total']}")
        print(f"   Questions returned: {len(data['questions'])}")
    
    # Test 2: Filter by teacher_id
    response = requests.get(f"{BASE_URL}/questions?teacher_id=4")
    print(f"2. Filter by teacher_id=4: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Questions for teacher 4: {data['total']}")
    
    # Test 3: Filter by subject
    response = requests.get(f"{BASE_URL}/questions?subject=english")
    print(f"3. Filter by subject=english: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   English questions: {data['total']}")
    
    # Test 4: Filter by question type
    response = requests.get(f"{BASE_URL}/questions?qtype=mcq")
    print(f"4. Filter by qtype=mcq: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   MCQ questions: {data['total']}")
    
    # Test 5: Search functionality
    response = requests.get(f"{BASE_URL}/questions?search=hands")
    print(f"5. Search for 'hands': {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Questions containing 'hands': {data['total']}")
    
    # Test 6: Pagination
    response = requests.get(f"{BASE_URL}/questions?page=1&size=5")
    print(f"6. Pagination (page=1, size=5): {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Page {data['page']} of {data['pages']}, showing {len(data['questions'])} questions")

def test_get_single_question():
    """Test getting a single question by ID"""
    print("\nTesting GET /questions/{id} endpoint...")
    
    # First get a question ID from the list
    response = requests.get(f"{BASE_URL}/questions?size=1")
    if response.status_code == 200:
        data = response.json()
        if data['questions']:
            question_id = data['questions'][0]['id']
            print(f"Found question ID: {question_id}")
            
            # Get the specific question
            response = requests.get(f"{BASE_URL}/questions/{question_id}")
            print(f"Get question {question_id}: {response.status_code}")
            if response.status_code == 200:
                question = response.json()
                print(f"   Question: {question['question_text'][:50]}...")
        else:
            print("No questions found to test with")
    else:
        print("Failed to get questions list")

def test_update_question():
    """Test updating a question"""
    print("\nTesting PUT /questions/{id} endpoint...")
    
    # First get a question ID
    response = requests.get(f"{BASE_URL}/questions?size=1")
    if response.status_code == 200:
        data = response.json()
        if data['questions']:
            question_id = data['questions'][0]['id']
            original_difficulty = data['questions'][0]['difficulty']
            
            # Update the question difficulty
            update_data = {
                "difficulty": "hard" if original_difficulty != "hard" else "easy",
                "rationale": "Updated rationale for testing purposes"
            }
            
            response = requests.put(
                f"{BASE_URL}/questions/{question_id}",
                json=update_data
            )
            print(f"Update question {question_id}: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"   Updated successfully: {result['message']}")
                print(f"   New difficulty: {result['question']['difficulty']}")
        else:
            print("No questions found to test with")
    else:
        print("Failed to get questions list")

def test_delete_questions():
    """Test deleting questions (BE CAREFUL - this actually deletes!)"""
    print("\nTesting DELETE /questions endpoint...")
    print("WARNING: This will actually delete questions!")
    
    # Test deletion by filters (commented out for safety)
    # Uncomment to test actual deletion
    """
    # Delete questions with a specific filter
    response = requests.delete(
        f"{BASE_URL}/questions",
        params={"teacher_id": "test_teacher_id"}  # Use a non-existent teacher for safety
    )
    print(f"Delete by filter: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   {result['message']}")
    """
    
    # Test deletion by specific ID (commented out for safety)
    """
    # First get a question ID
    response = requests.get(f"{BASE_URL}/questions?size=1")
    if response.status_code == 200:
        data = response.json()
        if data['questions']:
            question_id = data['questions'][0]['id']
            print(f"Would delete question ID: {question_id}")
            
            # Uncomment to actually delete
            # response = requests.delete(f"{BASE_URL}/questions/{question_id}")
            # print(f"Delete question {question_id}: {response.status_code}")
    """
    
    print("Delete tests skipped for safety. Uncomment the code to test actual deletion.")

if __name__ == "__main__":
    print("Testing Questions API Endpoints")
    print("=" * 50)
    
    try:
        test_get_questions()
        test_get_single_question()
        test_update_question()
        test_delete_questions()
        
        print("\n" + "=" * 50)
        print("Testing completed!")
        print("\nAPI Endpoints Available:")
        print("- GET    /api/questions              - List questions with filters")
        print("- GET    /api/questions/{id}          - Get single question")
        print("- PUT    /api/questions/{id}          - Update question")
        print("- DELETE /api/questions/{id}          - Delete single question")
        print("- DELETE /api/questions               - Delete questions by filters")
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server.")
        print("Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"Error: {e}")
